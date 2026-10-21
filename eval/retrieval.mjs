#!/usr/bin/env node
/**
 * retrieval.mjs — how well does the study assistant find the right past question?
 *
 *   node eval/retrieval.mjs                    print the metrics, write eval/results.json
 *   node eval/retrieval.mjs --write-baseline   ...and save them as eval/baseline.json
 *   node eval/retrieval.mjs --check            fail (exit 1) if assistant recall@5 is more than
 *                                              2 points below eval/baseline.json (used by CI)
 *
 * For each query in eval/retrieval_queries.json we rank all questions and look for
 * any of the query's gold ids (the target question plus known near-duplicates).
 *
 *   recall@5  share of queries with at least one gold id in the top 5
 *   MRR       mean of 1/rank of the first gold id (0 if it never appears)
 *
 * Three systems are measured on the same queries:
 *   assistant        the shipped int8 index (assets/assistant/index.bin) ranked with
 *                    topK() from assets/js/assistant-rank.mjs: exactly what the browser runs
 *   assistant_float  the same documents embedded fresh, without int8 quantization
 *                    (shows what quantization costs)
 *   keyword          the site's existing Search Questions box (filterQuestions() in
 *                    assets/js/app.js), reimplemented below line for line
 *   keyword_words    NOT on the site, for context only: the same metadata text, ranked by
 *                    how many of the query's words it contains (ties in file order)
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { pipeline } from '@huggingface/transformers';
import { topK, decodeIndex } from '../assets/js/assistant-rank.mjs';
import { MODEL, DTYPE, chapterNames } from '../scripts/assistant-text.mjs';
import { embedAll, loadCorpus } from '../scripts/build-index.mjs';

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = f => JSON.parse(fs.readFileSync(path.join(root, f), 'utf8'));
const K = 5;
const MAX_DROP = 0.02;   // CI tolerance: 2 percentage points of recall@5

/** recall@K and MRR from each query's full ranking (array of ids, best first). */
export function score(queries, rankings) {
  let hits = 0, rr = 0;
  const perQuery = queries.map((q, i) => {
    const gold = new Set(q.gold);
    const idx = rankings[i].findIndex(id => gold.has(id));
    const rank = idx < 0 ? null : idx + 1;
    if (rank && rank <= K) hits++;
    if (rank) rr += 1 / rank;
    return { id: q.id, rank };
  });
  return { recall_at_5: hits / queries.length, mrr: rr / queries.length, perQuery };
}

/**
 * The existing keyword search, copied from assets/js/app.js:
 * buildIndexes() builds q._hay, filterQuestions() keeps questions whose _hay contains the
 * whole lowercased query as one substring, in questions.json order (there is no ranking).
 * With no course selected it hides cross-listed copies, which questions.json doesn't contain.
 */
function hayOf(q, names) {
  const s = q.source;
  return [
    (q.chapter || '').replace(/_/g, ' '),
    names.get(`${q.course}|${q.chapter}`) || q.chapter,
    q.course,
    (q.skills || []).join(' '),
    s ? `${s.exam} ${s.term} ${s.exam_id}` : '',
    s && s.staff ? s.staff.join(' ') : '',
  ].join(' ').toLowerCase();
}

function keywordRanking(questions, names, query) {
  const kw = query.trim().toLowerCase();
  return questions.filter(q => !kw || hayOf(q, names).includes(kw)).map(q => q.id);
}

/** Context only (not on the site): rank by number of query words (3+ letters) found in the haystack. */
function keywordWordsRanking(questions, names, query) {
  const words = [...new Set(query.toLowerCase().match(/[a-z0-9]{3,}/g) || [])];
  return questions
    .map((q, i) => { const hay = hayOf(q, names); return { id: q.id, i, n: words.filter(w => hay.includes(w)).length }; })
    .filter(h => h.n > 0)
    .sort((a, b) => b.n - a.n || a.i - b.i)
    .map(h => h.id);
}

function byCourse(queries, perQuery) {
  const out = {};
  queries.forEach((q, i) => {
    const c = (out[q.course] ||= { n: 0, hits: 0 });
    c.n++;
    if (perQuery[i].rank && perQuery[i].rank <= K) c.hits++;
  });
  return Object.fromEntries(Object.entries(out).sort().map(([c, v]) => [c, +(v.hits / v.n).toFixed(3)]));
}

async function main() {
  const args = new Set(process.argv.slice(2));
  const queries = read('eval/retrieval_queries.json');
  const questions = read('questions.json');
  const names = chapterNames(read('chapters.json'));
  const manifest = read('assets/assistant/index.json');
  const rows = decodeIndex(fs.readFileSync(path.join(root, 'assets/assistant/index.bin')).buffer
    .slice(0));   // copy into a standalone ArrayBuffer

  const extractor = await pipeline('feature-extraction', MODEL, { dtype: DTYPE });
  const qvecs = await embedAll(extractor, queries.map(q => q.query));
  const all = manifest.ids.length;

  // 1. the shipped int8 index, ranked by the browser's code
  const assistant = score(queries, qvecs.map(v => topK(v, rows, manifest.dims, manifest.ids, null, all).map(h => h.id)));

  // 2. same documents, float vectors (no quantization)
  const { docs } = loadCorpus();
  const dvecs = await embedAll(extractor, docs.map(d => d.text));
  const assistantFloat = score(queries, qvecs.map(v => dvecs
    .map((d, i) => ({ id: docs[i].id, s: d.reduce((a, x, j) => a + x * v[j], 0) }))
    .sort((a, b) => b.s - a.s).map(h => h.id)));

  // 3. the existing keyword search
  const keyword = score(queries, queries.map(q => keywordRanking(questions, names, q.query)));
  const keywordWords = score(queries, queries.map(q => keywordWordsRanking(questions, names, q.query)));
  const keywordAnyResult = queries.filter(q => keywordRanking(questions, names, q.query).length > 0).length;

  const r3 = x => +x.toFixed(3);
  const results = {
    queries: queries.length,
    questions_indexed: manifest.count,
    questions_transcribed: manifest.transcribed,
    model: `${MODEL} (${DTYPE})`,
    assistant: { recall_at_5: r3(assistant.recall_at_5), mrr: r3(assistant.mrr), recall_at_5_by_course: byCourse(queries, assistant.perQuery) },
    assistant_float: { recall_at_5: r3(assistantFloat.recall_at_5), mrr: r3(assistantFloat.mrr) },
    keyword: { recall_at_5: r3(keyword.recall_at_5), mrr: r3(keyword.mrr), queries_with_any_result: keywordAnyResult },
    keyword_words_context_only: { recall_at_5: r3(keywordWords.recall_at_5), mrr: r3(keywordWords.mrr) },
    per_query: queries.map((q, i) => ({ id: q.id, target: q.target, assistant_rank: assistant.perQuery[i].rank, keyword_rank: keyword.perQuery[i].rank })),
  };
  fs.writeFileSync(path.join(root, 'eval/results.json'), JSON.stringify(results, null, 1) + '\n');

  console.log(`${queries.length} queries, ${manifest.count} questions indexed (${manifest.transcribed} transcribed)`);
  console.log(`assistant (int8)   recall@5 ${results.assistant.recall_at_5}  MRR ${results.assistant.mrr}`);
  console.log(`assistant (float)  recall@5 ${results.assistant_float.recall_at_5}  MRR ${results.assistant_float.mrr}`);
  console.log(`keyword baseline   recall@5 ${results.keyword.recall_at_5}  MRR ${results.keyword.mrr}  (${keywordAnyResult}/${queries.length} queries return anything)`);
  console.log(`keyword words (not on site) recall@5 ${results.keyword_words_context_only.recall_at_5}  MRR ${results.keyword_words_context_only.mrr}`);
  console.log('assistant recall@5 by course', results.assistant.recall_at_5_by_course);

  if (args.has('--write-baseline')) {
    const { per_query, ...summary } = results;
    fs.writeFileSync(path.join(root, 'eval/baseline.json'), JSON.stringify({ ...summary, written: new Date().toISOString() }, null, 1) + '\n');
    console.log('wrote eval/baseline.json');
  }
  if (args.has('--check')) {
    const base = read('eval/baseline.json');
    const floor = base.assistant.recall_at_5 - MAX_DROP;
    const ok = results.assistant.recall_at_5 >= floor - 1e-9;
    console.log(`check: recall@5 ${results.assistant.recall_at_5} vs baseline ${base.assistant.recall_at_5} (floor ${floor.toFixed(3)}): ${ok ? 'PASS' : 'FAIL'}`);
    if (!ok) process.exit(1);
  }
}

if (process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1])) await main();

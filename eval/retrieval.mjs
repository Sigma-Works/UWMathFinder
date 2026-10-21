#!/usr/bin/env node
/**
 * retrieval.mjs — how well does the study assistant find the right past question?
 *
 *   node eval/retrieval.mjs                    print the metrics, write eval/results.json
 *   node eval/retrieval.mjs --write-baseline   ...and save them as eval/baseline.json
 *   node eval/retrieval.mjs --check            fail (exit 1) if retrieval got worse (used by CI, see GATE below)
 *
 * Two query sets:
 *   eval/retrieval_queries.json  written while looking at each target question ("llm", plus any
 *                                rewritten by hand, "human"). gold ids count as grade 2.
 *   eval/human_queries.json      from UWMathFinder Lab (scripts/import-lab.mjs), optional:
 *                                  human_blind        typed BEFORE seeing any question, then results
 *                                                     rated wanted (2) / related (1) / not relevant (0);
 *                                                     split into a frozen TEST (70%) and DEV (30%)
 *                                  human_image_shown  typed while looking at a question (grade 2 for it)
 *                                Only the DEV split may be used for tuning. TEST is for reporting and CI.
 *
 * Metrics (top K = 5). "Relevant" means grade 2 for recall and MRR; nDCG uses every grade.
 *   recall@5  share of queries with a relevant result in the top 5
 *   MRR       mean of 1/rank of the first relevant result (0 if it never appears)
 *   nDCG@5    graded: DCG = sum over the top 5 of (2^grade - 1) / log2(rank + 1), divided by
 *             the DCG of the best possible order of the judged results. Unjudged results count
 *             as grade 0, so it rewards systems that surface what people actually rated well.
 *   Queries with no grade-2 result are left out of recall/MRR, and with no grade >= 1 out of
 *   nDCG; the counts are reported so nothing disappears silently.
 *
 * Systems, all measured on the same queries:
 *   assistant        the shipped int8 index (assets/assistant/index.bin) ranked with
 *                    topK() from assets/js/assistant-rank.mjs: exactly what the browser runs
 *   assistant_float  the same documents embedded fresh, without int8 quantization
 *   keyword          the site's existing Search Questions box (filterQuestions() in
 *                    assets/js/app.js), reimplemented below line for line
 *   keyword_words    NOT on the site, for context only: the same metadata text, ranked by
 *                    how many of the query's words it contains (ties in file order)
 * Human queries made with a course picked (course_filter) are ranked within that course, as
 * they were in the lab; all other queries are ranked over every question.
 *
 * GATE (--check): until eval/human_queries.json has HUMAN_GATE_MIN human_blind TEST queries, CI
 * fails if assistant recall@5 on retrieval_queries.json drops more than 2 points below
 * eval/baseline.json. From then on (once the baseline has a human_blind_test entry) it fails if
 * assistant nDCG@5 on the human_blind TEST split drops more than 2 points.
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { pipeline } from '@huggingface/transformers';
import { topK, decodeIndex, courseFilter } from '../assets/js/assistant-rank.mjs';
import { MODEL, DTYPE, chapterNames } from '../scripts/assistant-text.mjs';
import { embedAll, loadCorpus } from '../scripts/build-index.mjs';

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = f => JSON.parse(fs.readFileSync(path.join(root, f), 'utf8'));
const K = 5;
const MAX_DROP = 0.02;        // CI tolerance: 2 percentage points
const HUMAN_GATE_MIN = 100;   // human_blind TEST queries needed before CI gates on them

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

/** nDCG@k for one ranking. judgments: {question_id: grade 0..2}; null if nothing is relevant. */
export function ndcgAt(ranking, judgments, k = K) {
  const gain = g => 2 ** g - 1;
  const ideal = Object.values(judgments).filter(g => g > 0).sort((a, b) => b - a).slice(0, k);
  if (!ideal.length) return null;
  const idcg = ideal.reduce((s, g, i) => s + gain(g) / Math.log2(i + 2), 0);
  const dcg = ranking.slice(0, k).reduce((s, id, i) => s + gain(judgments[id] || 0) / Math.log2(i + 2), 0);
  return dcg / idcg;
}

/** Graded metrics for a set of queries ({judgments}) and their rankings. */
export function scoreGraded(queries, rankings) {
  let nR = 0, hits = 0, rr = 0, nN = 0, nd = 0;
  queries.forEach((q, i) => {
    const r = rankings[i];
    if (Object.values(q.judgments).some(g => g === 2)) {
      nR++;
      const idx = r.findIndex(id => q.judgments[id] === 2);
      if (idx >= 0 && idx < K) hits++;
      if (idx >= 0) rr += 1 / (idx + 1);
    }
    const v = ndcgAt(r, q.judgments);
    if (v !== null) { nN++; nd += v; }
  });
  const r3 = x => +x.toFixed(3);
  return {
    queries: queries.length,
    recall_at_5: nR ? r3(hits / nR) : null, mrr: nR ? r3(rr / nR) : null, queries_with_wanted: nR,
    ndcg_at_5: nN ? r3(nd / nN) : null, queries_with_any_relevant: nN,
  };
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

/** recall@5 split by who wrote the query ("llm" or "human"). */
function bySource(queries, perQuery) {
  const out = {};
  queries.forEach((q, i) => {
    const c = (out[q.source] ||= { n: 0, hits: 0 });
    c.n++;
    if (perQuery[i].rank && perQuery[i].rank <= K) c.hits++;
  });
  return Object.fromEntries(Object.entries(out).sort().map(([src, v]) => [src, { queries: v.n, recall_at_5: +(v.hits / v.n).toFixed(3) }]));
}

/** Which report group a query belongs to: its source, with human_blind split into test / dev. */
const groupOf = q => (q.source === 'human_blind' ? `human_blind_${q.split}` : q.source);

async function main() {
  const args = new Set(process.argv.slice(2));
  const queries = read('eval/retrieval_queries.json');
  const humanFile = path.join(root, 'eval/human_queries.json');
  const human = fs.existsSync(humanFile) ? JSON.parse(fs.readFileSync(humanFile, 'utf8')).queries : [];
  const questions = read('questions.json');
  const questionsById = new Map(questions.map(q => [q.id, q]));
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
  const floatRank = v => dvecs
    .map((d, i) => ({ id: docs[i].id, s: d.reduce((a, x, j) => a + x * v[j], 0) }))
    .sort((a, b) => b.s - a.s).map(h => h.id);
  const assistantFloat = score(queries, qvecs.map(floatRank));

  // 3. the existing keyword search
  const keyword = score(queries, queries.map(q => keywordRanking(questions, names, q.query)));
  const keywordWords = score(queries, queries.map(q => keywordWordsRanking(questions, names, q.query)));
  const keywordAnyResult = queries.filter(q => keywordRanking(questions, names, q.query).length > 0).length;

  // 4. graded metrics per source, over both query sets
  const graded = [
    ...queries.map(q => ({ ...q, judgments: Object.fromEntries(q.gold.map(g => [g, 2])), course_filter: null })),
    ...human,
  ];
  const gvecs = [...qvecs, ...(human.length ? await embedAll(extractor, human.map(q => q.query)) : [])];
  const within = (q, ids) => { const keep = courseFilter(questionsById, q.course_filter); return keep ? ids.filter(keep) : ids; };
  const systems = {
    assistant: (q, v) => topK(v, rows, manifest.dims, manifest.ids, courseFilter(questionsById, q.course_filter), all).map(h => h.id),
    assistant_float: (q, v) => within(q, floatRank(v)),
    keyword: q => within(q, keywordRanking(questions, names, q.query)),
    keyword_words: q => within(q, keywordWordsRanking(questions, names, q.query)),
  };
  const bySourceGraded = {};
  for (const g of [...new Set(graded.map(groupOf))].sort()) {
    const idx = graded.map((_, i) => i).filter(i => groupOf(graded[i]) === g);
    bySourceGraded[g] = Object.fromEntries(Object.entries(systems).map(([name, rankFn]) =>
      [name, scoreGraded(idx.map(i => graded[i]), idx.map(i => rankFn(graded[i], gvecs[i])))]));
  }
  const humanTestCount = human.filter(q => q.source === 'human_blind' && q.split === 'test').length;

  const r3 = x => +x.toFixed(3);
  const results = {
    queries: queries.length,
    human_queries: human.length,
    questions_indexed: manifest.count,
    questions_transcribed: manifest.transcribed,
    model: `${MODEL} (${DTYPE})`,
    assistant: { recall_at_5: r3(assistant.recall_at_5), mrr: r3(assistant.mrr), recall_at_5_by_course: byCourse(queries, assistant.perQuery), recall_at_5_by_source: bySource(queries, assistant.perQuery) },
    assistant_float: { recall_at_5: r3(assistantFloat.recall_at_5), mrr: r3(assistantFloat.mrr) },
    keyword: { recall_at_5: r3(keyword.recall_at_5), mrr: r3(keyword.mrr), queries_with_any_result: keywordAnyResult },
    keyword_words_context_only: { recall_at_5: r3(keywordWords.recall_at_5), mrr: r3(keywordWords.mrr) },
    graded_by_source: bySourceGraded,
    per_query: queries.map((q, i) => ({ id: q.id, target: q.target, assistant_rank: assistant.perQuery[i].rank, keyword_rank: keyword.perQuery[i].rank })),
  };
  fs.writeFileSync(path.join(root, 'eval/results.json'), JSON.stringify(results, null, 1) + '\n');

  console.log(`${queries.length} queries, ${manifest.count} questions indexed (${manifest.transcribed} transcribed)`);
  console.log(`assistant (int8)   recall@5 ${results.assistant.recall_at_5}  MRR ${results.assistant.mrr}`);
  console.log(`assistant (float)  recall@5 ${results.assistant_float.recall_at_5}  MRR ${results.assistant_float.mrr}`);
  console.log(`keyword baseline   recall@5 ${results.keyword.recall_at_5}  MRR ${results.keyword.mrr}  (${keywordAnyResult}/${queries.length} queries return anything)`);
  console.log(`keyword words (not on site) recall@5 ${results.keyword_words_context_only.recall_at_5}  MRR ${results.keyword_words_context_only.mrr}`);
  console.log('assistant recall@5 by course', results.assistant.recall_at_5_by_course);
  console.log('assistant recall@5 by query source', results.assistant.recall_at_5_by_source);
  console.log(`\ngraded metrics by source (${human.length} lab queries in eval/human_queries.json; only human_blind_dev may be used for tuning)`);
  const fmt = x => (x === null ? '  -  ' : x.toFixed(3));
  for (const [g, sys] of Object.entries(bySourceGraded)) {
    const a = sys.assistant;
    console.log(`  ${g.padEnd(20)} ${String(a.queries).padStart(4)} queries (${a.queries_with_wanted} with a "wanted", ${a.queries_with_any_relevant} with any relevant)`);
    for (const [name, m] of Object.entries(sys)) {
      console.log(`    ${name.padEnd(16)} recall@5 ${fmt(m.recall_at_5)}  MRR ${fmt(m.mrr)}  nDCG@5 ${fmt(m.ndcg_at_5)}`);
    }
  }

  const humanTest = bySourceGraded.human_blind_test?.assistant;
  if (args.has('--write-baseline')) {
    const { per_query, graded_by_source, ...summary } = results;
    const baseline = { ...summary, written: new Date().toISOString() };
    if (humanTest) baseline.human_blind_test = { queries: humanTest.queries, ndcg_at_5: humanTest.ndcg_at_5, recall_at_5: humanTest.recall_at_5, mrr: humanTest.mrr };
    fs.writeFileSync(path.join(root, 'eval/baseline.json'), JSON.stringify(baseline, null, 1) + '\n');
    console.log('wrote eval/baseline.json');
  }
  if (args.has('--check')) {
    const base = read('eval/baseline.json');
    let ok;
    if (humanTestCount >= HUMAN_GATE_MIN && base.human_blind_test?.ndcg_at_5 != null) {
      const floor = base.human_blind_test.ndcg_at_5 - MAX_DROP;
      ok = humanTest.ndcg_at_5 >= floor - 1e-9;
      console.log(`check (human_blind TEST, ${humanTestCount} queries): nDCG@5 ${humanTest.ndcg_at_5} vs baseline ${base.human_blind_test.ndcg_at_5} (floor ${floor.toFixed(3)}): ${ok ? 'PASS' : 'FAIL'}`);
    } else {
      if (humanTestCount >= HUMAN_GATE_MIN) {
        console.log(`::warning::${humanTestCount} human_blind TEST queries but eval/baseline.json has no human_blind_test entry: run \`node eval/retrieval.mjs --write-baseline\` and commit it to switch the gate`);
      } else {
        console.log(`gate: ${humanTestCount}/${HUMAN_GATE_MIN} human_blind TEST queries so far, so CI still gates on retrieval_queries.json recall@5`);
      }
      const floor = base.assistant.recall_at_5 - MAX_DROP;
      ok = results.assistant.recall_at_5 >= floor - 1e-9;
      console.log(`check: recall@5 ${results.assistant.recall_at_5} vs baseline ${base.assistant.recall_at_5} (floor ${floor.toFixed(3)}): ${ok ? 'PASS' : 'FAIL'}`);
    }
    if (!ok) process.exit(1);
  }
}

if (process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1])) await main();

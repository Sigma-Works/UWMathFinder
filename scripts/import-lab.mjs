#!/usr/bin/env node
/**
 * import-lab.mjs — bring UWMathFinder Lab's export into the eval.
 *
 *   node scripts/import-lab.mjs [path/to/eval-export.json]
 *        default: ../uwmathfinder-lab/out/eval-export.json (made by the lab's scripts/export.mjs)
 *
 * Checks every query (known question ids, valid source / split / grades), then writes
 * eval/human_queries.json, which eval/retrieval.mjs reads. The file is replaced on every
 * import: the lab's export is the source of truth, and its TEST/DEV split is frozen there
 * (uwmathfinder-lab/splits/splits.json), so re-importing never moves a query between splits.
 * This script refuses an import that would move one, as a second safety net.
 *
 * Remember: only human_blind DEV queries may be used for tuning. TEST is for reporting and CI.
 */
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const input = path.resolve(process.argv[2] || path.join(root, '..', 'uwmathfinder-lab', 'out', 'eval-export.json'));
const outFile = path.join(root, 'eval', 'human_queries.json');
const die = m => { console.error('import-lab: ' + m); process.exit(1); };

if (!fs.existsSync(input)) die(`${input} not found. In the lab, run: node scripts/export.mjs`);
const exp = JSON.parse(fs.readFileSync(input, 'utf8'));
const qids = new Set(JSON.parse(fs.readFileSync(path.join(root, 'questions.json'), 'utf8')).map(q => q.id));

const SOURCES = new Set(['human_blind', 'human_image_shown']);
const errors = [];
const seen = new Set();
for (const q of exp.queries || []) {
  const where = `query ${q.id}`;
  if (seen.has(q.id)) errors.push(`${where}: duplicate id`);
  seen.add(q.id);
  if (!q.query || typeof q.query !== 'string') errors.push(`${where}: missing text`);
  if (!SOURCES.has(q.source)) errors.push(`${where}: source must be human_blind or human_image_shown, got ${q.source}`);
  if (q.source === 'human_blind' && !['test', 'dev'].includes(q.split)) errors.push(`${where}: human_blind needs split test or dev`);
  if (q.source !== 'human_blind' && q.split != null) errors.push(`${where}: only human_blind queries are split`);
  if ('session_id' in q) errors.push(`${where}: contains a session id; re-run the lab export`);
  for (const [id, g] of Object.entries(q.judgments || {})) {
    if (!qids.has(id)) errors.push(`${where}: judged question ${id} is not in questions.json`);
    if (![0, 1, 2].includes(g)) errors.push(`${where}: grade ${g} for ${id} is not 0, 1 or 2`);
  }
}
if (errors.length) die(`${errors.length} problem(s):\n  ` + errors.slice(0, 30).join('\n  '));

// a query must never change split between imports
if (fs.existsSync(outFile)) {
  const before = new Map(JSON.parse(fs.readFileSync(outFile, 'utf8')).queries.map(q => [q.id, q.split]));
  const moved = exp.queries.filter(q => before.has(q.id) && before.get(q.id) !== q.split);
  if (moved.length) die(`${moved.length} queries changed split (e.g. ${moved[0].id}: ${before.get(moved[0].id)} → ${moved[0].split}). The split is frozen; check the lab's splits/splits.json.`);
}

// which index version each judgment was made against, vs the index in this checkout
let indexCommit = null;
try { indexCommit = execFileSync('git', ['-C', root, 'log', '-1', '--format=%H', '--', 'assets/assistant/index.bin', 'assets/assistant/index.json'], { encoding: 'utf8' }).trim(); } catch {}
const commits = {};
for (const q of exp.queries) commits[q.index_commit] = (commits[q.index_commit] || 0) + 1;

const queries = exp.queries.map(q => ({
  id: q.id, query: q.query, course: q.course ?? null, course_filter: q.course_filter ?? null,
  source: q.source, split: q.split ?? null, judgments: q.judgments,
  ...(q.target ? { target: q.target } : {}), ...(q.source === 'human_blind' ? { none_relevant: !!q.none_relevant } : {}),
  index_commit: q.index_commit,
}));
fs.writeFileSync(outFile, JSON.stringify({
  imported_at: new Date().toISOString(),
  from: { exported_at: exp.exported_at, lab_commit: exp.lab_commit, split_seed: exp.split_seed },
  grades: exp.grades,
  pairs_preferred: exp.report?.pairs_preferred ?? {},
  queries,
}, null, 1) + '\n');

const count = key => queries.reduce((m, q) => { const k = key(q); m[k] = (m[k] || 0) + 1; return m; }, {});
console.log(`imported ${queries.length} queries from ${path.relative(process.cwd(), input)}`);
console.log('by source/split', count(q => (q.split ? `${q.source} ${q.split}` : q.source)));
console.log('judged against index commits', commits, indexCommit ? `(index files last changed in ${indexCommit.slice(0, 7)})` : '');
console.log('wrote eval/human_queries.json; next: node eval/retrieval.mjs');

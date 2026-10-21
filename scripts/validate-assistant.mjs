#!/usr/bin/env node
/**
 * validate-assistant.mjs — checks for the study assistant's data files (CI runs it on PRs).
 *
 *   node scripts/validate-assistant.mjs
 *
 * - questions_text.json: known ids, no duplicates, required fields, every formula renders in KaTeX
 * - assets/assistant/index.*: same questions in the same order as questions.json, the right
 *   byte size, and built from the current transcriptions (otherwise run `npm run build:index`)
 * - eval/retrieval_queries.json: every gold id exists, every query says where it came from
 */
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const { checkLatex } = require('./latex-check.js');
const root = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = f => JSON.parse(fs.readFileSync(path.join(root, f), 'utf8'));
const errors = [];
const fail = m => errors.push(m);

const questions = read('questions.json');
const qids = new Set(questions.map(q => q.id));

// ── transcriptions
const texts = read('questions_text.json');
const seen = new Set();
for (const t of texts) {
  if (!qids.has(t.id)) fail(`questions_text.json: unknown id ${t.id}`);
  if (seen.has(t.id)) fail(`questions_text.json: duplicate id ${t.id}`);
  seen.add(t.id);
  for (const k of ['question_latex', 'answer_latex', 'final_answer']) {
    if (typeof t[k] !== 'string') { fail(`${t.id}: ${k} missing`); continue; }
    checkLatex(t[k]).forEach(m => fail(`${t.id} ${k}: ${m}`));
  }
  if (typeof t.confident !== 'boolean') fail(`${t.id}: confident must be true/false`);
}

// ── index
const man = read('assets/assistant/index.json');
const binSize = fs.statSync(path.join(root, 'assets/assistant/index.bin')).size;
if (man.ids.length !== questions.length || man.ids.some((id, i) => id !== questions[i].id)) {
  fail('index.json ids differ from questions.json: run `npm run build:index`');
}
if (binSize !== man.count * man.dims) fail(`index.bin is ${binSize} bytes, expected ${man.count} x ${man.dims}`);
if (man.transcribed !== texts.length) {
  fail(`index was built with ${man.transcribed} transcriptions but questions_text.json has ${texts.length}: run \`npm run build:index\``);
}
const sols = fs.readdirSync(path.join(root, 'solutions')).filter(f => f.endsWith('.json')).map(f => f.slice(0, -5)).sort();
if (JSON.stringify(sols) !== JSON.stringify(man.solutions)) fail('index.json solutions list is stale: run `npm run build:index`');

// ── eval queries
const qs = read('eval/retrieval_queries.json');
for (const q of qs) {
  if (!q.query || !Array.isArray(q.gold) || !q.gold.length) fail(`${q.id}: needs query and gold`);
  (q.gold || []).forEach(g => { if (!qids.has(g)) fail(`${q.id}: gold id ${g} not in questions.json`); });
  if (!q.source) fail(`${q.id}: missing "source" (llm or human)`);
}

// ── human eval queries from UWMathFinder Lab (optional)
let humanCount = 0;
if (fs.existsSync(path.join(root, 'eval/human_queries.json'))) {
  const hq = read('eval/human_queries.json').queries;
  humanCount = hq.length;
  const ids = new Set();
  for (const q of hq) {
    if (ids.has(q.id)) fail(`human ${q.id}: duplicate id`);
    ids.add(q.id);
    if (!q.query) fail(`human ${q.id}: missing query`);
    if (!['human_blind', 'human_image_shown'].includes(q.source)) fail(`human ${q.id}: unknown source ${q.source}`);
    if (q.source === 'human_blind' && !['test', 'dev'].includes(q.split)) fail(`human ${q.id}: human_blind needs split test or dev`);
    for (const [id, g] of Object.entries(q.judgments || {})) {
      if (!qids.has(id)) fail(`human ${q.id}: judged id ${id} not in questions.json`);
      if (![0, 1, 2].includes(g)) fail(`human ${q.id}: grade ${g} must be 0, 1 or 2`);
    }
  }
}

if (errors.length) {
  console.error(errors.join('\n'));
  console.error(`\n${errors.length} problem(s)`);
  process.exit(1);
}
console.log(`ok: ${texts.length} transcriptions, index of ${man.count} x ${man.dims}, ${qs.length} eval queries, ${humanCount} human eval queries`);

#!/usr/bin/env node
/**
 * transcribe.js — bookkeeping for the hand transcription of question images.
 *
 * The transcription itself is done by a person (or Claude) reading each PNG; this
 * script only keeps the queue, merges finished batches and checks the LaTeX.
 *
 *   node scripts/transcribe.js status            how many are done, what's next
 *   node scripts/transcribe.js next [n]          print the next n ids (default 50) with image paths
 *   node scripts/transcribe.js merge <file.json> merge a batch (array of entries) into
 *                                                questions_text.json and update the progress file
 *   node scripts/transcribe.js check             KaTeX-parse every entry in questions_text.json
 *
 * Queue order (scripts/transcribe_progress.json "queue"): the questions Zahid added first
 * (git log --author="Zahid-M" --diff-filter=A -- 'questions/*.png'), then everything else
 * in id order. To resume in a later session: run `status`, then `next`, transcribe, `merge`.
 *
 * Entry format: { id, question_latex, answer_latex, final_answer, confident }
 * Text is plain prose with math in $...$ / $$...$$ / \(...\) / \[...\] (KaTeX auto-render delimiters).
 */
const fs = require('node:fs');
const path = require('node:path');
const { execSync } = require('node:child_process');
const { checkLatex } = require('./latex-check.js');

const root = path.join(__dirname, '..');
const TEXT_FILE = path.join(root, 'questions_text.json');
const PROGRESS_FILE = path.join(__dirname, 'transcribe_progress.json');
const BATCH_SIZE = 50;

const questions = JSON.parse(fs.readFileSync(path.join(root, 'questions.json'), 'utf8'));
const byId = new Map(questions.map(q => [q.id, q]));

function loadText() {
  return fs.existsSync(TEXT_FILE) ? JSON.parse(fs.readFileSync(TEXT_FILE, 'utf8')) : [];
}

function buildQueue() {
  const log = execSync(
    `git log --author="Zahid-M" --diff-filter=A --name-only --format= -- "questions/*.png"`,
    { cwd: root, encoding: 'utf8' });
  const zahid = new Set(log.split(/\r?\n/).map(s => s.trim())
    .filter(s => /^questions\/q\d+\.png$/.test(s))
    .map(s => s.slice('questions/'.length, -'.png'.length)));
  const ids = questions.map(q => q.id).sort();
  return [...ids.filter(id => zahid.has(id)), ...ids.filter(id => !zahid.has(id))];
}

function loadProgress() {
  if (fs.existsSync(PROGRESS_FILE)) return JSON.parse(fs.readFileSync(PROGRESS_FILE, 'utf8'));
  const queue = buildQueue();
  return { batch_size: BATCH_SIZE, batches_done: 0, done: 0, total: queue.length, queue, batches: [] };
}

function saveProgress(p, text) {
  const doneIds = new Set(text.map(t => t.id));
  p.done = doneIds.size;
  p.next_id = p.queue.find(id => !doneIds.has(id)) || null;
  p.updated = new Date().toISOString();
  fs.writeFileSync(PROGRESS_FILE, JSON.stringify(p, null, 2) + '\n');
}

function validateEntry(e) {
  const errs = [];
  if (!byId.has(e.id)) errs.push(`${e.id}: not in questions.json`);
  for (const k of ['question_latex', 'answer_latex', 'final_answer']) {
    if (typeof e[k] !== 'string') errs.push(`${e.id}: ${k} must be a string`);
  }
  if (typeof e.confident !== 'boolean') errs.push(`${e.id}: confident must be true/false`);
  for (const k of ['question_latex', 'answer_latex', 'final_answer']) {
    if (typeof e[k] === 'string') checkLatex(e[k]).forEach(m => errs.push(`${e.id} ${k}: ${m}`));
  }
  return errs;
}

const [cmd, arg] = process.argv.slice(2);
const progress = loadProgress();
const text = loadText();
const doneIds = new Set(text.map(t => t.id));

if (cmd === 'status' || !cmd) {
  saveProgress(progress, text);
  const byCourse = {};
  text.forEach(t => { const c = byId.get(t.id).course; byCourse[c] = (byCourse[c] || 0) + 1; });
  console.log(`${doneIds.size} / ${progress.total} transcribed (${text.filter(t => !t.confident).length} marked not confident)`);
  console.log('by course:', byCourse);
  console.log('next id:', progress.next_id);
} else if (cmd === 'next') {
  const n = Number(arg) || BATCH_SIZE;
  progress.queue.filter(id => !doneIds.has(id)).slice(0, n).forEach(id => {
    const q = byId.get(id);
    console.log(`${id}\t${q.course}\t${q.image}\t${q.answer_image || '-'}`);
  });
} else if (cmd === 'merge') {
  // a batch is a .json array, or a .js file exporting one (handy: String.raw`...` needs no escaping);
  // several files can be given comma-separated and are merged as one batch
  const batch = arg.split(',').flatMap(f => f.endsWith('.js')
    ? require(path.resolve(f))
    : JSON.parse(fs.readFileSync(f, 'utf8')));
  const errs = batch.flatMap(validateEntry);
  if (errs.length) { console.error(errs.join('\n')); process.exit(1); }
  const map = new Map(text.map(t => [t.id, t]));
  batch.forEach(e => map.set(e.id, {
    id: e.id, question_latex: e.question_latex, answer_latex: e.answer_latex,
    final_answer: e.final_answer, confident: e.confident }));
  const order = new Map(progress.queue.map((id, i) => [id, i]));
  const merged = [...map.values()].sort((a, b) => order.get(a.id) - order.get(b.id));
  fs.writeFileSync(TEXT_FILE, JSON.stringify(merged, null, 1) + '\n');
  progress.batches_done += 1;
  progress.batches.push({ n: progress.batches_done, first: batch[0].id, last: batch[batch.length - 1].id,
    count: batch.length, not_confident: batch.filter(e => !e.confident).length, at: new Date().toISOString() });
  saveProgress(progress, merged);
  console.log(`merged ${batch.length}; ${merged.length} / ${progress.total} done; next ${progress.next_id}`);
} else if (cmd === 'check') {
  const errs = text.flatMap(validateEntry);
  console.log(errs.length ? errs.join('\n') : `all ${text.length} entries parse with KaTeX`);
  process.exit(errs.length ? 1 : 0);
} else {
  console.error('usage: transcribe.js status | next [n] | merge <file> | check');
  process.exit(2);
}

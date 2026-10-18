#!/usr/bin/env node
/**
 * coverage-report.js — how complete is the question bank?
 *
 * Run with `npm run coverage`. Prints, per course:
 *   - exams in exams.json, and how many have had their questions cropped
 *   - questions in the bank, and how many have an answer image
 * then lists the exams still waiting to be cropped. Use it to decide what to
 * add next (see docs/adding-an-exam.md).
 */
const fs = require('node:fs');
const path = require('node:path');

const root = path.join(__dirname, '..');
const read = f => JSON.parse(fs.readFileSync(path.join(root, f), 'utf8'));
const exams = read('exams.json');
const questions = read('questions.json');

// exams.json ids and questions' source.exam_id differ in letter case, so compare lowercase
const examKey = e => (e.id || path.basename(e.pdf || '', '.pdf')).toLowerCase();
const croppedIds = new Set(questions.map(q => (q.source && q.source.exam_id || '').toLowerCase()));

const rows = {};
const row = c => (rows[c] = rows[c] || { exams: 0, cropped: 0, questions: 0, keyed: 0 });
for (const e of exams) {
  const r = row(e.course);
  r.exams++;
  if (croppedIds.has(examKey(e))) r.cropped++;
}
for (const q of questions) {
  const r = row(q.course);
  r.questions++;
  if (q.answer_image) r.keyed++;
}

const pct = (a, b) => (b ? Math.round((a / b) * 100) + '%' : '—');
console.log('Course     Exams  Cropped   Questions  With answer');
for (const [c, r] of Object.entries(rows).sort()) {
  console.log(`${c.padEnd(10)} ${String(r.exams).padStart(5)}  ${pct(r.cropped, r.exams).padStart(7)}   ${String(r.questions).padStart(9)}  ${pct(r.keyed, r.questions).padStart(11)}`);
}

const todo = exams.filter(e => !croppedIds.has(examKey(e)) && e.pdf && e.pdf !== '#');
console.log(`\nExams not cropped yet (${todo.length}):`);
for (const e of todo) {
  const local = fs.existsSync(path.join(root, e.pdf)) ? '' : '   (PDF not in repo)';
  console.log(`  ${e.course} ${e.type}, ${e.quarter} ${e.year} — ${e.pdf}${local}`);
}

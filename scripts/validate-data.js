#!/usr/bin/env node
/**
 * validate-data.js — sanity-check the JSON data files before they ship.
 *
 * Run with `npm run validate` (CI runs it on every push and pull request).
 * Exits non-zero and lists every problem it finds, e.g. a question tagged with
 * a chapter id that doesn't exist, or a syllabus change with a typo'd term.
 * Files that are referenced but not in the repo (a PDF that hasn't been
 * uploaded yet) are printed as warnings: they show as broken links on the
 * site but shouldn't block unrelated changes.
 */
const fs = require('node:fs');
const path = require('node:path');
const { termIndex } = require('../assets/js/syllabus.js');

const root = path.join(__dirname, '..');
const read = f => JSON.parse(fs.readFileSync(path.join(root, f), 'utf8'));
const errors = [];
const warnings = [];
const fail = msg => errors.push(msg);
const warn = msg => warnings.push(msg);

const chapters  = read('chapters.json');
const questions = read('questions.json');
const exams     = read('exams.json');
const syllabus  = read('syllabus.json');

const EXAM_TYPES = new Set(['Midterm 1', 'Midterm 2', 'Final']);
// "Math 126" → Set of its chapter ids
const chapterIds = Object.fromEntries(
  Object.entries(chapters.courses).map(([c, conf]) => [c, new Set(conf.chapters.map(ch => ch.id))]));

// ── chapters.json: textbook sections (used by scripts/syllabus-check.js) look like "12.1"
for (const [c, conf] of Object.entries(chapters.courses)) {
  for (const ch of conf.chapters) {
    if (ch.sections !== undefined && !(Array.isArray(ch.sections) && ch.sections.every(s => /^\d{1,2}\.\d{1,2}$/.test(s)))) {
      fail(`chapters.json ${c} ${ch.id}: "sections" must be a list like ["12.1", "12.2"]`);
    }
  }
}
for (const [c, conf] of Object.entries(syllabus.courses || {})) {
  if (conf.source_url !== undefined && !/^https?:\/\//.test(conf.source_url)) fail(`syllabus.json ${c}: "source_url" must be an http(s) link`);
}

// ── questions.json: unique ids, known course/chapter, valid exam types, image paths that exist
const seen = new Set();
for (const q of questions) {
  const where = `questions.json ${q.id}`;
  if (seen.has(q.id)) fail(`${where}: duplicate id`);
  seen.add(q.id);
  if (!chapterIds[q.course]) { fail(`${where}: unknown course "${q.course}"`); continue; }
  if (!chapterIds[q.course].has(q.chapter)) fail(`${where}: chapter "${q.chapter}" is not in chapters.json for ${q.course}`);
  for (const t of q.exam_types || []) if (!EXAM_TYPES.has(t)) fail(`${where}: unknown exam type "${t}"`);
  // optional finer-grained skill tags, e.g. ["Chain Rule", "L'Hôpital's Rule"]
  if (q.skills !== undefined && !(Array.isArray(q.skills) && q.skills.every(k => typeof k === 'string' && k.trim()))) {
    fail(`${where}: "skills" must be a list of non-empty strings`);
  }
  // optional cross-listing into another course's chapter, e.g. [{ "course": "Math 224", "chapter": "double_integrals" }]
  for (const x of q.also_in || []) {
    if (!chapterIds[x.course] || !chapterIds[x.course].has(x.chapter)) fail(`${where}: also_in ${x.course} / ${x.chapter} is not in chapters.json`);
  }
  for (const img of [q.image, q.answer_image].filter(Boolean)) {
    if (!fs.existsSync(path.join(root, img))) warn(`${where}: missing image ${img}`);
  }
}

// ── exams.json: required fields and PDFs that exist
for (const e of exams) {
  const where = `exams.json ${e.id || e.pdf || `${e.course} ${e.type} ${e.quarter} ${e.year}`}`;
  for (const k of ['course', 'type', 'quarter', 'year', 'topics']) if (e[k] === undefined) fail(`${where}: missing "${k}"`);
  if (e.source_url !== undefined && !/^https?:\/\//.test(e.source_url)) fail(`${where}: "source_url" must be an http(s) link`);
  for (const f of [e.pdf, e.answer_key].filter(f => f && f !== '#')) {
    if (!fs.existsSync(path.join(root, f))) warn(`${where}: missing file ${f}`);
  }
}

// ── syllabus.json: known courses and chapters, well-formed terms
for (const [course, conf] of Object.entries(syllabus.courses || {})) {
  const where = `syllabus.json ${course}`;
  if (!chapterIds[course]) { fail(`${where}: course is not in chapters.json`); continue; }
  if (conf.verified && Number.isNaN(termIndex(conf.verified))) fail(`${where}: bad "verified" term "${conf.verified}" (use e.g. "Autumn 2026")`);
  for (const c of conf.changes || []) {
    if (Number.isNaN(termIndex(c.from))) fail(`${where}: bad "from" term "${c.from}"`);
    for (const id of [...(c.remove || []), ...(c.restore || [])]) {
      if (!chapterIds[course].has(id)) fail(`${where}: chapter "${id}" is not in chapters.json`);
    }
    for (const t of c.exam_types || []) if (!EXAM_TYPES.has(t)) fail(`${where}: unknown exam type "${t}"`);
  }
}

if (warnings.length) {
  // ::warning:: makes GitHub Actions show these as annotations on the run
  const prefix = process.env.GITHUB_ACTIONS ? '::warning::' : '⚠ ';
  console.warn(`${prefix}${warnings.length} referenced file(s) not in the repo (broken links on the site):`);
  warnings.slice(0, 20).forEach(w => console.warn(`  ${w}`));
  if (warnings.length > 20) console.warn(`  …and ${warnings.length - 20} more`);
}
if (errors.length) {
  console.error(`✗ ${errors.length} data problem(s):\n  ` + errors.join('\n  '));
  process.exit(1);
}
console.log(`✓ Data OK — ${questions.length} questions, ${exams.length} exams, ${Object.keys(chapterIds).length} courses.`);

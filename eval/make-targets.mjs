#!/usr/bin/env node
/**
 * make-targets.mjs — pick which questions the retrieval eval queries are about.
 *
 *   node eval/make-targets.mjs > eval/targets.json
 *
 * A seeded, stratified random sample: every course gets at least MIN targets and the
 * rest are split in proportion to course size. Choosing targets at random (instead of
 * picking questions we already transcribed, or ones that look easy) keeps the eval
 * honest. Re-running with the same seed gives the same list.
 */
import fs from 'node:fs';

const TOTAL = 150, MIN = 12, SEED = 2025;
const questions = JSON.parse(fs.readFileSync(new URL('../questions.json', import.meta.url), 'utf8'));

// mulberry32: tiny seeded PRNG so the sample is reproducible
function rng(seed) {
  return () => {
    seed |= 0; seed = (seed + 0x6D2B79F5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const rand = rng(SEED);

const byCourse = {};
questions.forEach(q => (byCourse[q.course] ||= []).push(q.id));
const courses = Object.keys(byCourse).sort();

// quotas: MIN for small courses, the remainder proportional among the big ones
const quota = {};
let small = courses.filter(c => byCourse[c].length * TOTAL / questions.length < MIN);
small.forEach(c => { quota[c] = MIN; });
const big = courses.filter(c => !small.includes(c));
const left = TOTAL - MIN * small.length;
const bigTotal = big.reduce((s, c) => s + byCourse[c].length, 0);
big.forEach(c => { quota[c] = Math.floor(left * byCourse[c].length / bigTotal); });
// hand out rounding leftovers to the largest courses
let rest = TOTAL - Object.values(quota).reduce((a, b) => a + b, 0);
[...big].sort((a, b) => byCourse[b].length - byCourse[a].length).forEach(c => { if (rest > 0) { quota[c]++; rest--; } });

const targets = [];
for (const c of courses) {
  const ids = [...byCourse[c]];
  for (let i = ids.length - 1; i > 0; i--) { const j = Math.floor(rand() * (i + 1)); [ids[i], ids[j]] = [ids[j], ids[i]]; }
  ids.slice(0, quota[c]).sort().forEach(id => targets.push({ id, course: c }));
}
console.error('quota', quota);
console.log(JSON.stringify(targets, null, 1));

// Unit tests for scripts/syllabus-check.js (the parts that don't touch the network).
const test = require('node:test');
const assert = require('node:assert/strict');
const { parseSections, compare, htmlToLines } = require('../scripts/syllabus-check.js');

test('parseSections expands ranges in the formats UW course pages use', () => {
  assert.deepEqual(parseSections('(Sec. 3.3-3.5)'), ['3.3', '3.4', '3.5']);
  assert.deepEqual(parseSections('Chapter 6: §6.1-§6.3'), ['6.1', '6.2', '6.3']);
  assert.deepEqual(parseSections('3 — 12.5–12.6; 13.1 — Planes'), ['12.5', '12.6', '13.1']);
  assert.deepEqual(parseSections('(Sec. 9.3, 3.8/9.4)'), ['3.8', '9.3', '9.4']);
  assert.deepEqual(parseSections('10 — 11.10–11.11 — Taylor series'), ['11.10', '11.11']);
});

test('parseSections ignores numbers that are not textbook sections', () => {
  assert.deepEqual(parseSections('the median grade will fall within 2.9 ± 0.2'), []);
  assert.deepEqual(parseSections('Office hours in PDL C-36, 2:30 to 3.30'), []);
  assert.deepEqual(parseSections('One 8.5 x 11 sheet of notes is allowed'), []);
});

test('htmlToLines decodes entities and splits on block tags', () => {
  const lines = htmlToLines('<li>1 &mdash; 12.1&ndash;12.2</li><li>2.9 &plusmn; 0.2</li>');
  assert.deepEqual(lines, ['1 — 12.1–12.2', '2.9 ± 0.2']);
});

test('compare proposes removals, restorations and uncovered sections', () => {
  const chapters = [
    { id: 'vectors', sections: ['12.1', '12.2'] },
    { id: 'double_integrals', sections: ['15.1', '15.2'] },
    { id: 'series', sections: ['11.1'] },
    { id: 'untracked' },                                   // no sections → never proposed
  ];
  const r = compare(chapters, new Set(['series']), ['12.1', '11.1', '16.1']);
  assert.deepEqual(r.remove, ['double_integrals']);
  assert.deepEqual(r.restore, ['series']);
  assert.deepEqual(r.uncovered, ['16.1']);
});

test('compare stays quiet when the outline matches', () => {
  const r = compare([{ id: 'a', sections: ['1.1', '1.2'] }], new Set(), ['1.1', '1.2']);
  assert.deepEqual(r, { remove: [], restore: [], uncovered: [] });
});

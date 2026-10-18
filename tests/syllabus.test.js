// Unit tests for assets/js/syllabus.js. Run with `npm test` (Node 18+, no dependencies).
const test = require('node:test');
const assert = require('node:assert/strict');
const S = require('../assets/js/syllabus.js');

test('termIndex orders quarters within and across years', () => {
  assert.ok(S.termIndex('Winter 2026') < S.termIndex('Spring 2026'));
  assert.ok(S.termIndex('Autumn 2025') < S.termIndex('Winter 2026'));
  assert.ok(Number.isNaN(S.termIndex('Fall 2026')));   // UW says "Autumn"
  assert.equal(S.termName(S.termIndex('Summer 2027')), 'Summer 2027');
});

test('currentTerm maps months to UW quarters', () => {
  assert.equal(S.currentTerm(new Date(2027, 0, 15)), 'Winter 2027');
  assert.equal(S.currentTerm(new Date(2027, 4, 1)), 'Spring 2027');
  assert.equal(S.currentTerm(new Date(2027, 6, 1)), 'Summer 2027');
  assert.equal(S.currentTerm(new Date(2027, 8, 20)), 'Autumn 2027');
});

const syllabus = {
  courses: {
    'Math 126': {
      verified: 'Autumn 2026',
      changes: [
        { from: 'Winter 2027', remove: ['taylor_series'], note: 'moved' },
        { from: 'Winter 2027', remove: ['double_integrals'], exam_types: ['Midterm 2'] },
        { from: 'Autumn 2027', restore: ['taylor_series'] },
      ],
    },
  },
};

test('a removal only applies from its start term on', () => {
  assert.equal(S.removedChapters(syllabus, 'Math 126', 'Final', 'Autumn 2026').size, 0);
  const r = S.removedChapters(syllabus, 'Math 126', 'Final', 'Winter 2027');
  assert.deepEqual([...r.keys()], ['taylor_series']);
  assert.equal(r.get('taylor_series').since, 'Winter 2027');
});

test('exam-scoped changes only hit that exam type, and are not course-wide', () => {
  assert.ok(S.removedChapters(syllabus, 'Math 126', 'Midterm 2', 'Winter 2027').has('double_integrals'));
  assert.ok(!S.removedChapters(syllabus, 'Math 126', 'Final', 'Winter 2027').has('double_integrals'));
  assert.ok(!S.removedChapters(syllabus, 'Math 126', '', 'Winter 2027').has('double_integrals'));
});

test('a later restore brings a chapter back', () => {
  assert.ok(!S.removedChapters(syllabus, 'Math 126', 'Final', 'Autumn 2027').has('taylor_series'));
});

test('unknown courses have no removals', () => {
  assert.equal(S.removedChapters(syllabus, 'Math 999', 'Final', 'Winter 2027').size, 0);
  assert.equal(S.removedChapters(null, 'Math 126', 'Final', 'Winter 2027').size, 0);
});

test('isStale flags syllabi nobody has confirmed for the current term', () => {
  assert.equal(S.isStale(syllabus, 'Math 126', 'Autumn 2026'), false);
  assert.equal(S.isStale(syllabus, 'Math 126', 'Winter 2027'), true);
  assert.equal(S.isStale(syllabus, 'Math 999', 'Autumn 2026'), true);
});

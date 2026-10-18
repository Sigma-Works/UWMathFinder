/**
 * syllabus.js — which chapters are on the *current* syllabus.
 *
 * The question bank (questions.json) holds every past problem we have, but a
 * course's syllabus can change between quarters (e.g. a topic gets dropped).
 * syllabus.json records those changes with the quarter they take effect, and
 * the functions here answer "is this chapter tested in <term>?" so the
 * generators never hand students a topic they won't be examined on.
 *
 * Pure functions with no DOM access, so they run in the browser (as the global
 * `Syllabus`) and in Node for the unit tests in tests/syllabus.test.js.
 */
(function (root) {
  'use strict';

  // UW quarters in calendar order; the index is used to compare terms.
  const QUARTERS = ['Winter', 'Spring', 'Summer', 'Autumn'];

  /**
   * Parse "Autumn 2026" into a sortable number (year * 4 + quarter index).
   * Returns NaN for anything that isn't "<Quarter> <Year>".
   */
  function termIndex(term) {
    const m = /^(Winter|Spring|Summer|Autumn)\s+(\d{4})$/.exec(String(term || '').trim());
    return m ? Number(m[2]) * 4 + QUARTERS.indexOf(m[1]) : NaN;
  }

  /** Turn a termIndex number back into "Autumn 2026". */
  function termName(index) {
    return `${QUARTERS[index % 4]} ${Math.floor(index / 4)}`;
  }

  /**
   * The UW quarter a student studying on `date` is preparing for.
   * Jan–Mar → Winter, Apr–Jun → Spring, Jul–Aug → Summer, Sep–Dec → Autumn
   * (September counts as Autumn because students are prepping for fall classes).
   */
  function currentTerm(date = new Date()) {
    const m = date.getMonth(); // 0 = January
    const q = m <= 2 ? 'Winter' : m <= 5 ? 'Spring' : m <= 7 ? 'Summer' : 'Autumn';
    return `${q} ${date.getFullYear()}`;
  }

  /**
   * Apply a course's syllabus changes up to `term` and return what was removed.
   *
   * @param {object} syllabus  parsed syllabus.json
   * @param {string} course    e.g. "Math 126"
   * @param {string} examType  e.g. "Final" — a change may be limited to some exam types;
   *                           pass '' to ask "removed from every exam?" (course-wide)
   * @param {string} term      e.g. "Winter 2027"
   * @returns {Map<string, {since: string, note: string}>} chapterId → why it's off the syllabus
   */
  function removedChapters(syllabus, course, examType, term) {
    const removed = new Map();
    const conf = syllabus && syllabus.courses && syllabus.courses[course];
    if (!conf || !Array.isArray(conf.changes)) return removed;

    const now = termIndex(term);
    // apply changes oldest-first so a later "restore" can undo an earlier "remove"
    const changes = conf.changes
      .filter(c => termIndex(c.from) <= now)
      .sort((a, b) => termIndex(a.from) - termIndex(b.from));

    for (const c of changes) {
      const scoped = Array.isArray(c.exam_types) && c.exam_types.length;
      // a change scoped to certain exams (e.g. only the Final) skips the others,
      // and doesn't count as course-wide when no exam type is given
      if (scoped && (!examType || !c.exam_types.includes(examType))) continue;
      (c.remove || []).forEach(id => removed.set(id, { since: c.from, note: c.note || '' }));
      (c.restore || []).forEach(id => removed.delete(id));
    }
    return removed;
  }

  /**
   * True when nobody has confirmed this course's syllabus for `term` yet,
   * i.e. the "verified" term in syllabus.json is older than the current one.
   * Courses with no entry at all count as unverified.
   */
  function isStale(syllabus, course, term) {
    const conf = syllabus && syllabus.courses && syllabus.courses[course];
    if (!conf || !conf.verified) return true;
    return termIndex(conf.verified) < termIndex(term);
  }

  const api = { QUARTERS, termIndex, termName, currentTerm, removedChapters, isStale };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; // Node (tests)
  else root.Syllabus = api;                                                 // browser global
})(typeof window !== 'undefined' ? window : globalThis);

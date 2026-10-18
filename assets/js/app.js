/**
 * app.js — all page behaviour for UWMathFinder (index.html).
 *
 * Sections, in order:
 *   1. Theme toggle and changelog modal
 *   2. Exam finder      — search/filter whole past exams (exams.json, Fuse.js)
 *   3. Exam generator   — build practice exams from single questions
 *                         (questions.json + chapters.json + syllabus.json)
 *   4. Shareable exam links
 *   5. Question search  — find individual problems
 *   6. Topics tested    — which chapters show up most
 *   7. Boot
 *
 * There is no build step: this file is served as-is. Data lives in the JSON
 * files at the repo root; see docs/data-format.md.
 */

// Public repo, used for the header link and "report a syllabus change" issue links.
const REPO_URL = 'https://github.com/Sigma-Works/UWMathFinder';

// ─────────────────────────────────────────────
// THEME TOGGLE (light / dark, persisted)
// ─────────────────────────────────────────────
(function initTheme(){
  const btn = document.getElementById('themeToggle');
  const icon = btn ? btn.querySelector('.theme-icon') : null;
  function current(){ return document.documentElement.getAttribute('data-theme') === 'light' ? 'light' : 'dark'; }
  function apply(theme){
    if (theme === 'light') document.documentElement.setAttribute('data-theme','light');
    else document.documentElement.removeAttribute('data-theme');
    if (icon) icon.textContent = theme === 'light' ? '☀' : '☾';
    if (btn)  btn.setAttribute('aria-label', theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode');
    // keep the browser UI theme-color in sync with the active theme
    const tc = document.querySelector('meta[name="theme-color"]');
    if (tc) tc.setAttribute('content', theme === 'light' ? '#f7f6fb' : '#0a0a0f');
  }
  apply(current());
  if (btn) btn.addEventListener('click', () => {
    const next = current() === 'light' ? 'dark' : 'light';
    try { localStorage.setItem('theme', next); } catch(e){}
    apply(next);
    if (typeof track === 'function') track('toggle_theme', { theme: next });
  });
})();

// ─────────────────────────────────────────────
// CHANGELOG (newest first)
// ─────────────────────────────────────────────
const CHANGELOG = [
  { v: 'v0.17', date: 'Oct 2026', items: [
    'Math 224 is here: Prof. Lee\'s Math 324 tests (the course\'s old number) with full solutions, plus the double-integral problems that moved over from Math 126.',
    'Every exam card now credits its instructor wherever we could confirm one: midterms by their author, and finals by every professor who gave that common final.',
    'Course menus are in numerical order.',
  ]},
  { v: 'v0.16', date: 'Oct 2026', items: [
    '30 more Math 207 exams from Prof. Loveless\'s archive. Every Math 207 and 208 exam PDF and answer key is now hosted on the site.',
    'Math 207 has 251 practice questions (up from 83), almost all with answers, and Math 208 answers went from 48 to 70.',
    'Generators follow each course\'s current UW course page. Math 207 no longer generates systems of ODEs, and topic coverage for Math 125 and 126 midterms matches their current schedules.',
    'Course pages are now checked every week. When a topic is dropped or added, we get a pull request to review right away.',
  ]},
  { v: 'v0.15', date: 'Oct 2026', items: [
    '78 more Math 125 and 126 exams from the UW Math department archive — 1,445 practice questions in total.',
    'Hundreds more answer keys, cropped by hand from the official solutions (89% of questions now have one).',
    'Every question now has skill tags you can search by.',
    'Math 126 follows its new syllabus: double integrals (Chapter 15) moved to Math 224 and are no longer generated.',
    'Exam cards show the instructor and link to where each exam was published.',
  ]},
  { v: 'v0.14', date: 'Oct 2026', items: [
    'Every past exam we host is now in the question bank, plus 9 more Math 124 midterms from the UW archive — 1,041 questions.',
    '36 more answer keys (now 72–87% of questions in Math 120–126).',
    'Skill tags on about half the questions (e.g. "Integration by parts", "Curvature") — search by skill.',
  ]},
  { v: 'v0.13', date: 'Oct 2026', items: [
    'Practice right in Search Questions — full questions inline, answers revealed in place.',
    'Mark questions Done or Needs review (saved in your browser, no account needed) and filter by them.',
    'Generator can focus on your Needs-review questions and skip ones you’ve done.',
    'Report a wrong answer or broken question in one click.',
    'New course pages with every past exam, e.g. uwmathfinder.com/courses/math-126/.',
  ]},
  { v: 'v0.12', date: 'Oct 2026', items: [
    'Generators now follow each course’s current syllabus — topics that are no longer tested are left out automatically.',
    'Old exams and questions flag topics that have since been dropped from the syllabus.',
    'UWMathFinder is now open source — find it on GitHub from the icon in the top right.',
  ]},
  { v: 'v0.11', date: 'Oct 2026', items: [
    'Midterm mode — one click to see only midterms for a course, newest first.',
    'Share a generated practice exam with a link that rebuilds the exact same paper.',
    'New "Topics Tested" view — see which chapters show up most on each course’s exams.',
    'Added a privacy policy covering the site’s analytics.',
  ]},
  { v: 'v0.10', date: 'Oct 2026', items: [
    'Light mode added, with a theme toggle that remembers your choice.',
    'This changelog! Accessibility (WCAG) and SEO improvements across the site.',
  ]},
  { v: 'v0.9', date: 'Oct 2026', items: [
    'Added Math 207 (Differential Equations) and Math 208 (Linear Algebra) — 36 exams, 200+ problems.',
    'Math 208 problems now cite the original exam’s instructor.',
  ]},
  { v: 'v0.8', date: 'Oct 2026', items: [
    'Added site analytics to understand how students use the tool.',
  ]},
  { v: 'v0.7', date: 'Oct 2026', items: [
    'New "Search Questions" tab — find individual problems, not just whole exams.',
    'Practice exam generator split into Realistic (mirrors a real UW exam’s length and topic mix) and Custom modes.',
    'Exam search now matches by quarter and year (e.g. "Math 124 Final Winter 2025").',
  ]},
  { v: 'v0.6', date: 'Oct 2026', items: [
    'Every problem now cites its source exam, term, and (where available) instructor.',
    'Corrected course labels and improved topic tagging across the question bank.',
  ]},
  { v: 'v0.5', date: 'Jun 2026', items: [
    'Launched the Practice Exam Generator — build a randomized exam from real past questions.',
  ]},
  { v: 'v0.4', date: 'Jun 2026', items: [
    'UW purple, black & gold theme. Added authors and submission link.',
  ]},
  { v: 'v0.3', date: 'Jun 2026', items: [
    'Database moved to a live file so new exams load automatically.',
  ]},
  { v: 'v0.2', date: 'Jun 2026', items: [
    'Added answer keys alongside each exam.',
  ]},
];

// Builds the changelog modal from CHANGELOG and wires open/close, Esc and a focus trap.
(function initChangelog(){
  const btn = document.getElementById('changelogBtn');
  const overlay = document.getElementById('changelogOverlay');
  const closeBtn = document.getElementById('changelogClose');
  const body = document.getElementById('changelogBody');
  const modal = document.getElementById('changelogModal');
  if (!btn || !overlay) return;
  let lastFocus = null;

  body.innerHTML = CHANGELOG.map(e => `
    <div class="cl-entry">
      <div class="cl-ver"><span class="v">${e.v}</span><span class="d">${e.date}</span></div>
      <ul>${e.items.map(i => `<li>${i}</li>`).join('')}</ul>
    </div>`).join('');

  function open(){
    lastFocus = document.activeElement;
    overlay.hidden = false;
    closeBtn.focus();
    document.addEventListener('keydown', onKey);
    if (typeof track === 'function') track('view_changelog', {});
  }
  function close(){
    overlay.hidden = true;
    document.removeEventListener('keydown', onKey);
    if (lastFocus) lastFocus.focus();
  }
  function onKey(e){
    if (e.key === 'Escape') close();
    if (e.key === 'Tab') { // simple focus trap
      const f = modal.querySelectorAll('button, a, [tabindex]:not([tabindex="-1"])');
      if (!f.length) return;
      const first = f[0], last = f[f.length-1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  }
  btn.addEventListener('click', open);
  closeBtn.addEventListener('click', close);
  overlay.addEventListener('click', e => { if (e.target === overlay) close(); });
})();

// ─────────────────────────────────────────────
// STATE — loaded from exams.json at runtime
// To add exams: edit exams.json, never this file
// ─────────────────────────────────────────────
let EXAMS = [];
let fuse  = null;

// ─────────────────────────────────────────────
// DOM REFS
// ─────────────────────────────────────────────
const searchInput   = document.getElementById('searchInput');
const clearBtn      = document.getElementById('clearBtn');
const courseFilter  = document.getElementById('courseFilter');
const typeFilter    = document.getElementById('typeFilter');
const quarterFilter = document.getElementById('quarterFilter');
const resetBtn      = document.getElementById('resetBtn');
const midtermToggle = document.getElementById('midtermToggle');
const cardsWrap     = document.getElementById('cardsWrap');
const resultsCount  = document.getElementById('resultsCount');

// Midterm mode: when on, show only midterms (both Midterm 1 & 2), newest first.
let midtermMode = false;

// ─────────────────────────────────────────────
// RENDER
// ─────────────────────────────────────────────
// escape text before it goes into innerHTML (needed for anything read from the URL)
function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, c =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

/** CSS class that colours a course badge (e.g. "Math 124" → badge-124). */
function courseClass(course) {
  if (course.includes('120')) return 'badge-120';
  if (course.includes('124')) return 'badge-124';
  if (course.includes('125')) return 'badge-125';
  if (course.includes('126')) return 'badge-126';
  if (course.includes('207')) return 'badge-207';
  if (course.includes('208')) return 'badge-208';
  if (course.includes('224')) return 'badge-224';
  return 'badge-124';
}

/** Render the exam-finder result cards (or an empty state) into #cardsWrap. */
function renderCards(exams, query) {
  resultsCount.textContent = exams.length;

  if (exams.length === 0) {
    cardsWrap.innerHTML = `
      <div class="empty">
        <div class="empty-icon">🔭</div>
        <h3>No exams found</h3>
        <p>Try a different keyword or reset your filters.</p>
      </div>`;
    return;
  }

  cardsWrap.innerHTML = exams.map(exam => {
    const title = exam.label || `${exam.course}: ${exam.type}`;   // label: e.g. an old course number
    const pdfHref = exam.pdf && exam.pdf !== '#' ? exam.pdf : null;
    const keyHref = exam.answer_key && exam.answer_key !== '#' ? exam.answer_key : null;

    return `
    <div class="card">
      <div class="card-left">
        <div class="card-meta">
          <span class="course-badge ${courseClass(exam.course)}">${exam.course}</span>
          <span class="exam-type-badge">${exam.type}</span>
        </div>
        <div class="card-title">${title}</div>
        ${exam.note ? `<p class="card-note">${esc(exam.note)}</p>` : ''}
        <div class="tags">
          ${exam.topics.map(t => {
            // grey out topics the current syllabus has dropped, so students know to skip them
            const off = offSyllabusTopic(exam.course, exam.type, t);
            return off
              ? `<span class="tag tag-off" title="No longer on the ${exam.course} syllabus (since ${off.since})">${t} · not tested now</span>`
              : `<span class="tag">${t}</span>`;
          }).join('')}
        </div>
      </div>
      <div class="card-right">
        <span class="quarter-label">${exam.quarter} ${exam.year}${exam.instructor && exam.instructor !== 'Staff' ? ` · ${esc(exam.instructor)}` : ''}</span>
        ${exam.source_url ? `<a class="source-link" href="${esc(exam.source_url)}" target="_blank" rel="noopener" title="Where this exam was published">Source ↗</a>` : ''}
        <div class="btn-row">
          ${pdfHref
            ? `<a class="view-btn" href="${pdfHref}" target="_blank" rel="noopener">↗ Exam</a>`
            : `<span class="view-btn" style="opacity:0.4;cursor:default;">Exam PDF coming</span>`}
          ${keyHref
            ? `<a class="key-btn" href="${keyHref}" target="_blank" rel="noopener">✦ Answer Key</a>`
            : `<span class="key-btn" style="opacity:0.4;cursor:default;">Key coming</span>`}
        </div>
      </div>
    </div>`;
  }).join('');
}

// ─────────────────────────────────────────────
// FILTER + SEARCH LOGIC
// ─────────────────────────────────────────────
function getFiltered() {
  const q       = searchInput.value.trim();
  const course  = courseFilter.value;
  const type    = typeFilter.value;
  const quarter = quarterFilter.value;

  let results;
  if (q.length >= 2 && !fuse) {
    // Fuse CDN failed to load — plain substring match so the finder still works
    const words = q.toLowerCase().split(/\s+/);
    results = EXAMS.filter(e => words.every(w => e._hay.includes(w)));
  } else if (q.length >= 2) {
    const hits = fuse.search(q);
    // If the best hit is strong (low score = good match), drop weak fuzzy tail
    // so a specific query like "Math 124 Final Winter 2025" returns a tight set.
    if (hits.length && hits[0].score !== undefined) {
      const best = hits[0].score;
      const cutoff = best < 0.15 ? best + 0.12 : 0.6;
      results = hits.filter(h => h.score <= cutoff).map(h => h.item);
    } else {
      results = hits.map(h => h.item);
    }
  } else {
    results = [...EXAMS];
  }

  if (course)  results = results.filter(e => e.course === course);

  if (midtermMode) {
    // Midterm mode overrides the exam-type dropdown: keep only midterms.
    results = results.filter(e => /midterm/i.test(e.type || ''));
  } else if (type) {
    results = results.filter(e => e.type === type);
  }

  if (quarter) results = results.filter(e => e.quarter === quarter);

  // Midterm mode always sorts newest first (then by course, then midterm number).
  if (midtermMode || !q) {
    results.sort((a, b) =>
      b.year - a.year ||
      a.course.localeCompare(b.course) ||
      String(a.type).localeCompare(String(b.type))
    );
  }

  return results;
}

// debounced search tracking — fire once the user pauses, not on every keystroke
let _searchTimers = {};
/** Send one analytics event per search, 1s after the user stops typing. */
function trackSearch(kind, query, count) {
  if (!query || query.length < 2) return;
  clearTimeout(_searchTimers[kind]);
  _searchTimers[kind] = setTimeout(() => {
    track('search', { search_type: kind, query: query.slice(0, 80), results: count });
  }, 1000);
}

/** Re-run the exam finder: read the filters, filter + sort, render, and track. */
/** Show "All Math 126 exams on one page →" next to the result count when a course is picked. */
function updateCoursePageLink() {
  const el = document.getElementById('coursePageLink');
  if (!el) return;
  const course = courseFilter.value;               // e.g. "Math 126"
  el.hidden = !course;
  if (course) {
    el.href = `/courses/${course.toLowerCase().replace(/\s+/g, '-')}/`;
    el.textContent = `All ${course} exams on one page →`;
  }
}

function update() {
  updateCoursePageLink();
  clearBtn.classList.toggle('visible', searchInput.value.length > 0);
  const results = getFiltered();
  renderCards(results, searchInput.value.trim());
  trackSearch('exams', searchInput.value.trim(), results.length);
}

// ─────────────────────────────────────────────
// EVENT LISTENERS
// ─────────────────────────────────────────────
searchInput.addEventListener('input', update);
courseFilter.addEventListener('change', update);
typeFilter.addEventListener('change', update);
quarterFilter.addEventListener('change', update);

clearBtn.addEventListener('click', () => {
  searchInput.value = '';
  update();
  searchInput.focus();
});

resetBtn.addEventListener('click', () => {
  searchInput.value = '';
  courseFilter.value = '';
  typeFilter.value = '';
  quarterFilter.value = '';
  setMidtermMode(false);
  update();
});

// --- Midterm mode toggle ---
function setMidtermMode(on) {
  midtermMode = on;
  midtermToggle.setAttribute('aria-pressed', on ? 'true' : 'false');
  // while midterm mode is on, the exam-type dropdown would conflict, so disable it
  typeFilter.disabled = on;
  typeFilter.style.opacity = on ? '0.4' : '';
  if (on) typeFilter.value = '';
}
midtermToggle.addEventListener('click', () => {
  setMidtermMode(!midtermMode);
  update();
  if (typeof track === 'function') track('midterm_mode', { on: midtermMode });
});

// ─────────────────────────────────────────────
// INIT — fetch exams.json and boot the app
// To add/update exams, only edit exams.json
// ─────────────────────────────────────────────
async function init() {
  cardsWrap.innerHTML = `
    <div class="empty">
      <div class="empty-icon">⏳</div>
      <h3>Loading exams...</h3>
      <p>Fetching the database.</p>
    </div>`;

  try {
    const res = await fetch("exams.json");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    EXAMS = await res.json();

    EXAMS = EXAMS.filter(e => !e.is_key);

    // add searchable string fields so queries like "Winter 2025" or
    // "Math 124 Final Winter 2025" match, not just topic keywords
    EXAMS.forEach(e => {
      e._year = String(e.year || '');
      // include the instructor so searches like "Ostroff 126" find their exams
      e._full = `${e.course} ${e.type} ${e.quarter || ''} ${e.year || ''}${e.instructor && e.instructor !== 'Staff' ? ' ' + e.instructor : ''}`;
      e._hay  = `${e._full} ${(e.topics || []).join(' ')}`.toLowerCase();
    });
    fuse = typeof Fuse === 'undefined' ? null : new Fuse(EXAMS, {
      keys: [
        { name: 'topics',  weight: 2 },
        { name: 'course',  weight: 1 },
        { name: 'type',    weight: 1 },
        { name: 'quarter', weight: 1 },
        { name: '_year',   weight: 1 },
        { name: '_full',   weight: 1.5 },
      ],
      threshold: 0.3,
      ignoreLocation: true,
      includeScore: true,
      useExtendedSearch: false,
      minMatchCharLength: 2,
    });

    update();

  } catch (err) {
    cardsWrap.innerHTML = `
      <div class="empty">
        <div class="empty-icon">⚠️</div>
        <h3>Could not load exams</h3>
        <p>Make sure <code>exams.json</code> is in the same folder and you're running a local server (<code>python3 -m http.server</code>), not opening the file directly.</p>
      </div>`;
    resultsCount.textContent = '0';
    console.error('Failed to load exams.json:', err);
  }

  // the generator is kicked off separately in boot() so it never waits on Fuse
}

// ─────────────────────────────────────────────
// PRACTICE EXAM GENERATOR  (additive feature)
// Reads chapters.json + questions.json. Independent
// of the finder above — shares nothing but the page.
// ─────────────────────────────────────────────
let CHAPTERS = null;   // { courses: { "Math 126": { chapters: [...] } } }
let QUESTIONS = [];    // [{ id, course, chapter, exam_types[], image, answer_image, ... }]
let lastExam = null;   // remembers last generated set for reshuffle
let SYLLABUS = { courses: {} };       // syllabus.json — current-syllabus overrides
const TERM = Syllabus.currentTerm();  // the quarter students are studying for right now

/** Chapters dropped from the current syllabus for this course + exam type (Map id → {since, note}). */
function offSyllabus(course, type) {
  return Syllabus.removedChapters(SYLLABUS, course, type, TERM);
}

/**
 * If an exam-card topic name (e.g. "Taylor Series") matches a chapter that's
 * been dropped from the syllabus, return {since, note}; otherwise null.
 * Exam topics are free-text names, so we match on chapter name, ignoring case.
 */
function offSyllabusTopic(course, type, topicName) {
  const removed = offSyllabus(course, type);
  if (!removed.size) return null;
  const want = String(topicName).toLowerCase();
  for (const [id, why] of removed) {
    if (chapterName(course, id).toLowerCase() === want) return why;
  }
  return null;
}

/** Link to a pre-filled GitHub issue so anyone can report a syllabus change. */
function syllabusIssueUrl(course) {
  const p = new URLSearchParams({ template: 'syllabus_change.yml', title: `Syllabus change: ${course}`, course });
  return `${REPO_URL}/issues/new?${p}`;
}

/**
 * The status line under the generate buttons: which syllabus the generator
 * follows, which topics it is leaving out, and a warning when nobody has
 * confirmed the syllabus for this quarter yet.
 */
function renderSyllabusStatus() {
  const el = document.getElementById('syllabusStatus');
  if (!el || !CHAPTERS) return;
  const course = elGenCourse.value;
  const type   = elGenType.value;
  const removed = [...offSyllabus(course, type)];
  const conf = SYLLABUS.courses[course] || {};

  let html = `Questions follow the ${esc(course)} syllabus for <strong>${esc(TERM)}</strong>.`;
  if (removed.length) {
    html += ` Left out (no longer tested): ` +
      removed.map(([id, why]) => `${esc(chapterName(course, id))} <span class="muted">(since ${esc(why.since)})</span>`).join(', ') + '.';
  }
  if (Syllabus.isStale(SYLLABUS, course, TERM)) {
    html += ` <span class="syl-warn">⚠ Last confirmed ${conf.verified ? esc(conf.verified) : 'never'} — double-check topics against your course page.</span>`;
  }
  html += ` <a href="${syllabusIssueUrl(course)}" target="_blank" rel="noopener">Syllabus changed? Tell us</a>`;
  el.innerHTML = html;
}

// Data-driven blueprints: median #problems, point total, and per-chapter
// frequency across REAL past exams. Powers the 'realistic' generator.
const EXAM_BLUEPRINTS = {"Math 120|Final":{"n":7,"pts":70,"chapters":[["linear_models",0.5],["rates",0.75],["angles",0.75],["circles",0.25],["composition",0.25],["functions",0.5],["inverses",0.25],["multipart_graphs",0.5],["angular_speed",0.25],["trig_functions",0.25],["exponentials",0.25],["circular_motion",0.75],["sinusoidal_modeling",1.0],["rational_functions",0.5]]},"Math 120|Midterm 1":{"n":4,"pts":45,"chapters":[["linear_models",0.333],["rates",0.333],["angles",0.833],["circles",0.667],["composition",0.333],["multipart_graphs",0.667],["quadratics",0.667]]},"Math 120|Midterm 2":{"n":5,"pts":50,"chapters":[["linear_models",1.0],["angles",0.6],["circles",0.2],["functions",0.4],["inverses",0.2],["multipart_graphs",0.2],["angular_speed",0.6],["exponentials",0.2],["circular_motion",0.2],["sinusoidal_modeling",0.4]]},"Math 124|Final":{"n":8,"pts":80,"chapters":[["limit_of_a_function",1.0],["continuity",1.0],["implicit_differentiation",0.294],["lines_circles_and_tangents",0.824],["linear_approximation_and_differentials",0.412],["derivatives_and_rates_of_change",0.176],["parametric_curves",0.235],["related_rates",0.412],["optimization",0.706],["maximum_and_minimum_values",0.412],["derivatives_and_shapes_of_graphs",0.706]]},"Math 124|Midterm 1":{"n":5,"pts":50,"chapters":[["limit_of_a_function",1.0],["continuity",0.833],["lines_circles_and_tangents",0.833],["tangent_and_velocity",0.083],["derivatives_and_rates_of_change",0.333]]},"Math 124|Midterm 2":{"n":5,"pts":50,"chapters":[["continuity",0.818],["implicit_differentiation",0.273],["lines_circles_and_tangents",0.909],["linear_approximation_and_differentials",0.364],["derivatives_and_rates_of_change",0.091],["parametric_curves",0.182],["related_rates",0.455]]},"Math 125|Final":{"n":10,"pts":100,"chapters":[["work_and_average_value",1.0],["integration_by_parts",0.056],["trig_substitution",0.111],["area_between_curves",0.111],["improper_integrals",0.611],["antiderivatives_and_acceleration",0.833],["mixing_and_air_resistance",0.111],["approximating_integrals",0.333],["rope_problems",0.167],["arc_length",0.389],["water_tank_problems",0.444],["leaky_bucket_problems",0.222],["volumes_by_shells",0.278],["volumes_by_cross_sectional_area",0.056],["differential_equations",1.0],["draining_a_pool_problems",0.056]]},"Math 125|Midterm 1":{"n":3,"pts":30,"chapters":[["riemann_sums_and_defining_area",0.143],["work_and_average_value",0.143],["integral_notation_and_ftoc",0.143],["area_between_curves",0.429],["antiderivatives_and_acceleration",1.0],["mixing_and_air_resistance",0.143],["approximating_integrals",0.143],["volumes_by_shells",0.286]]},"Math 125|Midterm 2":{"n":3,"pts":30,"chapters":[["improper_integrals",0.333],["antiderivatives_and_acceleration",1.0],["water_tank_problems",0.5],["leaky_bucket_problems",0.167]]},"Math 126|Final":{"n":8,"pts":80,"chapters":[["vectors_and_geometry_in_3d",1.0],["curves_in_3d_and_motion_in_space",0.842],["partial_derivatives_and_optimization",0.158],["tangent_planes_and_linear_approximation",0.526],["global_extrema_on_regions",0.316],["critical_points_and_local_extrema",0.895],["double_integrals",0.684],["taylor_polynomials",0.947],["taylor_series",0.789]]},"Math 126|Midterm 1":{"n":4,"pts":40,"chapters":[["vectors_and_geometry_in_3d",1.0],["curves_in_3d_and_motion_in_space",0.889],["critical_points_and_local_extrema",0.333],["double_integrals",0.111]]},"Math 126|Midterm 2":{"n":4,"pts":40,"chapters":[["vectors_and_geometry_in_3d",0.25],["curves_in_3d_and_motion_in_space",0.625],["tangent_planes_and_linear_approximation",0.625],["global_extrema_on_regions",0.25],["critical_points_and_local_extrema",1.0],["double_integrals",0.625]]},"Math 208|Final":{"n":8,"pts":80,"chapters":[["linear_systems_and_echelon",0.667],["linear_independence_and_basis",0.444],["linear_transformations",0.667],["vector_spaces_and_subspaces",0.556],["matrix_operations_and_inverse",0.333],["determinants",0.333],["eigenvalues_and_diagonalization",1.0]]},"Math 208|Midterm 1":{"n":4,"pts":45,"chapters":[["linear_systems_and_echelon",1.0],["linear_independence_and_basis",0.667],["linear_transformations",0.333],["vector_spaces_and_subspaces",0.167]]},"Math 208|Midterm 2":{"n":4,"pts":45,"chapters":[["linear_systems_and_echelon",0.5],["linear_independence_and_basis",0.333],["linear_transformations",0.667],["vector_spaces_and_subspaces",0.667],["matrix_operations_and_inverse",0.333],["determinants",0.333]]},"Math 207|Final":{"n":8,"pts":80,"chapters":[["initial_value_problems",0.8],["first_order_odes",0.4],["laplace_transforms",1.0],["second_order_odes",1.0],["springs_and_damping",1.0]]},"Math 207|Midterm 1":{"n":5,"pts":50,"chapters":[["initial_value_problems",1.0],["first_order_odes",0.8],["systems_of_odes",0.8],["second_order_odes",0.2],["modeling_applications",0.6]]},"Math 207|Midterm 2":{"n":5,"pts":50,"chapters":[["initial_value_problems",1.0],["first_order_odes",0.6],["second_order_odes",0.6],["springs_and_damping",0.8]]}};

const elTabFind   = document.getElementById('tabFind');
const elTabGen    = document.getElementById('tabGen');
const elViewFind  = document.getElementById('viewFind');
const elViewGen   = document.getElementById('viewGen');
const elGenCourse = document.getElementById('genCourse');
const elGenType   = document.getElementById('genType');
const elGenPerCh  = document.getElementById('genPerCh');
const elChapterList = document.getElementById('chapterList');
const elGenBtn    = document.getElementById('genBtn');
const elReshuffle = document.getElementById('genReshuffle');
const elIncludeAns= document.getElementById('genIncludeAns');
const elExamOut   = document.getElementById('examOutput');
const elGenFocus    = document.getElementById('genFocusReview');   // prefer "Needs review" questions
const elGenSkipDone = document.getElementById('genSkipDone');      // avoid questions marked done

// --- view switching ---
const elTabQ      = document.getElementById('tabQ');
const elViewQ     = document.getElementById('viewQ');
const elTabTopics = document.getElementById('tabTopics');
const elViewTopics= document.getElementById('viewTopics');
/** Switch tabs: 'find' | 'q' | 'gen' | 'topics'. Updates aria state and shows one panel. */
function showView(which) {
  const views = { find: elViewFind, q: elViewQ, gen: elViewGen, topics: elViewTopics };
  const tabs  = { find: elTabFind,  q: elTabQ,  gen: elTabGen,  topics: elTabTopics };
  Object.keys(views).forEach(k => {
    views[k].hidden = (k !== which);
    tabs[k].classList.toggle('active', k === which);
    tabs[k].setAttribute('aria-selected', k === which ? 'true' : 'false'); // a11y: reflect active tab
  });
  // keep the tab in the URL (#questions, #generate, #topics) so it can be linked and bookmarked
  const hash = TAB_HASH[which] ? '#' + TAB_HASH[which] : '';
  if (location.hash !== hash) {
    try { history.replaceState(null, '', location.pathname + location.search + hash); } catch (e) {}
  }
  window.scrollTo({ top: 0, behavior: 'smooth' });
  track('view_tab', { tab: which });
}

// tab id ↔ URL hash
const TAB_HASH = { find: '', q: 'questions', gen: 'generate', topics: 'topics' };
/** Open the tab named in the URL hash, if any (used on load and when links change the hash). */
function showViewFromHash() {
  const h = location.hash.replace('#', '');
  const tab = Object.keys(TAB_HASH).find(k => TAB_HASH[k] && TAB_HASH[k] === h);
  if (tab) showView(tab);
}
window.addEventListener('hashchange', showViewFromHash);
elTabFind.addEventListener('click',   () => showView('find'));
elTabQ.addEventListener('click',      () => showView('q'));
elTabGen.addEventListener('click',    () => showView('gen'));
elTabTopics.addEventListener('click', () => showView('topics'));

// --- populate course dropdown from chapters config ---
// courses in chapters.json that have at least one question; a course can be set up
// (chapters + syllabus) before its exams are added, and stays hidden until then
function activeCourses() {
  const withQuestions = new Set(QUESTIONS.map(q => q.course));
  return Object.keys(CHAPTERS.courses).filter(c => withQuestions.has(c))
    .sort((a, b) => parseInt(a.replace(/\D/g, ''), 10) - parseInt(b.replace(/\D/g, ''), 10));   // 120, 124, …, 224
}

function populateCourses() {
  const courses = activeCourses();
  elGenCourse.innerHTML = courses.map(c => `<option value="${c}">${c}</option>`).join('');
}

// --- count how many questions exist for a course/chapter/type ---
// index questions by course|chapter|type once, instead of scanning QUESTIONS on every call
let POOLS = new Map();
/** Build lookup tables once after the data loads (question pools, chapter names, search text). */
function buildIndexes() {
  POOLS = new Map();
  QUESTIONS.forEach(q => (q.exam_types || []).forEach(t => {
    const k = `${q.course}|${q.chapter}|${t}`;
    if (!POOLS.has(k)) POOLS.set(k, []);
    POOLS.get(k).push(q);
  }));
  CH_NAMES = new Map();
  Object.entries(CHAPTERS.courses).forEach(([co, conf]) =>
    conf.chapters.forEach(c => CH_NAMES.set(`${co}|${c.id}`, c.name)));
  // precompute lowercase haystack for the question keyword search
  QUESTIONS.forEach(q => {
    const s = q.source;
    q._hay = [
      (q.chapter || '').replace(/_/g, ' '),
      chapterName(q.course, q.chapter),
      q.course,
      (q.skills || []).join(' '),
      s ? `${s.exam} ${s.term} ${s.exam_id}` : '',
      s && s.staff ? s.staff.join(' ') : '',
    ].join(' ').toLowerCase();
  });
}
/** All questions for one course + chapter that can appear on the given exam type. */
function poolFor(course, chapterId, type) {
  return POOLS.get(`${course}|${chapterId}|${type}`) || [];
}

/** How many questions we have for a chapter (shown as "N q" in the custom picker). */
function countAvailable(course, chapterId, type) {
  return poolFor(course, chapterId, type).length;
}

// --- render the chapter checklist for the current course + exam type ---
function renderChapters() {
  const course = elGenCourse.value;
  const type   = elGenType.value;
  const conf   = CHAPTERS.courses[course];
  if (!conf) { elChapterList.innerHTML = ''; return; }

  // only chapters eligible for the selected exam type
  const eligible = conf.chapters.filter(ch => ch.types.includes(type));
  const removed  = offSyllabus(course, type);

  elChapterList.innerHTML = eligible.map(ch => {
    const n = countAvailable(course, ch.id, type);
    const off = removed.get(ch.id);
    // a chapter can't be picked if we have no questions for it, or it's off the syllabus
    const disabled = n === 0 || !!off;
    const count = off ? `not tested since ${off.since}` : `${n} q`;
    return `
      <label class="chapter-item ${disabled ? 'disabled' : ''}" ${off ? `title="Removed from the syllabus in ${off.since}"` : ''}>
        <input type="checkbox" class="ch-cb" value="${ch.id}" ${disabled ? 'disabled' : 'checked'} />
        <span class="ch-name">${ch.name}</span>
        <span class="ch-count">${count}</span>
      </label>`;
  }).join('');

  if (eligible.length === 0) {
    elChapterList.innerHTML = `<p style="color:var(--muted);font-size:0.85rem;">No chapters configured for this exam type yet.</p>`;
  }
}

/** Chapter ids currently ticked in the custom generator. */
function selectedChapters() {
  return [...elChapterList.querySelectorAll('.ch-cb:checked')].map(cb => cb.value);
}

/**
 * Shuffle a chapter's question pool, applying the student's generator options:
 *   "Focus on Needs review" → their flagged questions come first
 *   "Skip questions I've done" → done questions go last (still used if the pool runs out,
 *   so an exam never comes out short)
 */
function orderPool(pool) {
  const focus = elGenFocus && elGenFocus.checked;
  const skip  = elGenSkipDone && elGenSkipDone.checked;
  if (!focus && !skip) return shuffle(pool);
  const rank = q => {
    const st = Progress.get(q.id);
    if (focus && st === 'review') return 0;
    if (skip && st === 'done') return 2;
    return 1;
  };
  return [0, 1, 2].flatMap(r => shuffle(pool.filter(q => rank(q) === r)));
}

/** True if this course + chapter + exam has any question the student flagged for review. */
function hasReview(course, chId, type) {
  return poolFor(course, chId, type).some(q => Progress.get(q.id) === 'review');
}

// --- shuffle helper (Fisher–Yates) ---
function shuffle(arr) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

// --- build a consolidated attribution footer listing every source exam used ---
function buildAttribution(questions) {
  const exams = new Map();
  questions.forEach(q => {
    const s = q.source;
    if (!s) return;
    const key = s.exam_id || `${s.course} ${s.exam} ${s.term}`;
    if (!exams.has(key)) {
      let label = `${s.course} ${s.exam}`;
      if (s.term) label += `, ${s.term}`;
      if (s.staff && s.staff.length) label += ` (instructors: ${s.staff.join(', ')})`;
      exams.set(key, label);
    }
  });
  if (exams.size === 0) return '';
  const list = [...exams.values()].sort().map(l => `<li>${l}</li>`).join('');
  return `<div class="attrib-title">Sources &amp; attribution</div>
    <p>All problems are reproduced from the following University of Washington mathematics
    examinations, used for non-commercial student practice. Credit for each problem belongs to
    its original authors and the UW Department of Mathematics.</p>
    <ul>${list}</ul>`;
}

// --- format a problem's source citation for display + attribution ---
function formatSource(src, fallbackId) {
  if (!src || typeof src !== 'object') return 'Source: UW Math archive';
  const parts = [];
  if (src.course) parts.push(src.course);
  if (src.exam) parts.push(src.exam);
  let line = parts.join(' ');
  if (src.term) line += `, ${src.term}`;
  if (src.problem) line += ` (Problem ${src.problem})`;
  let out = `Source: ${line || fallbackId}`;
  if (src.staff && src.staff.length) {
    out += src.staff.length === 1
      ? ` · Instructor: ${src.staff[0]}`
      : ` · Instructors that term: ${src.staff.join(', ')}`;
  }
  return out;
}

// --- core: build a randomized exam spec ---
function buildExam() {
  const course = elGenCourse.value;
  const type   = elGenType.value;
  const perCh  = Math.max(1, parseInt(elGenPerCh.value || '2', 10));
  const removed  = offSyllabus(course, type);
  const chapters = selectedChapters().filter(id => !removed.has(id));

  if (chapters.length === 0) {
    return { error: 'Select at least one chapter to include.' };
  }

  const picked = [];
  const shortfall = [];
  chapters.forEach(chId => {
    const chosen = orderPool(poolFor(course, chId, type)).slice(0, perCh);
    if (chosen.length < perCh) {
      const chName = chapterName(course, chId);
      shortfall.push(`${chName} (wanted ${perCh}, had ${chosen.length})`);
    }
    picked.push(...chosen);
  });

  if (picked.length === 0) {
    return { error: 'No questions available for the selected chapters yet.' };
  }

  // order questions by the chapter order in config (keeps exam coherent)
  const rank = new Map(CHAPTERS.courses[course].chapters.map((c, i) => [c.id, i]));
  picked.sort((a, b) => (rank.get(a.chapter) ?? -1) - (rank.get(b.chapter) ?? -1));

  return { course, type, questions: picked, shortfall };
}

// --- build a REALISTIC exam matching the shape of real past exams ---
// Uses EXAM_BLUEPRINTS: target #problems + a per-chapter appearance frequency
// derived from actual exams. High-frequency chapters are near-guaranteed a slot;
// occasional ones appear at roughly their real rate. One problem per chapter slot,
// capped at the blueprint's problem count, in canonical chapter order.
function buildRealisticExam() {
  const course = elGenCourse.value;
  const type   = elGenType.value;
  const base = EXAM_BLUEPRINTS[`${course}|${type}`];
  if (!base) return { error: 'No blueprint available for this course/exam yet.' };
  // Drop chapters that are off the current syllabus. The exam keeps its usual
  // length: the top-up step below hands their slots to the remaining chapters.
  const removed = offSyllabus(course, type);
  const bp = { ...base, chapters: base.chapters.filter(([id]) => !removed.has(id)) };

  const rank = new Map(CHAPTERS.courses[course].chapters.map((c, i) => [c.id, i]));
  const pool = chId => poolFor(course, chId, type);

  // Decide which chapters are "in" this exam: always include freq>=0.8;
  // include the rest probabilistically by their real frequency.
  let slots = [];
  bp.chapters.forEach(([chId, freq]) => {
    if (pool(chId).length === 0) return;      // no questions available, skip
    // with "Focus on Needs review", chapters holding flagged questions are always included
    const focused = elGenFocus && elGenFocus.checked && hasReview(course, chId, type);
    if (focused || freq >= 0.8 || Math.random() < freq) slots.push(chId);
  });

  // Rank by frequency so if we must trim, we keep the most characteristic chapters.
  const freqOf = Object.fromEntries(bp.chapters.map(([c,f]) => [c,f]));
  slots.sort((a,b) => (freqOf[b]||0) - (freqOf[a]||0));

  // Fit to target problem count.
  const target = bp.n;
  if (slots.length > target) {
    slots = slots.slice(0, target);
  } else {
    // too few — top up by repeating the highest-frequency chapters that have spare questions
    const ranked = bp.chapters
      .filter(([c]) => pool(c).length > 0)
      .sort((a,b) => b[1]-a[1]).map(([c]) => c);
    let i = 0;
    while (slots.length < target && ranked.length) {
      slots.push(ranked[i % ranked.length]); i++;
      if (i > target * 4) break;                 // safety
    }
  }

  // Put chapters back in canonical exam order.
  slots.sort((a,b) => (rank.get(a) ?? -1) - (rank.get(b) ?? -1));

  // Pick one distinct question per slot (avoid repeating the exact same question).
  const used = new Set();
  const picked = [];
  slots.forEach(chId => {
    const fresh = orderPool(pool(chId).filter(q => !used.has(q.id)));
    const q = fresh[0] || orderPool(pool(chId))[0];
    if (q) { used.add(q.id); picked.push(q); }
  });

  if (picked.length === 0) return { error: 'Not enough questions to build a realistic exam yet.' };
  return { course, type, questions: picked, realistic: true, targetPoints: bp.pts };
}

// --- render a generated exam as a print-styled paper ---
function renderExam(spec) {
  if (spec.error) {
    elExamOut.innerHTML = `<div class="empty"><div class="empty-icon">⚠️</div><h3>${spec.error}</h3></div>`;
    elReshuffle.hidden = true;
    return;
  }

  const total = spec.questions.reduce((s, q) => s + (q.points || 10), 0);
  const showAns = elIncludeAns.checked;
  const date = new Date().toLocaleDateString('en-US', { year:'numeric', month:'long', day:'numeric' });

  const problems = spec.questions.map((q, i) => {
    // use real image if present; fall back to the bundled placeholder SVG (sample data)
    const qVisual = q._placeholder_svg
      ? q._placeholder_svg
      : `<img src="${q.image}" alt="Problem ${i+1}" loading="lazy" decoding="async" onerror="this.outerHTML='<p style=\\'color:#c00;font-size:0.8rem\\'>[missing image: ${q.image}]</p>'"/>`;

    let answer = '';
    if (showAns) {
      const aVisual = q._placeholder_svg
        ? `<svg xmlns="http://www.w3.org/2000/svg" width="680" height="90" viewBox="0 0 680 90"><rect width="680" height="90" fill="#f6f2ff"/><text x="16" y="50" font-family="Georgia,serif" font-size="13" fill="#6b4fc0">[ sample solution placeholder for ${q.id} ]</text></svg>`
        : (q.answer_image
            ? `<img src="${q.answer_image}" alt="Solution ${i+1}" loading="lazy" decoding="async" onerror="this.outerHTML='<p style=\\'color:#c00;font-size:0.8rem\\'>[missing key image]</p>'"/>`
            : `<p style="color:#999;font-size:0.82rem;">No answer key on file for this question.</p>`);
      answer = `<div class="answer-block"><div class="a-lbl">Solution</div>${aVisual}</div>`;
    }

    return `
      <div class="exam-problem">
        <div class="p-head">
          <span class="p-num">Problem ${i+1}</span>
          <span class="p-pts">(${q.points || 10} points)</span>
        </div>
        ${qVisual}
        <div class="p-src">${formatSource(q.source, q.id)}
          <button type="button" class="p-report" data-chapter="${q.chapter}">Not on your exam?</button>
        </div>
        <div class="p-tools">${progressButtons(q.id)}<a class="q-link" href="${reportUrl(q)}" target="_blank" rel="noopener">Report a problem</a></div>
        ${answer}
      </div>`;
  }).join('');

  let warn = '';
  // shared links made before a syllabus change can still contain dropped topics — say so
  const removed = offSyllabus(spec.course, spec.type);
  const stale = [...new Set(spec.questions.filter(q => removed.has(q.chapter)).map(q => chapterName(q.course, q.chapter)))];
  if (stale.length) {
    warn += `<p class="gen-note syl-warn">Heads up: this exam includes topics no longer on the ${esc(spec.course)} syllabus — ${stale.map(esc).join(', ')}. Generate a new exam to leave them out.</p>`;
  }
  if (spec.shortfall && spec.shortfall.length) {
    warn += `<p class="gen-note" style="color:var(--gold);">Note: some chapters had fewer questions than requested — ${spec.shortfall.join('; ')}. Add more to the question bank to fill these out.</p>`;
  }

  elExamOut.innerHTML = `
    ${warn}
    <div class="exam-paper" id="examPaper">
      <div class="exam-cover">
        <h2>${esc(spec.course)} — ${esc(spec.type)}</h2>
        <div class="sub">${spec.realistic ? 'Realistic Practice Examination' : 'Custom Practice Examination'} · Generated ${date} · ${spec.questions.length} problems · ${total} points · Syllabus as of ${esc(TERM)}</div>
        <div class="fields">
          <span class="f">Name:&nbsp;</span>
          <span class="f">Student ID:&nbsp;</span>
          <span class="f">Section:&nbsp;</span>
        </div>
        <ul class="exam-instructions">
          <li>This is a randomized practice exam assembled from real past UW ${esc(spec.course)} questions. Each problem is cited beneath it with its original exam and term.</li>
          <li>Show all work for full credit. Closed book; one sheet of notes permitted.</li>
          <li>Give answers in exact form unless otherwise specified.</li>
        </ul>
      </div>
      ${problems}
      <div class="exam-attrib">${buildAttribution(spec.questions)}</div>
    </div>
    <div class="paper-toolbar">
      <button class="gen-btn gold" onclick="window.print()">⎙ Print / Save as PDF</button>
      <button class="gen-btn" id="genShare">🔗 Share this exam</button>
      <button class="gen-btn ghost" id="genReshuffle2">↻ Reshuffle</button>
      <span class="share-status" id="shareStatus" aria-live="polite"></span>
    </div>`;

  elReshuffle.hidden = false;
  const rs2 = document.getElementById('genReshuffle2');
  if (rs2) rs2.addEventListener('click', regenerate);
  const shareBtn = document.getElementById('genShare');
  if (shareBtn) shareBtn.addEventListener('click', () => shareExam(spec));
}

// ─────────────────────────────────────────────
// SHAREABLE EXAM LINKS
// A generated exam is random, so a share link records exactly which
// questions were in it (their ids, in order) plus the course/type/mode and
// whether answers were shown. On load, maybeRestoreSharedExam() reads the
// ?exam= param and rebuilds the identical paper — no backend needed.
// ─────────────────────────────────────────────
const SHARE_SEP = '.';
/** Turn a generated exam into a share URL (question ids in order + course/type/mode). */
function encodeExam(spec) {
  // ids are like "q0012"; drop the leading "q" to keep the URL short
  const ids = spec.questions.map(q => (q.id || '').replace(/^q/, '')).join(SHARE_SEP);
  const params = new URLSearchParams();
  params.set('course', spec.course);
  params.set('type', spec.type);
  params.set('mode', spec.realistic ? 'r' : 'c');
  if (elIncludeAns && elIncludeAns.checked) params.set('ans', '1');
  params.set('exam', ids);
  return `${location.origin}${location.pathname}?${params.toString()}`;
}

/** Copy the share URL (or open the native share sheet) and show a confirmation. */
function shareExam(spec) {
  if (!spec || !spec.questions || !spec.questions.length) return;
  const url = encodeExam(spec);
  const status = document.getElementById('shareStatus');
  const done = msg => { if (status) { status.textContent = msg; setTimeout(() => { status.textContent = ''; }, 3500); } };

  // update the address bar so a copy/paste or bookmark also works
  try { history.replaceState(null, '', url); } catch (e) {}

  // prefer the clipboard; fall back to the native share sheet (mobile), then a prompt
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(url).then(() => done('✓ Link copied'),
      () => { if (navigator.share) navigator.share({ url }).catch(()=>{}); else done('Link is in your address bar'); });
  } else if (navigator.share) {
    navigator.share({ title: 'UWMathFinder practice exam', url }).catch(()=>{});
  } else {
    window.prompt('Copy this link to share your exam:', url);
  }
  track('share_exam', { course: spec.course, exam_type: spec.type, num_problems: spec.questions.length });
}

/** On load, if the URL has ?exam=…, rebuild that exact exam and open the generator tab. */
function maybeRestoreSharedExam() {
  const params = new URLSearchParams(location.search);
  const raw = params.get('exam');
  if (!raw) return;
  const course = params.get('course');
  const type   = params.get('type');
  const mode   = params.get('mode');
  const wantAns= params.get('ans') === '1';

  // rebuild the ordered question list from the ids in the URL
  const byId = {};
  QUESTIONS.forEach(q => { if (!q._crossListed) byId[q.id] = q; });
  const questions = raw.split(SHARE_SEP)
    .map(frag => byId['q' + frag] || byId[frag])   // tolerate ids with or without the "q"
    .filter(Boolean);

  if (!questions.length) return;   // ids didn't resolve (bank changed) — leave the normal page

  // reflect the shared settings in the controls, then switch to the generator view
  // only accept course/type values that exist in the dropdowns (URL is untrusted)
  const okCourse = course && [...elGenCourse.options].some(o => o.value === course);
  const okType   = type   && [...elGenType.options].some(o => o.value === type);
  if (okCourse) elGenCourse.value = course;
  if (okType)   elGenType.value = type;
  if (elIncludeAns) elIncludeAns.checked = wantAns;
  showView('gen');

  const spec = {
    course: okCourse ? course : (questions[0] && questions[0].course) || '',
    type:   okType   ? type   : 'Final',
    questions,
    realistic: mode === 'r',
    shared: true,
  };
  lastExam = spec;
  lastMode = spec.realistic ? 'realistic' : 'custom';
  renderExam(spec);
  track('open_shared_exam', { course: spec.course, exam_type: spec.type, num_problems: questions.length });
}

let lastMode = 'custom';   // which generator the user last ran (for Reshuffle)
/** Build a new exam in the last-used mode (realistic or custom), render it, and track it. */
function regenerate() {
  const spec = (lastMode === 'realistic') ? buildRealisticExam() : buildExam();
  lastExam = spec;
  renderExam(spec);
  elExamOut.scrollIntoView({ behavior: 'smooth', block: 'start' });
  if (!spec.error) {
    track('generate_exam', {
      mode: lastMode,
      course: spec.course,
      exam_type: spec.type,
      num_problems: spec.questions.length,
    });
  }
}
const elCustomControls = document.getElementById('customControls');
// "Generate Custom Exam" reveals the chapter/question controls (doesn't generate yet)
function revealCustom() {
  renderChapters();                       // make sure chapters reflect current course/exam
  elCustomControls.hidden = false;
  elCustomControls.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}
// "Build Custom Exam" (inside the revealed panel) actually generates
function buildCustomNow()    { lastMode = 'custom';    regenerate(); }
// "Generate Realistic Exam" button: hides the custom panel and builds a realistic exam
function generateRealistic() { lastMode = 'realistic'; elCustomControls.hidden = true; regenerate(); }

// --- wire up generator controls ---
elGenCourse.addEventListener('change', () => { renderSyllabusStatus(); if (!elCustomControls.hidden) renderChapters(); });
elGenType.addEventListener('change',   () => { renderSyllabusStatus(); if (!elCustomControls.hidden) renderChapters(); });
// "Not on your exam?" under each generated problem: one click logs which topic
// students think is off-syllabus, so maintainers can spot changes early.
elExamOut.addEventListener('click', e => {
  const prog = e.target.closest('.prog-btn');
  if (prog) { handleProgressClick(prog); return; }
  const btn = e.target.closest('.p-report');
  if (!btn || btn.disabled) return;
  track('report_off_syllabus', { course: lastExam && lastExam.course, exam_type: lastExam && lastExam.type, chapter: btn.dataset.chapter });
  btn.textContent = 'Thanks — noted';
  btn.disabled = true;
});
elGenBtn.addEventListener('click', revealCustom);
document.getElementById('genBuildCustom').addEventListener('click', buildCustomNow);
document.getElementById('genRealisticBtn').addEventListener('click', generateRealistic);
elReshuffle.addEventListener('click', regenerate);
elIncludeAns.addEventListener('change', () => { if (lastExam) renderExam(lastExam); });
document.getElementById('chAll').addEventListener('click', () => {
  elChapterList.querySelectorAll('.ch-cb:not(:disabled)').forEach(cb => cb.checked = true);
});
document.getElementById('chNone').addEventListener('click', () => {
  elChapterList.querySelectorAll('.ch-cb').forEach(cb => cb.checked = false);
});

/**
 * syllabus.json is optional: if it's missing or broken we fall back to "no
 * overrides", and every course shows the "not confirmed" warning instead.
 */
async function loadSyllabus() {
  try {
    const res = await fetch('syllabus.json');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return data && data.courses ? data : { courses: {} };
  } catch (err) {
    console.warn('syllabus.json not loaded; using the full chapter list:', err);
    return { courses: {} };
  }
}

/**
 * A question can also count toward another course: `also_in: [{course, chapter}]` (e.g. Math 126's
 * double integrals, a topic that moved to Math 224). Each listing becomes a copy in that course and
 * chapter, with that chapter's exam types. Copies keep the id, so progress marks and share links
 * are shared, and Search shows each question once unless a course is picked.
 */
function withCrossListings(list) {
  const out = [...list];
  list.forEach(q => (q.also_in || []).forEach(({ course, chapter }) => {
    const ch = CHAPTERS.courses[course] && CHAPTERS.courses[course].chapters.find(c => c.id === chapter);
    if (ch) out.push({ ...q, course, chapter, exam_types: ch.types, _crossListed: true });
  }));
  return out;
}

// --- load generator data (kicked off from boot, independent of Fuse) ---
let _generatorStarted = false;
/** Fetch chapters, questions and syllabus, then start the generator, question search and topics. */
async function loadGenerator() {
  if (_generatorStarted) return;   // guard: only load once
  _generatorStarted = true;
  try {
    const [chRes, qRes] = await Promise.all([
      fetch('chapters.json'),
      fetch('questions.json'),
    ]);
    if (!chRes.ok || !qRes.ok) throw new Error('generator data missing');
    CHAPTERS  = await chRes.json();
    QUESTIONS = withCrossListings(await qRes.json());
    SYLLABUS  = await loadSyllabus();
    buildIndexes();
    populateCourses();
    renderChapters();
    initQuestionSearch();
    initTopics();
    renderSyllabusStatus();
    if (EXAMS.length) update();  // re-render exam cards so dropped topics get flagged
    maybeRestoreSharedExam();   // if the URL carries a shared exam, rebuild it
  } catch (err) {
    console.warn('Generator data not loaded:', err);
    elChapterList.innerHTML = `<p style="color:var(--muted);font-size:0.85rem;">Generator data (chapters.json / questions.json) not found. The exam finder still works.</p>`;
    elGenBtn.disabled = true;
  }
}

// ─────────────────────────────────────────────
// QUESTION SEARCH (individual problems)
// ─────────────────────────────────────────────
const elQSearch      = document.getElementById('qSearchInput');
const elQClear       = document.getElementById('qClearBtn');
const elQCourse      = document.getElementById('qCourseFilter');
const elQChapter     = document.getElementById('qChapterFilter');
const elQType        = document.getElementById('qTypeFilter');
const elQReset       = document.getElementById('qResetBtn');
const elQCards       = document.getElementById('qCardsWrap');
const elQCount       = document.getElementById('qResultsCount');
const elQProgress    = document.getElementById('qProgressFilter');   // All / Not done / Needs review / Done
const elQProgressInfo= document.getElementById('qProgressInfo');

let CH_NAMES = new Map();
/** Human-readable chapter name, falling back to the id if it's unknown. */
function chapterName(course, chId) {
  return CH_NAMES.get(`${course}|${chId}`) || chId;
}

/** Fill the Search Questions chapter dropdown for the chosen course (or all courses). */
function populateQChapters() {
  const course = elQCourse.value;
  let opts = '<option value="">All Chapters</option>';
  if (course && CHAPTERS.courses[course]) {
    CHAPTERS.courses[course].chapters.forEach(c => {
      opts += `<option value="${c.id}">${c.name}</option>`;
    });
  } else {
    // all chapters across courses, labeled
    const seen = new Set();
    activeCourses().forEach(co => {
      CHAPTERS.courses[co].chapters.forEach(c => {
        const key = co + '|' + c.id;
        if (!seen.has(key)) { seen.add(key); opts += `<option value="${c.id}">${co.replace('Math ','')} · ${c.name}</option>`; }
      });
    });
  }
  elQChapter.innerHTML = opts;
}

/** Questions matching the Search Questions filters, keyword and progress filter. */
function filterQuestions() {
  const kw     = elQSearch.value.trim().toLowerCase();
  const course = elQCourse.value;
  const chap   = elQChapter.value;
  const type   = elQType.value;
  const prog   = elQProgress.value;   // '' | 'todo' | 'review' | 'done'

  return QUESTIONS.filter(q => {
    if (course ? q.course !== course : q._crossListed) return false;
    if (chap   && q.chapter !== chap)  return false;
    if (type   && !(q.exam_types || []).includes(type)) return false;
    if (kw && !q._hay.includes(kw)) return false;
    if (prog) {
      const st = Progress.get(q.id);
      if (prog === 'todo' ? st === 'done' : st !== prog) return false;
    }
    return true;
  });
}

/** Pre-filled GitHub issue for "this question / answer is wrong or broken". */
function reportUrl(q) {
  const s = q.source || {};
  const title = `Problem with ${q.id} (${q.course} ${s.exam || ''}${s.term ? ', ' + s.term : ''}${s.problem ? ', P' + s.problem : ''})`;
  const p = new URLSearchParams({ template: 'bug_report.yml', title, where: `Question ${q.id}` });
  return `${REPO_URL}/issues/new?${p}`;
}

/** The "Done" / "Needs review" toggle buttons for one question, reflecting saved progress. */
function progressButtons(id) {
  const st = Progress.get(id);
  return `
    <button type="button" class="prog-btn ${st === 'done' ? 'on' : ''}" data-action="done" data-id="${id}" aria-pressed="${st === 'done'}">✓ Done</button>
    <button type="button" class="prog-btn review ${st === 'review' ? 'on' : ''}" data-action="review" data-id="${id}" aria-pressed="${st === 'review'}">⚑ Needs review</button>`;
}

/** One practice card: full question inline, answer revealed in place, progress buttons. */
function questionCard(q) {
  const src = q.source || {};
  const off = offSyllabus(q.course, '').get(q.chapter);   // course-wide removals only
  const offTag = off ? `<span class="q-lowconf" title="Removed from the ${q.course} syllabus in ${off.since}">· not on current syllabus</span>` : '';
  const lc = q.low_confidence ? `<span class="q-lowconf" title="This topic label was auto-assigned and hasn't been verified yet.">· unverified tag</span>` : '';
  const skills = (q.skills || []).map(k => `<span class="tag skill-tag">${esc(k)}</span>`).join('');
  // the answer image's src is only set when it's first revealed, so we don't download every key up front
  const answer = q.answer_image
    ? `<button type="button" class="key-btn" data-action="answer" data-id="${q.id}" aria-expanded="false">✦ Show answer</button>`
    : `<a class="key-btn muted-btn" href="${REPO_URL}/blob/main/CONTRIBUTING.md" target="_blank" rel="noopener" title="No answer key yet — you can help add one">No key yet · help add one</a>`;
  return `
    <article class="q-card" id="card-${q.id}" data-status="${Progress.get(q.id) || ''}">
      <div class="q-meta">
        <span class="course-badge ${courseClass(q.course)}">${q.course}</span>
        <span class="q-chapter">${chapterName(q.course, q.chapter)}</span>
        ${lc}${offTag}
        <span class="q-source">${src.exam || ''}${src.term ? ', ' + src.term : ''}${src.problem ? ' · Problem ' + src.problem : ''}</span>
      </div>
      ${skills ? `<div class="tags">${skills}</div>` : ''}
      <div class="q-figure" id="fig-${q.id}"><img src="${q.image}" alt="${q.course} ${chapterName(q.course, q.chapter)} question ${q.id}" loading="lazy" decoding="async"
        onerror="this.style.opacity='0.3';this.alt='[image missing]'"/></div>
      <button type="button" class="q-expand" data-action="expand" data-id="${q.id}" aria-expanded="false">Show full question ▾</button>
      <div class="q-answer" id="ans-${q.id}" hidden>${q.answer_image ? `<img data-src="${q.answer_image}" alt="Solution to question ${q.id}" decoding="async"/>` : ''}</div>
      <div class="q-actions">
        ${answer}
        ${progressButtons(q.id)}
        <a class="q-link" href="${q.image}" target="_blank" rel="noopener">Full size ↗</a>
        <a class="q-link" href="${reportUrl(q)}" target="_blank" rel="noopener">Report a problem</a>
      </div>
    </article>`;
}

const Q_PAGE = 30;        // cards per "page"; more are added with "Load more"
let qResults = [];        // current filtered list
let qShown = 0;           // how many of qResults are on screen

/** Render the first page of results (call after the filters change). */
function renderQCards(list) {
  qResults = list;
  qShown = 0;
  elQCount.textContent = list.length;
  renderQProgress();
  if (list.length === 0) {
    elQCards.innerHTML = `<div class="empty"><div class="empty-icon">🔭</div><h3>No questions found</h3><p>Try a different keyword or clear the filters.</p></div>`;
    return;
  }
  elQCards.innerHTML = '';
  appendQPage();
}

/** Add the next Q_PAGE cards plus a "Load more" button if there are more. */
function appendQPage() {
  const old = document.getElementById('qLoadMore');
  if (old) old.remove();
  const next = qResults.slice(qShown, qShown + Q_PAGE);
  qShown += next.length;
  elQCards.insertAdjacentHTML('beforeend', next.map(questionCard).join(''));
  if (qShown < qResults.length) {
    elQCards.insertAdjacentHTML('beforeend',
      `<button type="button" class="gen-btn ghost load-more" id="qLoadMore">Load more (${qResults.length - qShown} left)</button>`);
  }
}

/** "You've done X of Y · Z to review" line for the current filter (course/chapter/type, ignoring the progress filter). */
function renderQProgress() {
  if (!elQProgressInfo) return;
  const saved = elQProgress.value;
  elQProgress.value = '';                 // count across the whole selection, not just one status
  const ids = filterQuestions().map(q => q.id);
  elQProgress.value = saved;
  const { done, review } = Progress.counts(ids);
  elQProgressInfo.innerHTML = ids.length
    ? `Your progress here: <strong>${done}</strong> of ${ids.length} done${review ? ` · <strong>${review}</strong> to review` : ''} <span class="muted">(saved in this browser)</span>`
    : '';
}

/** Re-run Search Questions: filter, render, and track the search. */
function updateQ() {
  elQClear.classList.toggle('visible', elQSearch.value.length > 0);
  const results = filterQuestions();
  renderQCards(results);
  trackSearch('questions', elQSearch.value.trim(), results.length);
}

/**
 * Handle Done / Needs review clicks anywhere (question cards and generated exams):
 * save the new state and update every button for that question on the page.
 */
function handleProgressClick(btn) {
  const id = btn.dataset.id;
  const state = Progress.toggle(id, btn.dataset.action);
  document.querySelectorAll(`.prog-btn[data-id="${id}"]`).forEach(b => {
    const on = b.dataset.action === state;
    b.classList.toggle('on', on);
    b.setAttribute('aria-pressed', on);
  });
  const card = document.getElementById(`card-${id}`);
  if (card) card.dataset.status = state || '';
  renderQProgress();
  track('mark_question', { state: state || 'cleared' });
}

/** Show/hide a question's answer in place, loading the image the first time. */
function toggleAnswer(btn) {
  const box = document.getElementById(`ans-${btn.dataset.id}`);
  if (!box) return;
  const img = box.querySelector('img[data-src]');
  if (img) { img.src = img.dataset.src; img.removeAttribute('data-src'); }
  box.hidden = !box.hidden;
  btn.setAttribute('aria-expanded', String(!box.hidden));
  btn.textContent = box.hidden ? '✦ Show answer' : '✦ Hide answer';
  if (!box.hidden) track('show_answer', {});
}

/** Expand/collapse a question image (collapsed cards show just the top of the problem). */
function toggleFigure(btn) {
  const fig = document.getElementById(`fig-${btn.dataset.id}`);
  if (!fig) return;
  const open = fig.classList.toggle('expanded');
  btn.setAttribute('aria-expanded', String(open));
  btn.textContent = open ? 'Show less ▴' : 'Show full question ▾';
}

/** Wire up the Search Questions controls once the question bank is loaded. */
function initQuestionSearch() {
  populateQChapters();
  updateQ();
  elQSearch.addEventListener('input', updateQ);
  elQCourse.addEventListener('change', () => { populateQChapters(); updateQ(); });
  elQChapter.addEventListener('change', updateQ);
  elQType.addEventListener('change', updateQ);
  elQProgress.addEventListener('change', updateQ);
  elQClear.addEventListener('click', () => { elQSearch.value=''; updateQ(); elQSearch.focus(); });
  elQReset.addEventListener('click', () => {
    elQSearch.value=''; elQCourse.value=''; elQType.value=''; elQProgress.value='';
    populateQChapters(); updateQ();
  });
  // one listener for every card's buttons (cards are re-rendered often)
  elQCards.addEventListener('click', e => {
    const btn = e.target.closest('button');
    if (!btn) return;
    if (btn.id === 'qLoadMore') appendQPage();
    else if (btn.dataset.action === 'answer') toggleAnswer(btn);
    else if (btn.dataset.action === 'expand') toggleFigure(btn);
    else if (btn.dataset.action === 'done' || btn.dataset.action === 'review') handleProgressClick(btn);
  });
}

// ─────────────────────────────────────────────
// TOPICS MOST OFTEN TESTED
// Built from the tagged question bank (QUESTIONS): for the chosen course
// (and optional exam type), count how many questions fall in each chapter,
// then rank chapters by share. This reflects how often each topic appears
// in the archived exams we have.
// ─────────────────────────────────────────────
const elTopicsCourse = document.getElementById('topicsCourse');
const elTopicsType   = document.getElementById('topicsType');
const elTopicsWrap   = document.getElementById('topicsWrap');
const elTopicsInfo   = document.getElementById('topicsInfo');

/** Count questions per chapter for a course (and optional exam type), ranked by share. */
function computeTopics(course, type) {
  // tally questions per chapter for this course (+ exam type if chosen)
  const counts = {};
  let total = 0;
  QUESTIONS.forEach(q => {
    if (q.course !== course) return;
    if (type && !(q.exam_types || []).includes(type)) return;
    counts[q.chapter] = (counts[q.chapter] || 0) + 1;
    total++;
  });
  const removed = offSyllabus(course, type);
  const rows = Object.keys(counts).map(chId => ({
    id: chId,
    off: removed.get(chId) || null,   // set when this chapter is no longer tested
    name: chapterName(course, chId),
    count: counts[chId],
    pct: total ? counts[chId] / total : 0,
  }));
  rows.sort((a, b) => b.count - a.count || a.name.localeCompare(b.name));
  return { rows, total };
}

/** Draw the Topics Tested bar list for the selected course and exam. */
function renderTopics() {
  if (!CHAPTERS || !QUESTIONS.length) {
    elTopicsInfo.textContent = 'Topic data not available.';
    elTopicsWrap.innerHTML = '';
    return;
  }
  const course = elTopicsCourse.value;
  const type   = elTopicsType.value;
  const { rows, total } = computeTopics(course, type);

  const scope = type ? `${course} ${type}` : `${course} (all exams)`;
  if (total === 0) {
    elTopicsInfo.textContent = `No tagged questions for ${scope} yet.`;
    elTopicsWrap.innerHTML = `<div class="empty"><div class="empty-icon">📊</div><h3>Nothing to chart yet</h3><p>No questions are tagged for this selection.</p></div>`;
    return;
  }

  elTopicsInfo.innerHTML = `Ranked by share of <span class="results-count">${total}</span> tagged questions in ${scope}`;
  const max = rows[0].pct || 1;   // scale bars so the top topic fills the track

  elTopicsWrap.innerHTML = rows.map((r, i) => `
    <div class="topic-row${r.off ? ' topic-off' : ''}">
      <div class="topic-row-head">
        <span><span class="topic-rank">#${i + 1}</span><span class="topic-name">${r.name}</span>${r.off ? `<span class="topic-offnote"> · not tested since ${r.off.since}</span>` : ''}</span>
        <span class="topic-stat">${Math.round(r.pct * 100)}% · ${r.count} q</span>
      </div>
      <div class="topic-bar-track">
        <div class="topic-bar-fill" style="width:${Math.max(4, (r.pct / max) * 100)}%"></div>
      </div>
    </div>`).join('')
    + `<p class="topics-note">Based on the exams currently in the archive, not an official UW distribution. More exams make this more accurate.</p>`;
}

/** Fill the Topics Tested course dropdown and wire its controls. */
function initTopics() {
  if (!CHAPTERS) return;
  // course dropdown from the chapters config (same source as the generator)
  const courses = activeCourses();
  elTopicsCourse.innerHTML = courses.map(c => `<option value="${c}">${c}</option>`).join('');
  elTopicsCourse.addEventListener('change', () => { renderTopics(); track('view_topics', { course: elTopicsCourse.value, exam_type: elTopicsType.value }); });
  elTopicsType.addEventListener('change',   () => { renderTopics(); track('view_topics', { course: elTopicsCourse.value, exam_type: elTopicsType.value }); });
  renderTopics();
}

// ─────────────────────────────────────────────
// BOOT
// app.js and Fuse.js are both `defer` scripts, so the browser runs them in
// order: by the time we get here Fuse is loaded (or failed to load, in which
// case the finder falls back to plain substring search).
// ─────────────────────────────────────────────
loadGenerator();   // question bank, chapters, syllabus — needed by generator, search, topics
init();            // exam finder
showViewFromHash();   // e.g. uwmathfinder.com/#generate opens the generator directly

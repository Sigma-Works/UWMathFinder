/**
 * assistant.mjs — "Find similar past exam questions" (beta, behind ?assistant=1).
 *
 * Loaded by a one-line dynamic import at the end of app.js, only when the URL has
 * ?assistant=1, so the normal page never downloads it. This file itself is small:
 * the heavy parts (transformers.js + the embedding model, the index, KaTeX) are only
 * fetched when the student actually opens the Ask tab (see loadResources), and the
 * browser caches them for next time.
 *
 * How a search works:
 *   1. embed the query with the same model that built the index (MODEL / DTYPE)
 *   2. cosine-rank every question against it (topK in assistant-rank.mjs)
 *   3. render the best 5 as cards, with LaTeX rendered by KaTeX
 *
 * Analytics go through the page's existing track() helper (index.html):
 *   assistant_open, assistant_search {course}, assistant_result_click {question_id},
 *   assistant_feedback {rating, question_id}
 */
import { decodeIndex, topK, courseFilter } from './assistant-rank.mjs';

// must match scripts/assistant-text.mjs, which built the index
const MODEL = 'Xenova/all-MiniLM-L6-v2';
const DTYPE = 'q8';
const TRANSFORMERS_URL = 'https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.1.2';
const KATEX_BASE = 'https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.11/';
const RESULTS = 5;

const log = (name, params) => { if (typeof track === 'function') track(name, params || {}); };
const esc = s => String(s ?? '').replace(/[&<>"']/g, c =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

// ─────────────────────────────────────────────
// TAB + PANEL (built here, so index.html is unchanged)
// ─────────────────────────────────────────────
const COURSES = ['Math 120', 'Math 124', 'Math 125', 'Math 126', 'Math 207', 'Math 208', 'Math 224'];

const style = document.createElement('style');
style.textContent = `
  .as-status { margin: 1rem 0; color: var(--muted); font-size: .9rem; }
  .as-bar { height: 4px; background: var(--border); border-radius: 2px; overflow: hidden; margin-top: .4rem; }
  .as-bar > span { display: block; height: 100%; width: 0; background: var(--accent); transition: width .2s; }
  .as-form { display: flex; gap: .5rem; flex-wrap: wrap; align-items: center; }
  .as-form .search-box { flex: 1 1 18rem; }
  .as-latex { margin: .6rem 0; line-height: 1.6; overflow-x: auto; }
  .as-latex .katex-display { margin: .4rem 0; }
  .as-note { font-size: .78rem; color: var(--muted); }
  .as-score { font-size: .78rem; color: var(--muted); margin-left: auto; }
  .as-feedback button { background: none; border: 1px solid var(--border); border-radius: 6px; cursor: pointer; padding: .15rem .5rem; color: inherit; }
  .as-feedback button.on { border-color: var(--accent); }
  .as-solution { margin-top: .6rem; padding: .6rem .8rem; border-left: 3px solid var(--gold); background: var(--surface, transparent); }
`;
document.head.appendChild(style);

const tab = document.createElement('button');
tab.className = 'view-tab';
tab.id = 'tabAssistant';
tab.setAttribute('role', 'tab');
tab.setAttribute('aria-selected', 'false');
tab.setAttribute('aria-controls', 'viewAssistant');
tab.innerHTML = '✧ <span class="tab-gold">Ask</span> (beta)';
document.querySelector('.view-nav').appendChild(tab);

const panel = document.createElement('div');
panel.className = 'view-panel';
panel.id = 'viewAssistant';
panel.setAttribute('role', 'tabpanel');
panel.setAttribute('aria-labelledby', 'tabAssistant');
panel.hidden = true;
panel.innerHTML = `
  <section class="hero">
    <div class="hero-eyebrow">Study assistant · beta</div>
    <h1>Find <em>similar</em> past questions</h1>
    <p class="hero-sub">Describe a problem or a topic, e.g. "related rates ladder" or
      "Math 125 integration by parts". Everything runs in your browser: your search never leaves this page.</p>
  </section>
  <form class="as-form search-wrap" id="asForm">
    <div class="search-box">
      <span class="search-icon">⌕</span>
      <input class="search-input" id="asQuery" type="search" autocomplete="off"
        aria-label="Describe a problem or topic" placeholder="e.g. &quot;ladder sliding down a wall&quot;" disabled />
    </div>
    <select class="filter-select" id="asCourse" aria-label="Course">
      <option value="">All courses</option>
      ${COURSES.map(c => `<option value="${c}">${c}</option>`).join('')}
    </select>
    <button class="gen-btn" id="asGo" type="submit" disabled>Search</button>
  </form>
  <div class="as-status" id="asStatus" role="status" aria-live="polite"></div>
  <div class="cards-wrap" id="asResults"></div>`;
document.querySelector('#main').appendChild(panel);

const elQuery = panel.querySelector('#asQuery');
const elCourse = panel.querySelector('#asCourse');
const elGo = panel.querySelector('#asGo');
const elStatus = panel.querySelector('#asStatus');
const elResults = panel.querySelector('#asResults');

/** Show our panel and hide the others (app.js's showView doesn't know about us). */
function openTab() {
  document.querySelectorAll('.view-panel').forEach(p => { p.hidden = p !== panel; });
  document.querySelectorAll('.view-tab').forEach(t => {
    t.classList.toggle('active', t === tab);
    t.setAttribute('aria-selected', t === tab ? 'true' : 'false');
  });
  if (location.hash !== '#assistant') {
    try { history.replaceState(null, '', location.pathname + location.search + '#assistant'); } catch (e) {}
  }
  log('assistant_open');
  loadResources();
  elQuery.focus();
}
tab.addEventListener('click', openTab);
// any other tab: app.js shows its panel; we just hide ours
document.querySelectorAll('.view-tab').forEach(t => {
  if (t !== tab) t.addEventListener('click', () => { panel.hidden = true; tab.classList.remove('active'); tab.setAttribute('aria-selected', 'false'); });
});
if (location.hash === '#assistant') openTab();

// ─────────────────────────────────────────────
// LAZY LOADING (only after the tab is opened)
// ─────────────────────────────────────────────
let ready = null;        // Promise of everything below, started once
let extractor, rows, manifest, questionsById, chapterNames, examsById, textById, solutionFiles;

function status(html, pct) {
  elStatus.innerHTML = html + (pct == null ? '' : `<div class="as-bar"><span style="width:${pct}%"></span></div>`);
}

function loadScript(src) {
  return new Promise((resolve, reject) => {
    const s = document.createElement('script');
    s.src = src; s.onload = resolve; s.onerror = () => reject(new Error('failed to load ' + src));
    document.head.appendChild(s);
  });
}

function loadKatex() {
  const css = document.createElement('link');
  css.rel = 'stylesheet'; css.href = KATEX_BASE + 'katex.min.css';
  document.head.appendChild(css);
  return loadScript(KATEX_BASE + 'katex.min.js').then(() => loadScript(KATEX_BASE + 'contrib/auto-render.min.js'));
}

const getJSON = url => fetch(url).then(r => { if (!r.ok) throw new Error(`${url}: HTTP ${r.status}`); return r.json(); });

function loadResources() {
  if (ready) return ready;
  status('Loading the study assistant… (first time only: about 24 MB, then it\'s cached)', 0);
  const files = new Map();   // model file → [loaded, total], for the progress bar
  const onProgress = p => {
    if (p.status !== 'progress' || !p.total) return;
    files.set(p.file, [p.loaded, p.total]);
    let loaded = 0, total = 0;
    files.forEach(([l, t]) => { loaded += l; total += t; });
    status(`Downloading the search model… ${(loaded / 1e6).toFixed(1)} / ${(total / 1e6).toFixed(1)} MB`, Math.round(100 * loaded / total));
  };

  ready = Promise.all([
    import(TRANSFORMERS_URL).then(({ pipeline }) =>
      pipeline('feature-extraction', MODEL, { dtype: DTYPE, progress_callback: onProgress })),
    getJSON('assets/assistant/index.json'),
    fetch('assets/assistant/index.bin').then(r => r.arrayBuffer()),
    getJSON('questions.json'),        // already in the HTTP cache from the main page
    getJSON('chapters.json'),
    getJSON('exams.json'),
    getJSON('questions_text.json'),
    loadKatex(),
  ]).then(([ext, man, bin, questions, chapters, exams, texts]) => {
    extractor = ext;
    manifest = man;
    rows = decodeIndex(bin);
    questionsById = new Map(questions.map(q => [q.id, q]));
    chapterNames = new Map();
    Object.entries(chapters.courses).forEach(([c, conf]) => conf.chapters.forEach(ch => chapterNames.set(`${c}|${ch.id}`, ch.name)));
    // questions.json and exams.json spell some ids with different case (m124finalAut2025 / m124finalaut2025)
    examsById = new Map(exams.map(e => [e.id.toLowerCase(), e]));
    solutionFiles = new Map(man.solutions.map(s => [s.toLowerCase(), s]));
    textById = new Map(texts.map(t => [t.id, t]));
    status(`Ready. Searching ${manifest.count.toLocaleString()} past exam questions.`);
    elQuery.disabled = false;
    elGo.disabled = false;
    elQuery.focus();
  }).catch(err => {
    console.error('Study assistant failed to load:', err);
    status('Sorry, the study assistant could not load. Check your connection and reload the page.');
    ready = null;   // allow a retry on the next open
  });
  return ready;
}

// ─────────────────────────────────────────────
// SEARCH
// ─────────────────────────────────────────────
async function embed(text) {
  const t = await extractor(text, { pooling: 'mean', normalize: true });
  return t.data;   // Float32Array, length manifest.dims, already L2-normalized
}

async function search(e) {
  e.preventDefault();
  const query = elQuery.value.trim();
  if (!query || !extractor) return;
  const course = elCourse.value;
  log('assistant_search', { course: course || 'all' });
  status('Searching…');
  const qvec = await embed(query);
  const hits = topK(qvec, rows, manifest.dims, manifest.ids, courseFilter(questionsById, course), RESULTS);
  render(hits);
  status(`Top ${hits.length} matches${course ? ' in ' + esc(course) : ''}.`);
}
panel.querySelector('#asForm').addEventListener('submit', search);

// ─────────────────────────────────────────────
// RESULT CARDS
// ─────────────────────────────────────────────
function renderMath(el) {
  if (typeof renderMathInElement !== 'function') return;
  renderMathInElement(el, {
    delimiters: [
      { left: '$$', right: '$$', display: true }, { left: '\\[', right: '\\]', display: true },
      { left: '\\(', right: '\\)', display: false }, { left: '$', right: '$', display: false },
    ],
    throwOnError: false,
  });
}

function card(hit) {
  const q = questionsById.get(hit.id);
  const s = q.source || {};
  const exam = examsById.get(String(s.exam_id || '').toLowerCase());
  const t = textById.get(q.id);
  const solution = solutionFiles.get(String(s.exam_id || '').toLowerCase());
  const has = f => f && f !== '#';
  const links = [
    exam && has(exam.pdf) ? `<a class="q-link" data-click href="${esc(exam.pdf)}" target="_blank" rel="noopener">Exam PDF ↗</a>` : '',
    exam && has(exam.answer_key) ? `<a class="q-link" data-click href="${esc(exam.answer_key)}" target="_blank" rel="noopener">${exam.answer_key_unofficial ? 'Unofficial key' : 'Answer key'} ↗</a>` : '',
    solution && s.problem ? `<button type="button" class="key-btn" data-solution="${esc(solution)}" data-problem="${esc(s.problem)}" aria-expanded="false">✦ Worked solution</button>` : '',
  ].join('');
  // the transcription is shown as text (escaped) and then typeset by KaTeX auto-render
  const latex = t ? `<div class="as-latex">${esc(t.question_latex)}</div>
      ${t.confident ? '' : '<div class="as-note">Transcription not verified: check it against the image.</div>'}` : '';
  return `
    <article class="q-card" data-id="${esc(q.id)}">
      <div class="q-meta">
        <span class="course-badge ${courseClass(q.course)}">${esc(q.course)}</span>
        <span class="q-chapter">${esc(chapterNames.get(`${q.course}|${q.chapter}`) || q.chapter)}</span>
        <span class="q-source">${esc(s.exam || '')}${s.term ? ', ' + esc(s.term) : ''}${s.problem ? ' · Problem ' + esc(s.problem) : ''}</span>
        <span class="as-score" title="Cosine similarity to your search">${hit.score.toFixed(2)}</span>
      </div>
      <a class="q-figure" data-click href="${esc(q.image)}" target="_blank" rel="noopener">
        <img src="${esc(q.image)}" alt="${esc(q.course)} question ${esc(q.id)}" loading="lazy" decoding="async"/></a>
      ${latex}
      <div class="q-actions">
        ${links}
        <span class="as-feedback" aria-label="Was this result helpful?">
          <button type="button" data-rating="up" aria-label="Helpful">👍</button>
          <button type="button" data-rating="down" aria-label="Not helpful">👎</button>
        </span>
      </div>
      <div class="as-solution" hidden></div>
    </article>`;
}

/** courseClass lives in app.js; fall back to a neutral badge if it isn't there. */
function courseClass(course) {
  return typeof window.courseClass === 'function' ? window.courseClass(course) : 'badge-' + course.replace(/\D/g, '');
}

function render(hits) {
  elResults.innerHTML = hits.length
    ? hits.map(card).join('')
    : `<div class="empty"><div class="empty-icon">🔭</div><h3>No questions found</h3><p>Try another course or wording.</p></div>`;
  renderMath(elResults);
}

async function toggleSolution(btn) {
  const box = btn.closest('.q-card').querySelector('.as-solution');
  if (!box.hidden) { box.hidden = true; btn.setAttribute('aria-expanded', 'false'); return; }
  if (!box.dataset.loaded) {
    box.textContent = 'Loading…';
    box.hidden = false;
    try {
      const sol = await getJSON(`solutions/${btn.dataset.solution}.json`);
      const body = sol[btn.dataset.problem];
      // the solution files use LaTeX text macros; turn the common ones into HTML before KaTeX runs
      box.innerHTML = body
        ? esc(body).replace(/\\textbf\{([^{}]*)\}/g, '<strong>$1</strong>').replace(/\\emph\{([^{}]*)\}/g, '<em>$1</em>').replace(/\n\n/g, '<br/><br/>')
        : 'No worked solution for this problem.';
      renderMath(box);
      box.dataset.loaded = '1';
    } catch (err) {
      box.textContent = 'Could not load the worked solution.';
    }
  }
  box.hidden = false;
  btn.setAttribute('aria-expanded', 'true');
}

elResults.addEventListener('click', e => {
  const cardEl = e.target.closest('.q-card');
  if (!cardEl) return;
  const id = cardEl.dataset.id;
  const rating = e.target.closest('[data-rating]');
  if (rating) {
    cardEl.querySelectorAll('[data-rating]').forEach(b => b.classList.toggle('on', b === rating));
    log('assistant_feedback', { rating: rating.dataset.rating, question_id: id });
    return;
  }
  const sol = e.target.closest('[data-solution]');
  if (sol) { toggleSolution(sol); log('assistant_result_click', { question_id: id }); return; }
  if (e.target.closest('[data-click]')) log('assistant_result_click', { question_id: id });
});

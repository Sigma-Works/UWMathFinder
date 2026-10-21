#!/usr/bin/env node
/**
 * spotcheck.js — measure transcription accuracy by marking a random sample by hand.
 *
 *   node scripts/spotcheck.js build [--seed N]   pick a 10% sample of questions_text.json,
 *                                                spread across courses, and write
 *                                                eval/spotcheck.html
 *   node scripts/serve.js                        then open http://localhost:8000/eval/spotcheck.html
 *                                                and mark each one Correct / Incorrect
 *   node scripts/spotcheck.js report             accuracy from eval/spotcheck.json
 *
 * The page shows each question image next to its rendered LaTeX. Marks are saved to
 * eval/spotcheck.json (serve.js accepts a POST to that path; the page also offers a
 * download if you open it some other way). A person does the marking: the point is an
 * independent check of what the transcriber produced.
 *
 * Sampling: stratified by course. Each course gets round(10% of its transcribed questions),
 * at least 1, so a course with few transcriptions is still checked. Seeded, so the same
 * transcriptions + seed give the same sample. Rebuilding keeps marks for ids still in the sample.
 */
const fs = require('node:fs');
const path = require('node:path');

const root = path.join(__dirname, '..');
const read = f => JSON.parse(fs.readFileSync(path.join(root, f), 'utf8'));
const MARKS = path.join(root, 'eval', 'spotcheck.json');
const PAGE = path.join(root, 'eval', 'spotcheck.html');
const RATE = 0.10;

function rng(seed) {   // mulberry32, same as eval/make-targets.mjs
  return () => {
    seed |= 0; seed = (seed + 0x6D2B79F5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function sample(texts, byId, seed) {
  const rand = rng(seed);
  const groups = {};
  texts.forEach(t => (groups[byId.get(t.id).course] ||= []).push(t.id));
  const picked = [];
  for (const course of Object.keys(groups).sort()) {
    const ids = [...groups[course]].sort();
    for (let i = ids.length - 1; i > 0; i--) { const j = Math.floor(rand() * (i + 1)); [ids[i], ids[j]] = [ids[j], ids[i]]; }
    picked.push(...ids.slice(0, Math.max(1, Math.round(ids.length * RATE))));
  }
  return picked.sort();
}

const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

function page(items, existing) {
  const cards = items.map(({ q, t }) => `
  <section class="item" data-id="${q.id}">
    <h2>${q.id} · ${esc(q.course)} · ${esc((q.source || {}).exam || '')} ${esc((q.source || {}).term || '')}${t.confident ? '' : ' · <em>marked not confident</em>'}</h2>
    <div class="cols">
      <img src="../${esc(q.image)}" alt="question ${q.id}" loading="lazy">
      <div class="tex">${esc(t.question_latex)}</div>
    </div>
    <div class="row">
      <button data-v="correct">✓ Correct</button>
      <button data-v="incorrect">✗ Incorrect</button>
      <input placeholder="note (what's wrong?)" aria-label="note">
    </div>
  </section>`).join('\n');
  return `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Transcription spot-check</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.11/katex.min.css">
<style>
  body { font: 15px/1.5 system-ui, sans-serif; max-width: 1200px; margin: 0 auto; padding: 1rem; background: #fafafa; color: #222; }
  .item { background: #fff; border: 1px solid #ddd; border-radius: 8px; padding: 1rem; margin: 1rem 0; }
  .item.correct { border-color: #2a9d4b; } .item.incorrect { border-color: #d43c3c; }
  h2 { font-size: .95rem; margin: 0 0 .5rem; color: #555; }
  .cols { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; align-items: start; }
  .cols img { width: 100%; border: 1px solid #eee; }
  .tex { overflow-x: auto; }
  .row { display: flex; gap: .5rem; margin-top: .6rem; flex-wrap: wrap; }
  button { padding: .3rem .8rem; cursor: pointer; } input { flex: 1; min-width: 12rem; }
  .item.correct [data-v=correct], .item.incorrect [data-v=incorrect] { font-weight: bold; outline: 2px solid currentColor; }
  #bar { position: sticky; top: 0; background: #fafafa; padding: .5rem 0; border-bottom: 1px solid #ddd; }
  @media (max-width: 700px) { .cols { grid-template-columns: 1fr; } }
</style></head><body>
<div id="bar"><strong>Spot-check:</strong> <span id="count"></span> <button id="dl">Download spotcheck.json</button> <span id="saved"></span></div>
<p>Compare each image with the rendered transcription. Mark <b>Incorrect</b> for any wrong symbol, number or missing part.
Marks save to <code>eval/spotcheck.json</code> when this page is served by <code>node scripts/serve.js</code>.</p>
${cards}
<script src="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.11/katex.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.11/contrib/auto-render.min.js"></script>
<script>
const state = ${JSON.stringify(existing)};
const save = () => {
  document.getElementById('count').textContent = Object.keys(state.marks).length + ' / ' + state.sample.length + ' marked';
  fetch('spotcheck.json', { method: 'POST', body: JSON.stringify(state, null, 1) })
    .then(r => { document.getElementById('saved').textContent = r.ok ? 'saved' : 'not saved (use Download)'; })
    .catch(() => { document.getElementById('saved').textContent = 'not saved (use Download)'; });
};
document.querySelectorAll('.item').forEach(el => {
  const id = el.dataset.id, m = state.marks[id];
  if (m) { el.classList.add(m.correct ? 'correct' : 'incorrect'); el.querySelector('input').value = m.note || ''; }
  el.querySelectorAll('button').forEach(b => b.onclick = () => {
    const correct = b.dataset.v === 'correct';
    state.marks[id] = { correct, note: el.querySelector('input').value, at: new Date().toISOString() };
    el.classList.toggle('correct', correct); el.classList.toggle('incorrect', !correct);
    save();
  });
  el.querySelector('input').onchange = e => { if (state.marks[id]) { state.marks[id].note = e.target.value; save(); } };
});
document.getElementById('dl').onclick = () => {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([JSON.stringify(state, null, 1)], { type: 'application/json' }));
  a.download = 'spotcheck.json'; a.click();
};
document.getElementById('count').textContent = Object.keys(state.marks).length + ' / ' + state.sample.length + ' marked';
renderMathInElement(document.body, { delimiters: [
  { left: '$$', right: '$$', display: true }, { left: '\\\\[', right: '\\\\]', display: true },
  { left: '\\\\(', right: '\\\\)', display: false }, { left: '$', right: '$', display: false } ], throwOnError: false });
</script></body></html>
`;
}

const [cmd, ...rest] = process.argv.slice(2);
const questions = read('questions.json');
const byId = new Map(questions.map(q => [q.id, q]));

if (cmd === 'build') {
  const seedArg = rest.indexOf('--seed');
  const seed = seedArg >= 0 ? Number(rest[seedArg + 1]) : 126;
  const texts = read('questions_text.json');
  const textById = new Map(texts.map(t => [t.id, t]));
  const ids = sample(texts, byId, seed);
  const old = fs.existsSync(MARKS) ? JSON.parse(fs.readFileSync(MARKS, 'utf8')) : { marks: {} };
  const marks = Object.fromEntries(Object.entries(old.marks || {}).filter(([id]) => ids.includes(id)));
  const state = { seed, rate: RATE, transcribed_at_build: texts.length, built: new Date().toISOString(), sample: ids, marks };
  fs.writeFileSync(MARKS, JSON.stringify(state, null, 1) + '\n');
  fs.writeFileSync(PAGE, page(ids.map(id => ({ q: byId.get(id), t: textById.get(id) })), state));
  const per = {};
  ids.forEach(id => { const c = byId.get(id).course; per[c] = (per[c] || 0) + 1; });
  console.log(`sampled ${ids.length} of ${texts.length} transcriptions`, per);
  console.log('serve with `node scripts/serve.js` and open http://localhost:8000/eval/spotcheck.html');
} else if (cmd === 'report') {
  const s = JSON.parse(fs.readFileSync(MARKS, 'utf8'));
  const marked = Object.entries(s.marks);
  if (!marked.length) { console.log(`0 / ${s.sample.length} marked yet: no accuracy to report`); process.exit(0); }
  const ok = marked.filter(([, m]) => m.correct).length;
  console.log(`accuracy ${ok}/${marked.length} = ${(100 * ok / marked.length).toFixed(1)}%  (${marked.length} of ${s.sample.length} sampled questions marked)`);
  const per = {};
  marked.forEach(([id, m]) => { const c = byId.get(id).course; (per[c] ||= [0, 0]); per[c][1]++; if (m.correct) per[c][0]++; });
  Object.entries(per).sort().forEach(([c, [a, n]]) => console.log(`  ${c}: ${a}/${n}`));
  marked.filter(([, m]) => !m.correct).forEach(([id, m]) => console.log(`  incorrect: ${id}${m.note ? ' (' + m.note + ')' : ''}`));
} else {
  console.error('usage: spotcheck.js build [--seed N] | report');
  process.exit(2);
}

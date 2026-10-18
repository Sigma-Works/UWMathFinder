#!/usr/bin/env node
/**
 * syllabus-check.js — detect syllabus changes on the official UW course pages.
 *
 * Each course in syllabus.json has a `source_url` (its course page), and each chapter in
 * chapters.json lists the textbook `sections` it covers. This script fetches every course
 * page, pulls the section numbers out of its outline ("Sec. 3.9", "§6.1-§6.6",
 * "12.1–12.2 — Vectors", …) and compares them with our chapters:
 *
 *   - a chapter whose sections no longer appear       → propose removing it (from this quarter)
 *   - a removed chapter whose sections are back        → propose restoring it
 *   - outline sections that no chapter covers          → flag as a possible new topic
 *   - outline differs from the last snapshot           → list the added/removed sections
 *
 * Usage:
 *   npm run syllabus:check                 # report only (exit 0 = no changes, 2 = changes found)
 *   node scripts/syllabus-check.js --write # also update syllabus.json + syllabus-snapshots/
 *   … --report report.md                   # write the Markdown report (used for the bot's PR)
 *
 * The weekly GitHub Action (.github/workflows/syllabus-watch.yml) runs it with --write and
 * opens a pull request when something changed, so a maintainer only reviews and merges.
 * Proposed changes never reach the live site without that review.
 */
const fs = require('node:fs');
const path = require('node:path');
const Syllabus = require('../assets/js/syllabus.js');

const root = path.join(__dirname, '..');
const SNAP_DIR = path.join(root, 'syllabus-snapshots');

/** Turn an HTML page into plain text lines. */
function htmlToLines(html) {
  return html
    .replace(/<(script|style)[^>]*>[\s\S]*?<\/\1>/gi, ' ')
    .replace(/<br\s*\/?>|<\/(p|li|tr|h\d|div)>/gi, '\n')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&(nbsp|amp|ndash|mdash|sect|plusmn|#\d+);/g, (_, e) => ({ nbsp: ' ', amp: '&', ndash: '–', mdash: '—', sect: '§', plusmn: '±' })[e]
      || (e[0] === '#' ? String.fromCharCode(Number(e.slice(1))) : ' '))
    .split('\n').map(l => l.replace(/\s+/g, ' ').trim()).filter(Boolean);
}

/** Does this line look like part of a course outline (not a GPA, room number, or note size)? */
function isOutlineLine(line) {
  if (/±|gpa|grade|sheet of notes|calculator/i.test(line)) return false;
  // "Sec. 4.9", "§6.1", "Chapter 3", a line starting "12.1", or a weekly row like "3 — 12.5–12.6; 13.1 — Planes"
  return /\bsec(tion)?s?\b\.?|§|chapter|^\(?\s*\d{1,2}\.\d{1,2}\b|[—–]\s*\d{1,2}\.\d{1,2}\b|;\s*\d{1,2}\.\d{1,2}\b/i.test(line);
}

const bySection = (x, y) => {
  const [a1, a2] = x.split('.').map(Number), [b1, b2] = y.split('.').map(Number);
  return a1 - b1 || a2 - b2;
};

/**
 * Section numbers mentioned in outline text, with ranges expanded:
 * "3.3-3.8" → 3.3 … 3.8, "§6.1-§6.6" → 6.1 … 6.6, "12.1–12.2" → 12.1, 12.2.
 * Returns a sorted array of strings like "3.9".
 */
function parseSections(text) {
  const found = new Set();
  for (const line of String(text).split('\n')) {
    if (!isOutlineLine(line)) continue;
    const re = /§?\s*(\d{1,2})\.(\d{1,2})(?:\s*[-–]\s*§?\s*(?:(\d{1,2})\.)?(\d{1,2}))?/g;
    let m;
    while ((m = re.exec(line))) {
      const ch = Number(m[1]), a = Number(m[2]);
      if (ch > 20 || a > 15) continue;                       // not a textbook section
      const endCh = m[3] ? Number(m[3]) : ch, b = m[4] ? Number(m[4]) : a;
      if (m[4] && endCh === ch && b >= a && b - a <= 12) {
        for (let s = a; s <= b; s++) found.add(`${ch}.${s}`);
      } else {
        found.add(`${ch}.${a}`);
        if (m[4] && endCh !== ch) found.add(`${endCh}.${b}`);
      }
    }
  }
  return [...found].sort(bySection);
}

/**
 * Compare a course's outline sections with its chapters.
 * @returns {{remove: string[], restore: string[], uncovered: string[]}}
 */
function compare(chapters, removedIds, sections) {
  const have = new Set(sections), covered = new Set(), remove = [], restore = [];
  for (const ch of chapters) {
    if (!Array.isArray(ch.sections) || !ch.sections.length) continue;   // chapters without sections aren't tracked
    ch.sections.forEach(s => covered.add(s));
    const present = ch.sections.some(s => have.has(s));
    if (!present && !removedIds.has(ch.id)) remove.push(ch.id);
    if (present && removedIds.has(ch.id)) restore.push(ch.id);
  }
  return { remove, restore, uncovered: sections.filter(s => !covered.has(s)) };
}

async function main() {
  const args = process.argv.slice(2);
  const write = args.includes('--write');
  const reportPath = args.includes('--report') ? args[args.indexOf('--report') + 1] : null;
  const chapters = JSON.parse(fs.readFileSync(path.join(root, 'chapters.json'), 'utf8')).courses;
  const syllabus = JSON.parse(fs.readFileSync(path.join(root, 'syllabus.json'), 'utf8'));
  const term = Syllabus.currentTerm();
  const lines = [`# Syllabus check — ${term}`, ''];
  let changed = false;

  for (const [course, conf] of Object.entries(syllabus.courses)) {
    if (!conf.source_url || !chapters[course]) continue;
    const slug = course.toLowerCase().replace(/\s+/g, '-');
    let sections;
    try {
      const res = await fetch(conf.source_url, { headers: { 'User-Agent': 'UWMathFinder syllabus-check (github.com/Sigma-Works/UWMathFinder)' } });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      sections = parseSections(htmlToLines(await res.text()).join('\n'));
    } catch (err) {
      lines.push(`## ${course}`, `⚠ Could not read ${conf.source_url} (${err.message}). Check it by hand.`, '');
      continue;
    }
    if (sections.length < 3) {                                // page redesigned or outline moved: don't guess
      lines.push(`## ${course}`, `⚠ Found only ${sections.length} section numbers on ${conf.source_url}; the outline may have moved. Check it by hand.`, '');
      continue;
    }
    const removed = new Set(Syllabus.removedChapters(syllabus, course, '', term).keys());
    const { remove, restore, uncovered } = compare(chapters[course].chapters, removed, sections);
    const snapFile = path.join(SNAP_DIR, `${slug}.json`);
    const before = fs.existsSync(snapFile) ? JSON.parse(fs.readFileSync(snapFile, 'utf8')).sections : null;
    const added = before ? sections.filter(s => !before.includes(s)) : [];
    const dropped = before ? before.filter(s => !sections.includes(s)) : [];
    const name = id => (chapters[course].chapters.find(c => c.id === id) || {}).name || id;

    const notes = [];
    if (remove.length) notes.push(`- **No longer in the outline:** ${remove.map(name).join(', ')} → proposing \`remove\` from ${term}`);
    if (restore.length) notes.push(`- **Back in the outline:** ${restore.map(name).join(', ')} → proposing \`restore\` from ${term}`);
    if (uncovered.length) notes.push(`- **Sections no chapter covers:** ${uncovered.join(', ')}. Add them to a chapter's \`sections\` in chapters.json, or add a new chapter if it's a new topic.`);
    if (added.length || dropped.length) notes.push(`- Outline changed since the last snapshot: ${[...added.map(s => '+' + s), ...dropped.map(s => '−' + s)].join(', ')}`);
    lines.push(`## ${course}`, `Source: ${conf.source_url}`, ...(notes.length ? notes : ['- No changes.']), '');

    // a missing snapshot alone isn't a change; it's just recorded
    if (remove.length || restore.length || added.length || dropped.length) changed = true;
    if (write) {
      if (remove.length || restore.length) {
        conf.changes = conf.changes || [];
        conf.changes.push({ from: term, ...(remove.length && { remove }), ...(restore.length && { restore }),
          note: `Auto-detected by syllabus-check on ${new Date().toISOString().slice(0, 10)} from ${conf.source_url}. Review before merging.` });
      }
      fs.mkdirSync(SNAP_DIR, { recursive: true });
      fs.writeFileSync(snapFile, JSON.stringify({ course, source_url: conf.source_url, sections }, null, 2) + '\n');
    }
  }
  if (write) fs.writeFileSync(path.join(root, 'syllabus.json'), JSON.stringify(syllabus, null, 2) + '\n');
  const report = lines.join('\n');
  if (reportPath) fs.writeFileSync(reportPath, report + '\n');
  console.log(report);
  process.exitCode = changed ? 2 : 0;
}

module.exports = { parseSections, compare, isOutlineLine, htmlToLines };
if (require.main === module) main().catch(err => { console.error(err); process.exit(1); });

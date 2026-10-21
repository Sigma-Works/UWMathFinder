/**
 * latex-check.js — does a piece of "prose with $math$" render with KaTeX?
 *
 * Splits the string on the same delimiters the browser uses (KaTeX auto-render:
 * $$..$$, \[..\], \(..\), $..$) and runs katex.renderToString on every math
 * segment with throwOnError, so anything that would show as a red error on the
 * site fails here instead. Returns a list of error messages (empty = OK).
 */
const katex = require('katex');

const DELIMS = [
  { left: '$$', right: '$$', display: true },
  { left: '\\[', right: '\\]', display: true },
  { left: '\\(', right: '\\)', display: false },
  { left: '$', right: '$', display: false },
];

/** Split text into [{math, display}] segments; an unclosed delimiter is an error. */
function mathSegments(s) {
  const out = [];
  let i = 0;
  while (i < s.length) {
    if (s[i] === '\\' && s[i + 1] === '$') { i += 2; continue; }   // escaped dollar in prose
    const d = DELIMS.find(d => s.startsWith(d.left, i));
    if (!d) { i++; continue; }
    let j = i + d.left.length;
    let end = -1;
    while (j < s.length) {
      if (s[j] === '\\' && d.right === '$' && s[j + 1] === '$') { j += 2; continue; }
      if (s.startsWith(d.right, j)) { end = j; break; }
      j++;
    }
    if (end < 0) { out.push({ error: `unclosed ${d.left} at ${i}` }); break; }
    out.push({ math: s.slice(i + d.left.length, end), display: d.display });
    i = end + d.right.length;
  }
  return out;
}

function checkLatex(s) {
  const errs = [];
  for (const seg of mathSegments(s)) {
    if (seg.error) { errs.push(seg.error); continue; }
    try {
      katex.renderToString(seg.math, { throwOnError: true, displayMode: seg.display });
    } catch (e) {
      errs.push(`${e.message.split('\n')[0]} in "${seg.math.slice(0, 60)}"`);
    }
  }
  return errs;
}

module.exports = { checkLatex, mathSegments };

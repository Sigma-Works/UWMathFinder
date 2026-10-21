/**
 * assistant-text.mjs — the text that represents one question to the embedding model.
 *
 * Shared by the index build (scripts/build-index.mjs) and the retrieval eval
 * (eval/retrieval.mjs) so both embed documents the same way. The browser never
 * calls this: it only embeds the student's query, and compares it with vectors
 * that were built from this text.
 */

export const MODEL = 'Xenova/all-MiniLM-L6-v2';
export const DTYPE = 'q8';   // must match assets/js/assistant.js

/** Rough LaTeX → words, so "\dfrac{dy}{dx}" doesn't eat tokens as backslash soup. */
export function latexToPlain(s) {
  return String(s || '')
    .replace(/\\(?:left|right|displaystyle|,|;|!|quad|qquad)/g, ' ')
    .replace(/\\[dt]?frac\{([^{}]*)\}\{([^{}]*)\}/g, '($1)/($2)')
    .replace(/\\(?:text|mathrm|textbf|mathcal|operatorname)\{([^{}]*)\}/g, '$1')
    .replace(/\\([a-zA-Z]+)/g, ' $1 ')        // \sin → sin, \int → int, \lim → lim
    .replace(/[$\\{}]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

/**
 * Metadata first, then the transcribed question (if any). The model truncates long
 * inputs, so the most reliable signal (course, chapter, skills) goes at the front.
 */
export function docText(q, chapterName, text) {
  const s = q.source || {};
  const parts = [
    q.course,
    chapterName,
    (q.skills || []).join(', '),
    [s.exam, s.term].filter(Boolean).join(' '),
  ];
  if (text && text.question_latex) parts.push(latexToPlain(text.question_latex));
  return parts.filter(Boolean).join('. ');
}

/** Map "Math 126|taylor_series" → "Taylor Series" from chapters.json. */
export function chapterNames(chapters) {
  const m = new Map();
  for (const [course, conf] of Object.entries(chapters.courses)) {
    for (const ch of conf.chapters) m.set(`${course}|${ch.id}`, ch.name);
  }
  return m;
}

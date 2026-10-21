# Study assistant: how it works

The study assistant answers "find past UW exam questions similar to this", entirely in the
student's browser. This document walks through the pieces in the order data flows through
them, and explains each idea the first time it shows up. Measured numbers live in
[DECISIONS.md](DECISIONS.md) and [eval/baseline.json](eval/baseline.json), next to the
command that produced them.

```
 questions/*.png ──(read by hand)──► questions_text.json ─┐
 questions.json, chapters.json ───────────────────────────┤
                                                           ▼
                                      scripts/build-index.mjs   (Node, at build time)
                                      embed every question with MiniLM, quantize to int8
                                                           │
                                                           ▼
                                      assets/assistant/index.bin + index.json  (static files)
                                                           │
 student types a query ──► assets/js/assistant.mjs ◄───────┘    (browser, at query time)
                           embed query with the same MiniLM, cosine-rank all rows,
                           show top 5 cards (image, KaTeX, PDF, key, worked solution)

 eval/retrieval_queries.json ──► eval/retrieval.mjs ──► recall@5, MRR ──► CI gate
```

---

## 1. Turning images into text: `questions_text.json`

Every question on the site is a PNG cropped from an exam PDF. Images are great for students
but useless for search, because a computer can't tell what a picture says. So the first step is
**transcription**: writing down each question as text with LaTeX for the math, e.g.
`Find $\lim_{x\to 0^+} x^x$`.

- `scripts/transcribe.js` keeps the work queue in `scripts/transcribe_progress.json`: Zahid's
  questions first (found with `git log --author="Zahid-M" --diff-filter=A`), then the rest, in id
  order. `node scripts/transcribe.js status` shows where we are; `next 50` lists the next batch;
  `merge <file>` adds a finished batch.
- Each entry has `question_latex`, `answer_latex`, `final_answer` and `confident`. `confident:
  false` means "the image was unclear, check me".
- `scripts/latex-check.js` (`checkLatex()`) splits the text on `$…$`, `$$…$$`, `\(…\)` and `\[…\]`
  (the same delimiters the browser uses) and runs every piece through KaTeX with `throwOnError`.
  A formula that wouldn't render on the site fails the merge and fails CI.
- `scripts/spotcheck.js` measures accuracy: a random 10% sample, spread across courses, shown as
  image-next-to-rendered-LaTeX for a human to mark right or wrong.

Questions that aren't transcribed yet are still in the index, represented by their metadata
(course, chapter, skills, exam), so search covers all 2,099 questions from day one and gets
sharper as transcription continues.

## 2. Embeddings: `scripts/assistant-text.mjs`, `scripts/build-index.mjs`

**What is an embedding?** A neural network (here *all-MiniLM-L6-v2*) reads a piece of text and
outputs a list of 384 numbers, a *vector*. The network was trained so that texts with similar
meaning get vectors that point in similar directions: "ladder sliding down a wall" and "a ladder
leans against a wall, how fast is the angle changing" end up close together, even though they
share few words. That's the advantage over keyword search, which only matches exact words.

`docText()` decides what text represents a question: course, chapter name, skills, exam and term,
then the transcription with LaTeX turned into words by `latexToPlain()` (`\dfrac{a}{b}` becomes
`(a)/(b)`). Metadata goes first because MiniLM only reads the first couple of hundred tokens.

`build-index.mjs` runs the model over all 2,099 questions in batches (`embedAll()`), using
transformers.js in Node, the *same library and model file* the browser uses.

**Normalization.** The vectors are scaled to length 1 ("L2-normalized", `normalize: true`). After
that, comparing two vectors only depends on the angle between them, not their length.

## 3. Quantization: `quantize()` in `build-index.mjs`

Each of the 384 numbers is a 32-bit float (4 bytes). **Quantization** stores each one in fewer
bits. Because the vectors have length 1, every component is between -1 and 1, so we store
`round(x * 127)` as a signed byte (-127…127). That's 4x smaller (806,016 bytes instead of about
3.2 MB for 2,099 questions) and loses very little: the eval reports recall for both the int8
index and the float vectors, so the cost is measured, not guessed.

## 4. Searching: `assets/js/assistant-rank.mjs`

**Cosine similarity** measures how similar two vectors' directions are:
`cos(a, b) = (a · b) / (|a| |b|)`, where `a · b` is the dot product (multiply matching
components and add them up). It's 1 for identical direction, 0 for unrelated. Since everything
is already length 1, cosine is just the dot product. With int8 rows it's `(query · row) / 127`.

`topK()` computes that for every row (a "brute-force" scan: 2,099 × 384 multiply-adds, a few
milliseconds), sorts, and returns the best k. `courseFilter()` optionally keeps only one course
(including questions cross-listed into it via `also_in`). A fancier approximate index (HNSW,
FAISS) only pays off with hundreds of thousands of rows.

This file has no DOM code and no model, so the browser *and* the eval import it. CI therefore
tests the exact ranking students get.

## 5. The browser side: `assets/js/assistant.mjs`

**Feature flag.** The last two lines of `assets/js/app.js` do
`if (?assistant=1) import('./assistant.mjs')`. Without the flag nothing about the page changes.

**Lazy loading** means "don't download something until it's needed". Opening the page with the
flag only fetches `assistant.mjs` and `assistant-rank.mjs` (a few KB) and adds the "Ask (beta)"
tab. Only when the student clicks the tab does `loadResources()` start, in parallel:

- transformers.js from the jsDelivr CDN (`import(TRANSFORMERS_URL)`), which then downloads the
  ONNX model and tokenizer from the Hugging Face CDN, reporting progress through
  `progress_callback` (that's the progress bar);
- `index.bin` + `index.json`, `questions_text.json`, and the question/exam/chapter data;
- KaTeX (CSS, JS and the auto-render extension) from cdnjs.

transformers.js stores the model in the browser's Cache Storage, and the browser's HTTP cache keeps
the rest, so the second visit doesn't download them again.

`search()` embeds the query (`embed()`: same model, same `dtype: 'q8'`, mean pooling, normalized),
calls `topK()`, and `render()` builds cards. Each card shows the question image, the
transcription typeset by KaTeX's `renderMathInElement`, links to the exam PDF and answer key
(looked up in `exams.json` case-insensitively, because some ids differ in case), and a "Worked
solution" button when `solutions/<exam>.json` exists; `toggleSolution()` fetches it on demand.

The tab doesn't modify `showView()` in app.js: `openTab()` hides the other panels itself, and a
click on any other tab hides ours.

## 6. Analytics

Through the page's existing `track()` (a GA4 `gtag('event', …)` wrapper defined in `index.html`):
`assistant_open`, `assistant_search {course}`, `assistant_result_click {question_id}` and
`assistant_feedback {rating, question_id}` from the 👍/👎 buttons. The query text is never sent.

## 7. Measuring quality: `eval/`

You can't improve what you don't measure, so there's a fixed test set:

- `eval/make-targets.mjs` picks 150 target questions with a seeded random sample stratified by
  course (every course at least 12). Random, so we didn't pick easy ones.
- `eval/retrieval_queries.json`: one query per target, written the way a student might type it,
  with `gold` = the target plus any near-duplicates (the same problem reused with new numbers).
  All are `"source": "llm"` and should be reviewed and replaced by real student queries.

**recall@5**: the share of queries where at least one gold question appears in the top 5. It
answers "does the right question show up on the first screen?"

**MRR (mean reciprocal rank)**: for each query take 1/rank of the first gold result (1 if it's
first, 1/2 if second, …, 0 if never found) and average. It rewards putting the answer at the very
top, which recall@5 doesn't distinguish.

`eval/retrieval.mjs` measures three systems on the same queries: the shipped assistant, the same
documents without quantization, and the site's existing keyword search (a word-overlap variant is
reported too, for context only).

## 8. CI gating: `.github/workflows/assistant.yml`

**CI (continuous integration)** runs checks automatically on every pull request. **Gating** means
a failing check marks the PR red, so a change that makes things worse is caught before merging.
This workflow runs `scripts/validate-assistant.mjs` (the transcriptions render, the index matches
`questions.json` and was rebuilt after the last transcription) and then
`node eval/retrieval.mjs --check`, which fails if recall@5 is more than 2 points (0.02) below
`eval/baseline.json`. The 2-point margin allows small, harmless changes, but catches a real
regression. When a change is meant to improve or trade off recall, rerun with
`--write-baseline` and commit the new baseline in the same PR, so the reviewer sees the number
move.

## File map

| File | Role |
| --- | --- |
| `questions_text.json` | transcriptions (LaTeX) |
| `scripts/transcribe.js`, `scripts/transcribe_progress.json` | resumable transcription queue |
| `scripts/latex-check.js` | does it render in KaTeX? |
| `scripts/spotcheck.js`, `eval/spotcheck.*` | human accuracy check |
| `scripts/assistant-text.mjs` | model name and document text, shared by build + eval |
| `scripts/build-index.mjs` | embeddings → `assets/assistant/index.*` |
| `assets/js/assistant-rank.mjs` | cosine top-k (browser + eval) |
| `assets/js/assistant.mjs` | tab, lazy loading, search UI, analytics |
| `eval/retrieval.mjs`, `eval/retrieval_queries.json`, `eval/baseline.json` | eval + baseline |
| `scripts/validate-assistant.mjs`, `.github/workflows/assistant.yml` | CI |
| `scripts/serve.js` | local static server (also saves spot-check marks) |

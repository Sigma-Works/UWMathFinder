# Study assistant: learning plan

Seven one-hour sessions, most important first. Each has files to read, something to run, and
questions you should be able to answer at the end. Start with ARCHITECTURE.md for the overview.

Setup once: `npm ci`, then `node scripts/serve.js` and open http://localhost:8000/?assistant=1.

---

## Session 1: The search itself (ranking)

- Read `assets/js/assistant-rank.mjs` (all of it, about 60 lines) and ARCHITECTURE.md §4.
- Run: in `node`, make two random unit vectors and compute their dot product by hand; then quantize
  them with `x => Math.round(x * 127)` and compare.
- You should be able to answer:
  1. Why does `topK()` divide by 127, and would ranking change if it didn't?
  2. What does `courseFilter()` do with `also_in`?
  3. What is the time complexity of a search, and when would you need an ANN index?

## Session 2: Embeddings and the index build

- Read `scripts/assistant-text.mjs` and `scripts/build-index.mjs`; ARCHITECTURE.md §2–3.
- Run `npm run build:index` and look at the output sizes; open `assets/assistant/index.json`.
- Answer:
  1. What does `docText()` produce for q0001? (Print it.)
  2. Why is metadata placed before the transcription?
  3. Why does `index.bin` have the same size with 50 or 200 transcriptions?
  4. What would break if the browser used `dtype: 'fp32'`?

## Session 3: The browser module and lazy loading

- Read `assets/js/assistant.mjs` top to bottom, and the last lines of `assets/js/app.js`.
- Run the site with and without `?assistant=1`; watch the Network tab before and after opening the tab.
- Answer:
  1. List everything `loadResources()` downloads and from where.
  2. Why is the module loaded with `import()` instead of a `<script>` tag?
  3. How does the progress bar get its numbers?
  4. Why are exam ids looked up lowercased?

## Session 4: Measuring retrieval

- Read `eval/retrieval.mjs`, `eval/make-targets.mjs`, a few entries of `eval/retrieval_queries.json`;
  DECISIONS.md §6–7.
- Run `npm run eval:retrieval`. Then add a query of your own and rerun.
- Answer:
  1. Compute recall@5 and MRR by hand for 3 queries with ranks 1, 4, none.
  2. Why does the keyword baseline return nothing for most queries?
  3. Name two ways the current numbers are biased.

## Session 5: CI gating

- Read `.github/workflows/assistant.yml`, `scripts/validate-assistant.mjs`; DECISIONS.md §8.
- Run: break `topK()` (reverse the sort), run `node eval/retrieval.mjs --check`, see it fail, revert.
- Answer:
  1. What does the gate protect against that unit tests wouldn't?
  2. When is it correct to rewrite `eval/baseline.json`, and in which PR?
  3. Why cache the Hugging Face model in CI?

## Session 6: Transcription pipeline and quality

- Read `scripts/transcribe.js`, `scripts/latex-check.js`, `scripts/spotcheck.js`.
- Run `npm run transcribe -- status`; build the spot-check (`node scripts/spotcheck.js build`), mark
  the sample in the browser, then `node scripts/spotcheck.js report`.
- Answer:
  1. How does a later session resume transcription?
  2. What does `mathSegments()` do with an escaped `\$`?
  3. Why does passing the KaTeX check not mean the transcription is correct?

## Session 7: Product decisions and next steps

- Read DECISIONS.md end to end and INTERVIEW.md; skim GA4 events in `assistant.mjs`.
- Answer:
  1. Argue for and against moving to a server-side embedding API.
  2. Which single change would raise recall the most, according to the measurements?
  3. What needs to happen before removing the `?assistant=1` flag?
  4. Answer five INTERVIEW.md questions out loud without looking.

# Study assistant: interview questions

Twenty questions an interviewer could ask about this project, with answers that point at the code.
Numbers are the measured ones from `DECISIONS.md` / `eval/baseline.json`.

---

**1. Walk me through what happens when a student searches "related rates ladder".**
`search()` in `assets/js/assistant.mjs` embeds the query with MiniLM (`embed()`), which returns a
384-number vector of length 1. `topK()` in `assets/js/assistant-rank.mjs` takes the dot product of
that vector with each of the 2,099 int8 rows in `index.bin`, sorts, and returns the best 5.
`render()` builds the cards and KaTeX typesets the transcriptions.

**2. Why run the model in the browser instead of on a server?**
Constraints: static GitHub Pages site, no servers, no API keys, no paid services. In-browser
inference only needs static files. Tradeoffs: a ~24 MB first download and a small model.
Bonus: queries never leave the device. (`DECISIONS.md` §1.)

**3. What is an embedding, and why is it better than keyword search here?**
A vector that places texts with similar meaning close together. "Ladder sliding down a wall" and
"related rates" share no words, so keyword search misses that match but embeddings don't. Measured: the site's keyword
box returns nothing for 150/150 natural-language queries (recall@5 0); the assistant gets 0.233.

**4. Why cosine similarity, and why is it just a dot product in your code?**
Cosine measures the angle between vectors, ignoring length. Both sides are L2-normalized
(`normalize: true` in `embedAll()` / `embed()`), so |a| = |b| = 1 and cos = a · b. See the comment
on `topK()`.

**5. How did you shrink the index?**
`quantize()` in `scripts/build-index.mjs`: each normalized component is in [-1, 1], stored as
`round(x * 127)` in one signed byte. 806,016 bytes instead of ~3.2 MB float32. `eval/retrieval.mjs`
measures both: recall@5 0.233 for int8 and float alike.

**6. Why brute-force search instead of an ANN index like HNSW?**
2,099 × 384 = ~806K multiply-adds, which takes a few milliseconds in JS. An ANN index adds code and
approximation error and only pays off at hundreds of thousands of vectors.

**7. Why must the query and documents use the same model? What breaks if they don't?**
An embedding's coordinates only mean something relative to the model that produced it; two models
produce unrelated spaces, so similarities become noise. Even dtype matters, so `MODEL` and `DTYPE` are
pinned in both `scripts/assistant-text.mjs` and `assets/js/assistant.mjs`.

**8. What text do you embed for each question, and why that order?**
`docText()` in `scripts/assistant-text.mjs`: course, chapter name, skills, exam/term, then the
transcription run through `latexToPlain()`. Metadata comes first because MiniLM truncates long inputs.

**9. How do you keep the main page fast?**
The assistant module loads only with `?assistant=1` (last lines of `app.js`), and the heavy
resources load only when the tab opens (`loadResources()`). Lighthouse interleaved runs: `main` and
the branch both 41; the flag adds 17,904 bytes (`eval/lighthouse.md`).

**10. How did you measure retrieval quality?**
`eval/retrieval.mjs`: 150 queries, gold = target + near-duplicates. `score()` computes recall@5
(share of queries with a gold hit in the top 5) and MRR (mean of 1/rank of the first hit).

**11. What's wrong with your eval set?**
The queries are LLM-written by the same model that wrote the transcriptions, so phrasing can leak
(10/11 for transcribed targets is inflated). Only 11 targets are transcribed so far, and
near-duplicates are under-marked. Every query is tagged `"source": "llm"` so real queries can
replace them. (`DECISIONS.md` §7.)

**12. How did you choose eval targets without biasing toward easy ones?**
`eval/make-targets.mjs`: a seeded (mulberry32) stratified random sample, at least 12 per course,
the rest proportional to course size. Reproducible and not hand-picked.

**13. Why compare against the existing keyword search, which obviously scores 0?**
Because it's what students actually have, so it's the honest "before". To avoid only beating a
straw man, `keywordWordsRanking()` adds a word-overlap ranker (0.167), which the assistant still beats.

**14. How does CI stop a regression?**
`.github/workflows/assistant.yml` runs `scripts/validate-assistant.mjs` then
`node eval/retrieval.mjs --check`, which exits 1 if recall@5 < baseline − 0.02. Shown: reversing
the sort in `topK()` → recall@5 0 → FAIL.

**15. Why 2 points?**
One query is 0.67 points, so 2 points means about three queries can flip without failing. Enough to
absorb tie-order noise, tight enough to catch real breakage. Intentional changes rewrite the
baseline in the same PR.

**16. How do you know the eval tests the same ranking students get?**
The eval imports `topK()` from `assets/js/assistant-rank.mjs`, the exact module the browser
imports, and scores the committed `index.bin`, not a re-embedded copy.

**17. How did you produce text from images without an OCR API?**
Hand transcription (by Claude reading the PNGs) with tooling: `scripts/transcribe.js` keeps a
resumable queue, `merge` validates every entry, and `checkLatex()` in `scripts/latex-check.js`
renders each math segment with KaTeX `throwOnError`.

**18. How do you know the transcriptions are right?**
I don't yet. `scripts/spotcheck.js` samples 10% per course (`sample()`), shows image next to
rendered LaTeX, and saves human marks to `eval/spotcheck.json`; `report` prints accuracy. KaTeX
only proves it renders, not that it's correct.

**19. What would you do next to improve recall?**
(a) Keep transcribing: transcribed targets hit 10/11 vs 25/139. (b) Try `bge-small-en-v1.5` and let CI
show the difference. (c) Hybrid ranking: add BM25 on transcriptions and fuse with embeddings.
(d) Replace LLM queries with real student queries.

**20. What privacy considerations did you make?**
Queries are embedded on-device and never sent anywhere. GA4 gets `assistant_search {course}`, not
the text (`search()`), plus result clicks and 👍/👎 with question ids.

# Study assistant: design decisions

Each entry: what we chose, what else we could have done, why, and what it costs us.
Numbers in here come from commands that were actually run; the command is next to the number.

---

## 1. Everything runs in the browser (no server)

**Chosen:** the student's query is embedded in their own browser with transformers.js, and
compared against a precomputed index file served by GitHub Pages like any other static file.

**Alternatives:**
- A small API (e.g. a serverless function) that embeds the query, or calls a hosted embedding API.
- A hosted vector database (Pinecone, etc.).

**Why:** the site is a static GitHub Pages site and the hard constraints are no servers, no API
keys and no paid services. In-browser inference meets all three: the only things fetched are
static files (the model from the Hugging Face CDN, our index from GitHub Pages).

**Tradeoffs:**
- The first time a student opens the assistant they download about 24 MB of model plus the
  index (see §3 and §4). After that the browser cache makes it instant, but the first open is
  slow on a phone or a bad connection. A server would make the first query fast.
- We can only use a *small* model, because it has to download and run on a laptop or phone.
  A larger hosted model would probably retrieve better.
- Nothing about a student's query ever leaves their browser, which is a privacy win
  (apart from the GA4 event, which records the course filter, never the query text; see §9).

## 2. The transcriptions were made by reading the images, not by an API

**Chosen:** `questions_text.json` is written by hand (by Claude reading each PNG in a coding
session), in batches of 50, tracked by `scripts/transcribe_progress.json`.

**Alternatives:** an OCR service (Mathpix), a vision LLM API, Tesseract.

**Why:** no API keys / paid services. Tesseract can't read math.

**Tradeoffs:** slow (it takes a session per few hundred questions), and an LLM reading images
can misread a symbol. That's why every entry has `confident`, every formula is checked by
KaTeX (`scripts/latex-check.js`), and `scripts/spotcheck.js` lets a human measure accuracy
on a random sample.

**Spot-check (measured, `node scripts/spotcheck.js report`, 200 transcriptions, seed 126):**
21/21 = 100.0% marked correct by a human (Math 120 1/1, 124 8/8, 125 6/6, 126 6/6). With 21
samples this does not prove the error rate is zero; it means it is probably below about 13%
(the exact 95% upper bound when 0 of 21 are wrong: `1 - 0.05^(1/21)` = 0.133). Questions without text are still searchable through their metadata
(course, chapter, skills), just less precisely.

Answer keys sometimes contain mistakes (e.g. q0002's key differentiates $x^2\sin x$ although the
question says $x^2\cos x$). The transcription keeps what the key says and adds a note in
parentheses; it does not silently "fix" the key.

## 3. Embedding model: `Xenova/all-MiniLM-L6-v2`, quantized (q8)

**Chosen:** all-MiniLM-L6-v2, the ONNX export by Xenova, 8-bit quantized weights, 384-dim
output, mean pooling + L2 normalization. The same model *and* the same `dtype` (`q8`) are used
at build time (Node) and query time (browser): `MODEL` / `DTYPE` in
`scripts/assistant-text.mjs` and `assets/js/assistant.js`.

**Alternatives:**
- `bge-small-en-v1.5` / `gte-small` (same 384 dims, often better on retrieval benchmarks,
  about 1.5x the download).
- A bigger model (`bge-base`, 768 dims): around 4x the download and 2x the index size.
- No neural model at all: BM25 / TF-IDF keyword ranking (tiny, but doesn't know that
  "ladder sliding down a wall" and "related rates" are related).

**Why:** it is the default sentence-embedding model for transformers.js, it is small, and it is
fast on a laptop. If the eval (§7) shows retrieval is the bottleneck, swapping in bge-small is a
one-line change plus a rebuild, and CI will show whether recall went up.

**Size (measured):** files transformers.js downloaded into
`node_modules/@huggingface/transformers/.cache/Xenova/all-MiniLM-L6-v2/`:

```
22972370  onnx/model_quantized.onnx
  711661  tokenizer.json
     650  config.json
     366  tokenizer_config.json
```

Total **23,685,047 bytes (about 23.7 MB)**, plus the transformers.js library and its ONNX
Runtime WASM file (measured in §5).

**Why the query and the documents must use the same model:** an embedding is a list of numbers
whose meaning is only defined by the model that produced it. Two different models put "integration
by parts" in unrelated places, so comparing their vectors is meaningless. Even the same model at
different precision (fp32 vs q8) gives slightly different vectors, which is why `dtype` is pinned too.

## 4. Index: int8 vectors in a binary file + JSON manifest

**Chosen:** `assets/assistant/index.bin` holds one row of 384 signed bytes per question (row
order = `ids` in `assets/assistant/index.json`). Vectors are L2-normalized first, so every
component is in [-1, 1], then stored as `round(x * 127)`.

**Size (measured with `npm run build:index` at 50 transcribed questions):**

```
index.bin   806,016 bytes  (2,099 x 384; 454,054 bytes gzipped)
index.json   17,943 bytes  (4,735 bytes gzipped)
```

**Alternatives:**
- float32 rows: 4x bigger (3.2 MB).
- JSON array of numbers: bigger still, and slow to parse.
- Binary (1-bit) quantization: 48 bytes per row (100 KB total) but noticeably worse ranking.
- Product quantization / an ANN index (HNSW): only worth it at hundreds of thousands of rows.
  With 2,099 rows, a brute-force scan is 806 K multiply-adds, under a few milliseconds.

**Tradeoff:** int8 loses a little precision. `eval/retrieval.mjs` reports recall for both the
int8 index and the unquantized float vectors so this is measured, not assumed (see §7).

**What goes into each document** (`docText()` in `scripts/assistant-text.mjs`): course, chapter
name, skills, exam and term, then the transcribed question with LaTeX turned into words. Metadata
comes first because MiniLM truncates long inputs.

**Update (200 transcriptions):** `npm run build:index` again printed `index.bin 806016 bytes`,
`index.json 17944 bytes`. The size depends only on the number of questions, not on how many are
transcribed.

## 5. Lazy loading behind a URL flag

**Chosen:** two lines at the end of `assets/js/app.js` import `assets/js/assistant.mjs` only when
the URL has `?assistant=1`. That module adds the tab and does nothing heavy until the tab is opened;
then `loadResources()` fetches transformers.js (jsDelivr), the model (Hugging Face CDN), the index,
the transcriptions and KaTeX (cdnjs) in parallel.

**Alternatives:** a separate page (`/assistant.html`); loading the model on page load "to be fast".

**Why:** the hard requirement was that the main page's weight and Lighthouse score do not get
worse. Measured in `eval/lighthouse.md`: with no flag, the branch and `main` both score 41 with the
same bytes (interleaved runs); with the flag, +17,904 bytes before the tab is opened.

**Tradeoff:** the first search waits for the model download. There is a progress bar driven by
transformers.js's `progress_callback`.

## 6. Keyword baseline = the site's real search box, reproduced exactly

The existing Search Questions box (`filterQuestions()` in `app.js`) keeps questions whose metadata
contains the **whole query as one substring**, in file order. For natural-language queries this
returns nothing, so its recall@5 is 0. That's the honest baseline because it's what students have
today. `eval/retrieval.mjs` also reports a fairer word-overlap ranking over the same metadata
(not on the site) so the comparison doesn't only beat a straw man.

## 7. Retrieval eval: 150 LLM-drafted queries, stratified random targets

**Measured** (`node eval/retrieval.mjs --write-baseline`, 200 transcriptions):

```
assistant (int8)   recall@5 0.233  MRR 0.168
assistant (float)  recall@5 0.233  MRR 0.164
keyword baseline   recall@5 0      MRR 0      (0/150 queries return anything)
keyword words (not on site) recall@5 0.167  MRR 0.11
by course: 120 0.25 · 124 0.25 · 125 0.179 · 126 0.156 · 207 0.067 · 208 0.25 · 224 0.75
targets with a transcription: 10/11 in top 5; without: 25/139
```

**Known biases. Read before trusting these numbers:**
- The queries were written by the same model that wrote the transcriptions, after looking at the
  same image. For transcribed targets, the query and the document can share phrasing, which
  inflates the 10/11. Real student queries will do worse. Replace `"source": "llm"` queries with
  real ones (e.g. from GA4 or a survey) and rerun.
- Targets were drawn at random, so only 11 of 150 happen to be transcribed so far. The overall
  number will move as transcription continues; that's expected, and CI's baseline should be
  rewritten in the PR that adds transcriptions.
- Near-duplicates (the same problem reused with new numbers) were only marked where I noticed them
  (4 gold sets). Missing near-duplicates make recall look worse than it is.

**Quantization cost (measured):** int8 and float vectors give the same recall@5 (0.233), MRR 0.168 vs
0.164. No measurable loss, so int8 stays.

## 8. CI gate: 2 points of recall@5

`.github/workflows/assistant.yml` fails a PR if recall@5 < baseline − 0.02. With 150 queries, one
query is 0.67 points, so 2 points is three queries' worth of slack: enough to ignore tie-order
noise, small enough to catch a broken ranking. Demonstrated: flipping the sort in `topK()` gave
recall@5 0 and exit code 1 (output in the commit that added the workflow).

## 9. Analytics

GA4 events via the existing `track()`. `assistant_search` records the course filter only, never the
query text, because queries are free text a student typed and could contain anything.

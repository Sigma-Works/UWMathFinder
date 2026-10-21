# Human evaluation data from UWMathFinder Lab

The 150 queries in `eval/retrieval_queries.json` were written while looking at each target
question, so they share words with it and flatter the search. [UWMathFinder Lab](https://zahid-m.github.io/uwmathfinder-lab/)
([source](https://github.com/Zahid-M/uwmathfinder-lab)) collects queries from UW students **before**
they see any question, plus graded ratings of the results. This page explains how that data
gets into `eval/` and how it is used.

## Sources

| `source` | How it was written | Used for |
|---|---|---|
| `llm` | by a model, looking at the target (`eval/retrieval_queries.json`) | the old CI gate; trend only |
| `human_blind` | by a student, from a scenario, before seeing any question; results rated wanted / related / not relevant | **TEST** split: honest score and CI gate. **DEV** split: tuning |
| `human_image_shown` | by a student while looking at one question | extra signal; biased like `llm` |

Grades: wanted = 2, related = 1, not relevant = 0. Results nobody rated count as 0.

## The rule

**Only `human_blind` DEV queries may be used for tuning**: trying a new model, changing `docText()`,
fine-tuning, picking thresholds. TEST is only for reporting and the CI gate. If you look at TEST
failures and change the system because of them, TEST stops being held out, and its score stops
meaning anything. The split is frozen in the lab (`splits/splits.json`, fixed seed), so a query
never moves between TEST and DEV; `scripts/import-lab.mjs` refuses an import that would move one.

## Updating the data

1. In the lab checkout (`../uwmathfinder-lab`), with the service key in its `.env`:
   ```sh
   node scripts/export.mjs
   git add splits/splits.json && git commit -m "Freeze splits for new lab queries"
   ```
   This drops test rows and sessions that failed attention checks, dedupes, grades, and assigns new
   `human_blind` queries to TEST (70%) or DEV (30%), stratified by course.
2. Here, on a branch:
   ```sh
   node scripts/import-lab.mjs            # reads ../uwmathfinder-lab/out/eval-export.json
   node scripts/validate-assistant.mjs
   node eval/retrieval.mjs                # metrics per source: llm, human_blind_test, human_blind_dev, human_image_shown
   ```
3. Commit `eval/human_queries.json` and open a PR. Contributors agreed that their queries may be
   published as part of an open dataset; the file contains no session ids.

## Metrics

`eval/retrieval.mjs` reports, for each source and each system (assistant, assistant_float, keyword,
keyword_words):

- **recall@5**: share of queries with a "wanted" result in the top 5
- **MRR**: mean of 1 / rank of the first "wanted" result
- **nDCG@5**: uses every grade. DCG = Σ (2^grade − 1) / log2(rank + 1) over the top 5, divided by the
  DCG of the ideal order of the judged results. 1.0 means the best-rated results come first.

Queries where nobody chose "wanted" are left out of recall and MRR; queries with nothing rated
relevant are left out of nDCG. The counts are printed so nothing disappears silently.

Human queries made with a course picked are ranked within that course (as in the lab and in the
Ask tab's course filter).

## CI gate

`node eval/retrieval.mjs --check` (the *Study assistant* workflow):

- While `eval/human_queries.json` has fewer than **100** `human_blind` TEST queries, it keeps the old
  gate: assistant recall@5 on `retrieval_queries.json` may not drop more than 2 points below
  `eval/baseline.json`.
- At 100 or more, run `node eval/retrieval.mjs --write-baseline` once and commit `eval/baseline.json`.
  It now has a `human_blind_test` entry, and the gate becomes: assistant nDCG@5 on the TEST split may
  not drop more than 2 points. Until that baseline is committed, CI prints a warning and keeps the
  old gate.

## Index versions

Each lab judgment records the UWMathFinder commit its index was synced from (`index_commit`).
Question ids are stable, so old judgments stay valid when the index is rebuilt, but a new model
can surface questions nobody rated (they count as 0). After a big index change, re-sync the lab
(`node scripts/sync-index.mjs` there) so new judgments cover what the new model returns.

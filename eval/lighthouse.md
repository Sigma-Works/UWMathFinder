# Lighthouse: before and after the study assistant

Lighthouse 12.2.1, default mobile emulation (Moto G Power, throttled), headless Chrome on the dev
machine, page served locally by `node scripts/serve.js`. Raw JSON reports are in `eval/lighthouse/`
(git-ignored; regenerate with the commands below).

```
LH=<path>/node_modules/.bin/lighthouse
$LH http://localhost:8123/index.html --chrome-flags="--headless=new" \
    --only-categories=performance,accessibility,best-practices,seo --output=json --output-path=...
```

## Runs

| Run | Page | Perf | A11y | Best pr. | SEO | Total bytes | TBT ms | LCP ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| before-1 | main page, before any assistant code | 46 | 96 | 75 | 100 | 1,973,991 | 1230 | 10980 |
| before-2 | " | 50 | 96 | 75 | 100 | 1,973,996 | 818 | 12638 |
| before-3 | " | 48 | 96 | 75 | 100 | 1,974,040 | 1033 | 11879 |
| after-plain-1 | branch, no flag | 40 | 96 | 75 | 100 | 1,973,926 | 2550 | 11826 |
| after-plain-2 | " | 41 | 96 | 75 | 100 | 1,974,201 | 2235 | 12398 |
| after-plain-3 | " | 40 | 96 | 75 | 100 | 1,973,927 | 2517 | 11809 |
| after-flag-1 | branch, `?assistant=1`, tab not opened | 37 | 96 | 75 | 100 | 1,991,827 | 2330 | 12278 |
| after-flag-2 | " | 38 | 96 | 75 | 100 | 1,991,824 | 2450 | 11949 |
| after-flag-3 | " | 38 | 96 | 75 | 100 | 1,991,827 | 2278 | 11982 |

The "after-plain" performance score was lower than "before" even though the bytes are the same, so
`main` and the branch were then measured **interleaved** (main, branch, main, branch, ...) in the
same session, `main` served from a separate git worktree:

| | Run 1 | Run 2 | Run 3 | Run 4 |
| --- | --- | --- | --- | --- |
| `main` (19fac11) | 41 / 1,974,147 B / TBT 1993 | 41 / 1,974,138 / 2182 | 41 / 1,974,136 / 2343 | 41 / 1,974,134 / 2116 |
| `study-assistant` | 41 / 1,973,926 B / TBT 2267 | 41 / 1,974,197 / 2353 | 41 / 1,974,312 / 1909 | 41 / 1,973,929 / 2429 |

## Conclusion

- **Main page (no flag): no measurable change.** Same score as `main` under the same conditions
  (41 vs 41, four runs each) and the same transferred bytes (differences of a few hundred bytes
  come from the analytics requests, which vary per run). The earlier 46–50 vs 40–41 gap was the
  machine being busier later in the session, not the code: `main` itself dropped to 41.
- **With `?assistant=1`, before opening the tab:** +17,904 bytes (`assistant.mjs` 15,768 +
  `assistant-rank.mjs` 2,136 transferred). No model, index, KaTeX or transformers.js is requested
  until the tab is opened. Score 37–38 vs 40–41 for the plain page in the same batch.
- Only the beta flag adds weight, and only students who open the Ask tab download the model
  (about 24 MB, once, then cached).

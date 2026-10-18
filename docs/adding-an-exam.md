# Adding an exam

There are two separate things you can add, and you can do either or both:

1. **The whole exam** (PDF + answer key) → it shows up in **Find Exams**.
2. **Its individual questions** (cropped images) → they show up in **Search Questions**,
   **Topics Tested** and both **generators**.

Install the helper dependencies once:

```bash
pip3 install -r requirements.txt
```

All commands below run from the repo root.

## 1. Add the whole exam

1. Name the PDFs in the usual pattern, `m<course><exam><Qtr><year>.pdf`, for example
   `m126finalWin2025.pdf`, `m124mid2Aut2023.pdf`, with the key as `…Ans.pdf`. Put them in `exams/`.
2. Generate the metadata:
   ```bash
   python3 scripts/parse_exams.py
   ```
   This writes **`exams.new.json`**. It never overwrites `exams.json`, which holds
   hand-curated tags.
3. Copy the new exam's entry into `exams.json`, set `answer_key` to the key PDF's path, and
   fill in `topics` with chapter names from `chapters.json` (matching the names lets the site
   flag topics that are later dropped from the syllabus).

## 2. Add its questions

1. Render the pages so you can read off pixel coordinates:
   ```bash
   python3 scripts/crop_questions.py pages exams/m126finalSpr2025.pdf
   ```
   Page images land in `preview_pages/` (git-ignored).
2. Write a `crop_config.json` with one entry per question: its page, pixel box, chapter and
   exam types. The format is documented at the top of `scripts/crop_questions.py`. At 150 dpi
   the box `[88, 100, 1185, 1600]` fits the content area of a standard UW exam page.
   Add a top-level `"source"` block (exam, quarter, year, exam_id, staff) and a `"problem"`
   number per question so each one is cited properly, and use `"a_parts"` when an answer
   runs across a page break.
3. Crop and append:
   ```bash
   python3 scripts/crop_questions.py batch crop_config.json
   ```
   Images go to `questions/`, entries are appended to `questions.json`, and ids
   auto-increment. Then run `npm run build:pages` to refresh the course pages.

### Classifying a question

- **chapter**: the topic it mainly tests. It must be an `id` from `chapters.json` for that
  course (e.g. `taylor_series`, `double_integrals` for Math 126). If it spans two, pick the
  dominant one.
- **exam_types**: which exams it could appear on. A question on early material can be
  `["Midterm 1", "Final"]`; one on the last chapters is usually `["Final"]`.

## 3. Check and submit

```bash
npm run validate
```

This catches unknown chapter ids, duplicate question ids, and files that are referenced but
missing. Then open a pull request with the PDFs, images and JSON changes.

> The generator prints its own "Problem 1, 2, 3…" above each image, so an image that
> internally says "8." is fine. To hide the original number, crop just below it.

# Adding a real exam to the generator — worked example

We just did **Math 126 Final, Spring 2025** together. Here's the exact loop so you
can repeat it for any exam. It produced 8 real questions that now show up when you
generate a Math 126 Final.

## What you got from this round

- `questions.json` — 8 real entries (no more sample placeholders)
- `questions/` — 16 PNGs (8 questions + 8 answer-key crops)
- `crop_config_m126finalSpr2025.json` — the config we used, as a template for the next exam
- `crop_questions.py` — the helper (now bug-fixed)

## The 5-step loop for each new exam

### 1. Render the exam pages to images
```bash
pip3 install pymupdf pillow
python3 crop_questions.py pages exams/m126finalSpr2025.pdf
```
This dumps every page to `preview_pages/` and prints each page's pixel size.

### 2. Find each problem and its box
Open the page images. For this exam the layout was one problem per page, starting
on page 3 (page 1 = cover, page 2 = blank scratch). So:

| Problem | Question page | Answer-key page | Chapter | Eligible exams |
|---|---|---|---|---|
| 1 | 3 | 1 | vectors | Midterm 1, Final |
| 2 | 4 | 2 | space_curves | Midterm 2, Final |
| 3 | 5 | 3 | partials | Midterm 2, Final |
| 4 | 6 | 4 | optimization | Final |
| 5 | 7 | 5 | double_int | Final |
| 6 | 8 | 6 | double_int | Final |
| 7 | 9 | 7 | taylor | Midterm 1, Final |
| 8 | 10 | 8 | taylor | Midterm 1, Final |

The pixel box `[88, 100, 1185, 1600]` cropped the content area below the running
header at 150 dpi. That same box works for any standard UW Math exam page at 150 dpi.

### 3. Write a crop_config.json
Copy `crop_config_m126finalSpr2025.json` and edit the `source_pdf`, `answer_pdf`,
page numbers, chapters, and exam_types. The `chapter` value **must** match an id in
`chapters.json` (taylor, vectors, space_curves, partials, optimization, double_int
for 126; see chapters.json for the other courses).

### 4. Crop + append to questions.json
```bash
python3 crop_questions.py batch crop_config.json
```
IDs auto-increment, so running this on a second exam adds q0009, q0010, ... without
clobbering the first.

### 5. Commit to your fork
Upload the new `questions/*.png` and the updated `questions.json` to your fork —
same drag-and-drop you've been doing. The generator picks them up automatically.

## Classification cheat-sheet

The only judgment calls are **chapter** and **exam_types**:
- **chapter**: what topic does the problem mainly test? (If it spans two, pick the dominant one — e.g. P2 here was quadric surface + space curve, tagged space_curves.)
- **exam_types**: which exams could this question appear on? A Taylor question shows up on Midterm 1 AND the Final, so it gets both. A double-integral question is Final-only.

If you're ever unsure, paste me the question image or the problem text and I'll tell
you the chapter and exam_types — same as I did for the topic tags earlier.

## A note on numbering

Each crop keeps the original "Problem N" printed in the image, but the generator adds
its own "Problem 1, 2, 3..." header above it. So a generated exam might show the
generator's "Problem 1" above an image that internally says "8." That's harmless —
the generator's header is the one that counts. If it bugs you, crop just below the
original problem number next time (raise the box's y0 a little).

# Practice Exam Generator — what's new in v0.5

This adds a **"Generate Practice Exam"** feature to UWMathFinder. Nothing from the
existing exam finder was removed or changed — it's a second view bolted onto the
same page, with its own data files.

## Files in this delivery

| File | What it is | What to do with it |
|------|-----------|--------------------|
| `index.html` | Your site, now v0.5 with the generator built in | Replace the existing `index.html` in your repo |
| `chapters.json` | Defines each course's chapters and which exam each chapter belongs on | Add to repo root. **Edit to match the real syllabus.** |
| `questions.json` | The question bank the generator pulls from — currently **sample/dummy data** so you can see it work | Add to repo root. Replace with real questions over time. |
| `crop_questions.py` | Helper script to cut real questions out of your exam PDFs into images | Keep locally (like `parse_exams.py`); not needed on the site |

## How the feature works

1. Student picks **Course**, **Exam** (Midterm 1 / Midterm 2 / Final), and **questions per chapter** (default 2).
2. The chapter checklist only shows chapters that belong on the chosen exam — so a Midterm 1 won't pull from material taught later. A Final pulls from everything. This is what gives you the "2 questions from each chapter, structured by exam" behavior.
3. They can uncheck chapters to **focus** on specific ones.
4. **Generate** assembles a randomized paper in the classic UW exam format (cover sheet + numbered problems), with **Print / Save as PDF** and a **Reshuffle** button.
5. **Include answer keys** toggles solutions in under each problem.

Right now it runs on **sample placeholder questions** so the mechanics are visible. The placeholders say *"replace with cropped question image."*

## Adding real questions (the part that needs you)

Each question in `questions.json` looks like this:

```json
{
  "id": "q0001",
  "course": "Math 126",
  "chapter": "taylor",
  "exam_types": ["Midterm 1", "Final"],
  "source": "m126mid1Spr2025 (p2)",
  "points": 10,
  "image": "questions/q0001.png",
  "answer_image": "questions/q0001_ans.png"
}
```

You classify each question by **course**, **chapter** (must match an id in `chapters.json`), and **which exams it can appear on**. The `image` is a cropped picture of the question so it looks exactly like the original.

### Using the crop helper

```bash
pip3 install pymupdf pillow

# 1. Render an exam's pages so you can read off pixel coordinates
python3 crop_questions.py pages exams/m126finalSpr2025.pdf

# 2. Make a crop_config.json describing where each question sits (see script header)
# 3. Batch-crop them into questions/ and append to questions.json
python3 crop_questions.py batch crop_config.json
```

Then commit the new `questions/*.png` and the updated `questions.json` — same workflow you already use for exams.

> Important: the `chapter` values in `questions.json` must match the chapter `id`s in `chapters.json`. Adjust `chapters.json` first so it reflects the real UW syllabus (the current chapters are a reasonable starting guess), then classify questions into those chapters.

## A note on classification

I built everything with sample data as you asked, so you can try the feature
immediately. When you're ready to add real questions, that's the step where you
(or I, if you paste me exam text) decide which chapter each question tests and
which exams it belongs on. The generator does the rest automatically.

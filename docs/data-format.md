# Data files

The site reads four JSON files from the repo root. `npm run validate` checks all of them.

## `exams.json`: whole past exams (Find Exams)

```json
{
  "id": "m126finalWin2025",
  "course": "Math 126",
  "type": "Final",
  "quarter": "Winter",
  "year": 2025,
  "instructor": "Staff",
  "topics": ["Vectors and Geometry in 3D", "Taylor Series"],
  "pdf": "exams/m126finalWin2025.pdf",
  "answer_key": "exams/m126finalWin2025Ans.pdf"
}
```

`type` is `Midterm 1`, `Midterm 2` or `Final`. Use `"#"` for a PDF or key you don't have yet.
Topic names should match chapter names in `chapters.json`.

## `questions.json`: individual questions (generators, Search Questions, Topics)

```json
{
  "id": "q0001",
  "course": "Math 124",
  "chapter": "limit_of_a_function",
  "exam_types": ["Midterm 1", "Final"],
  "points": 10,
  "image": "questions/q0001.png",
  "answer_image": "questions/q0001_ans.png",
  "low_confidence": false,
  "source": {
    "course": "Math 124", "exam": "Final", "quarter": "Autumn", "year": 2025,
    "term": "Autumn 2025", "problem": 1, "exam_id": "m124finalAut2025",
    "staff": ["Instructor names"]
  }
}
```

- `chapter` must be an id from `chapters.json` for the same course.
- `exam_types` lists the exams this question could plausibly appear on.
- `low_confidence: true` shows an "unverified tag" note in Search Questions.
- Question ids are used in share links, so **never renumber or reuse them**.

## `chapters.json`: chapters per course

```json
{ "courses": { "Math 126": { "chapters": [
  { "id": "taylor_series", "name": "Taylor Series", "types": ["Midterm 1", "Final"] }
] } } }
```

`types` says which exams the chapter normally belongs on. Chapter order is the order
problems appear in on a generated exam.

## `syllabus.json`: syllabus changes by quarter

See [syllabus-changes.md](syllabus-changes.md).

## Realistic-exam blueprints

The realistic generator's problem counts, point totals and chapter frequencies are in
`EXAM_BLUEPRINTS` in `assets/js/app.js`, derived from real past exams. Chapters removed in
`syllabus.json` are dropped from these automatically; you only need to edit the
blueprints when a course's exam *format* changes (e.g. a final goes from 8 to 10 problems).

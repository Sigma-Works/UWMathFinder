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
`instructor` credits who the exam belongs to:

- **Midterms** are written by each professor for their own sections, so name that professor. Find
  them on the exam, from the archive that published it (the department archive and Prof. Loveless's
  archive name each file's instructor), or from the [UW Time Schedule](https://www.washington.edu/students/timeschd/)
  when the cover prints a section (e.g. "Math 307N, Winter 2018" → section N's instructor).
- **Finals** in Math 120–126 are common exams sat by every section, so list every professor
  teaching that quarter, e.g. `"Camacho, Loveless, Ostroff"`: from the cover's "check one" list
  if it has one, otherwise the Time Schedule's lecture sections. Add a `note` saying so.
- Use `"Staff"` only when there's no evidence. Never guess.

`label` *(optional)* replaces the card title, e.g. `"Math 324: Test 3 (Sections A and B)"` for
an exam from a course's old number. `note` *(optional)* is a short line shown on the card.
`source_url` *(optional)* is the page the exam was published on (e.g. the UW Math department archive);
exam cards link to it as "Source ↗". When a quarter has several instructors' versions, the file name
gets an `_Instructor` suffix, e.g. `exams/m126mid1Aut2023_Ostroff.pdf`.
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
- `skills` *(optional)*: finer-grained tags within the chapter, e.g. `["Chain Rule", "Product Rule"]`.
  They're shown as chips on the question and are searchable. Reuse existing spellings.
- `also_in` *(optional)*: also count the question toward another course's chapter, e.g.
  `[{ "course": "Math 224", "chapter": "double_integrals" }]` for a Math 126 problem on a topic
  that moved to Math 224. It keeps its id and `source`, and takes that chapter's exam types there.
- Question ids are used in share links, so **never renumber or reuse them**.

## `chapters.json`: chapters per course

```json
{ "courses": { "Math 126": { "chapters": [
  { "id": "taylor_series", "name": "Taylor Series", "types": ["Midterm 1", "Final"], "sections": ["11.10", "11.11"] }
] } } }
```

`types` says which exams the chapter normally belongs on. Chapter order is the order
problems appear in on a generated exam. `sections` *(optional)* lists the textbook sections
the chapter covers; the weekly syllabus check uses them to match the course page's outline
to chapters (see [syllabus-changes.md](syllabus-changes.md#automatic-weekly-check)).

## `syllabus.json`: syllabus changes by quarter

See [syllabus-changes.md](syllabus-changes.md).

## Realistic-exam blueprints

The realistic generator's problem counts, point totals and chapter frequencies are in
`EXAM_BLUEPRINTS` in `assets/js/app.js`, derived from real past exams. Chapters removed in
`syllabus.json` are dropped from these automatically; you only need to edit the
blueprints when a course's exam *format* changes (e.g. a final goes from 8 to 10 problems).

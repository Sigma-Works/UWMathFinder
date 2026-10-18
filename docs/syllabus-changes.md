# Keeping the generators in line with the current syllabus

Courses change: a topic gets dropped from Math 126, or moves from Midterm 2 to the
Final. The question bank still holds every past problem, so without help the
practice-exam generator would keep giving students topics they won't be tested on.

`syllabus.json` fixes that. It records **what changed and from which quarter**, and the
site applies it automatically based on today's date.

## What the site does with it

For the quarter students are studying for right now (Jan–Mar = Winter, Apr–Jun = Spring,
Jul–Aug = Summer, Sep–Dec = Autumn):

- **Realistic generator** leaves removed chapters out. The exam keeps its usual length,
  because their slots go to the remaining chapters.
- **Custom generator** shows removed chapters greyed out as "not tested since …".
- **Find Exams** flags those topics on older exams ("· not tested now"), so students
  know which problems to skip.
- **Search Questions** and **Topics Tested** mark them as not on the current syllabus.
- **Shared exam links** made before the change show a warning.
- If nobody has confirmed a course for the current quarter, the generator shows
  "Last confirmed <quarter>, double-check topics against your course page."

### A real example

From Autumn 2026, Math 126 no longer covers Chapter 15 (multiple integrals); it moved to
Math 224. `syllabus.json` records that, so 126 generators leave out double integrals and older
exams flag those problems.

## The file

```json
{
  "courses": {
    "Math 126": {
      "verified": "Winter 2027",
      "changes": [
        { "from": "Winter 2027", "remove": ["taylor_series"], "note": "Moved to Math 127" }
      ]
    }
  }
}
```

- `verified`: the latest quarter someone checked this course's syllabus.
- `changes`: applied oldest first, each from its `from` quarter onwards:
  - `remove`: chapter ids (from `chapters.json`) that are no longer tested.
  - `restore`: chapter ids that are tested again (undoes an earlier `remove`).
  - `exam_types` *(optional)*: limit the change to some exams, e.g. `["Midterm 2"]`.
  - `note` *(optional)*: why, for maintainers.

Quarters are written `"Winter 2027"`, `"Spring 2027"`, `"Summer 2027"`, `"Autumn 2027"`.

### More examples

A topic moves from Midterm 2 to the Final only:

```json
{ "from": "Spring 2027", "remove": ["double_integrals"], "exam_types": ["Midterm 2"] }
```

A dropped topic comes back:

```json
{ "from": "Autumn 2028", "restore": ["taylor_series"] }
```

A brand-new topic: add the chapter to `chapters.json` first, then add questions for it.
Nothing is needed in `syllabus.json` (new chapters are on the syllabus by default).

## The quarterly routine

1. Before each quarter, a GitHub Action
   ([`syllabus-reminder.yml`](../.github/workflows/syllabus-reminder.yml)) opens an issue
   called **"Confirm syllabi for <quarter>"** with a checklist of courses.
2. For each course, check the course page or syllabus.
3. Edit `syllabus.json`: set `verified` to the new quarter, and add a `changes` entry if
   something changed. You can add a change before the quarter starts; it switches on
   when the quarter begins.
4. Run `npm run validate` (it catches typos in chapter ids and quarter names), then open
   a pull request and close the reminder issue.

Students can also report changes from the site ("Syllabus changed? Tell us" on the
generator), which opens a pre-filled issue.

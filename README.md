# UWMathFinder

[![CI](https://github.com/Sigma-Works/UWMathFinder/actions/workflows/ci.yml/badge.svg)](https://github.com/Sigma-Works/UWMathFinder/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Find past University of Washington math exams by topic, and practice with exams built from real past questions.**

🔗 **Live site: [uwmathfinder.com](https://uwmathfinder.com)**

Covers Math 120, 124, 125, 126, 207, 208 and 224: about 290 midterms and finals with answer keys,
and over 1,600 individual problems, each tagged by chapter and skill.

## Why we built this

UWMathFinder was started by Saad and Zahid, two UW students who finished the Math 12X
series and thought, "Hey, we can make this better!" We saw professors (and fellow students)
spend ages digging through dozens of old finals to find one worked example of a specific
topic. So we built a database of every exam we could find, tagged with the topics it tests,
so anyone can practise a skill without scouring PDFs for hours.

## Features

- **Find Exams:** fuzzy search and filters by course, exam, quarter and topic, plus a
  one-click *Midterm mode*. Every exam links to its PDF and answer key.

  <img width="784" alt="Exam cards with topic tags" src="https://github.com/user-attachments/assets/fac512fb-a3e7-4241-99bb-4ca77b218abb" />

- **Search Questions:** practise individual problems by chapter, course or exam. Reveal answers in place and
  mark each one *Done* or *Needs review* (saved in your browser, no account needed).
- **Practice Exam Generator:**
  - *Realistic* mode mirrors a real UW exam's length, points and chapter mix.
  - *Custom* mode lets you pick chapters and how many questions from each.
  - Both print in the classic exam format and can be shared with a link that rebuilds the exact same paper.
  - Can focus on the questions you flagged *Needs review* and skip the ones you've done.
- **Syllabus-aware:** the generators follow each course's *current* syllabus. When a topic is
  dropped, it stops appearing in generated exams and is flagged on older exams. See
  [docs/syllabus-changes.md](docs/syllabus-changes.md).
- **Topics Tested:** which chapters show up most often on each course's exams.
- **Course pages** (e.g. [/courses/math-126/](https://uwmathfinder.com/courses/math-126/)) list every past exam in plain HTML, so search engines can find them.
- Light and dark themes, keyboard accessible, works on phones.

<img width="1422" alt="Searching and filtering exams" src="https://github.com/user-attachments/assets/463b12d8-fbe2-4c2e-9f81-536db5cef917" />

## Run it locally

No build step and no dependencies. You only need Python 3 (for a local web server) and,
for the checks, Node 18+.

```bash
git clone https://github.com/Sigma-Works/UWMathFinder.git
cd UWMathFinder
npm start            # or: python3 -m http.server 8000
```

Open <http://localhost:8000>. Opening `index.html` directly won't work, because the page
loads its data with `fetch`.

```bash
npm test             # unit tests
npm run validate     # check the JSON data files
```

## How it works

A static site hosted on GitHub Pages. The page (`index.html`, `assets/`) loads plain JSON
files from the repo:

| File | Used for |
|---|---|
| `exams.json` | Whole exams in Find Exams |
| `questions.json` + `questions/` | Individual problems for the generators, search and topics |
| `chapters.json` | Each course's chapters and which exams they belong on |
| `syllabus.json` | Topics added or dropped by quarter, so generators stay current |

Details: [docs/data-format.md](docs/data-format.md). Fuzzy search uses
[Fuse.js](https://www.fusejs.io/), and the site falls back to plain search if it can't load.

### Staying current each quarter

Every week, a GitHub Action reads each course's official UW page and compares its outline with
the textbook sections our chapters cover. If a topic disappears or comes back, it opens a pull
request proposing the `syllabus.json` change, and a maintainer reviews and merges it. Before
every quarter, another Action also opens a **"Confirm syllabi"** issue for a manual check. Until that's done, the site warns students that the
syllabus hasn't been confirmed for the new quarter. Students can report changes from the site
too ("Syllabus changed? Tell us").

## Contributing

Contributions are welcome, and most don't need any code: reporting a syllabus change, fixing a
tag, or adding a past exam all help. See [CONTRIBUTING.md](CONTRIBUTING.md) to get started,
and please follow our [Code of Conduct](CODE_OF_CONDUCT.md). Found a security problem? See
[SECURITY.md](SECURITY.md).

## License and credits

The **code** is released under the [MIT License](LICENSE).

The **exam material** (PDFs, answer keys and question images in `exams/`, `questions/` and
`questions_207_208/`) belongs to the University of Washington Department of Mathematics and
the instructors who wrote it. It is **not** covered by the MIT license. It is reproduced for
non-commercial student practice, and each problem cites its source exam and instructors. If
you are a rights holder and want something removed, please open an issue.

UWMathFinder is a student project and is not affiliated with or endorsed by the University of Washington.

Built by [Saad Ahmed](https://www.linkedin.com/in/sssaaaddd/) and
[Zahid Mannan](https://www.linkedin.com/in/zahid-m-5a9a11320/).

# Contributing to UWMathFinder

Thanks for helping! Most contributions don't need any coding. Pick whichever fits:

| You want to… | Do this |
|---|---|
| Report a topic that's no longer tested (or newly tested) | [Open a "Syllabus change" issue](https://github.com/Sigma-Works/UWMathFinder/issues/new?template=syllabus_change.yml) |
| Report a broken link, wrong tag, or bug | [Open a bug report](https://github.com/Sigma-Works/UWMathFinder/issues/new?template=bug_report.yml) |
| Add a past exam or its questions | Follow [docs/adding-an-exam.md](docs/adding-an-exam.md) and open a pull request |
| Record a syllabus change yourself | Follow [docs/syllabus-changes.md](docs/syllabus-changes.md) and open a pull request |
| Improve the site's code | Read on |

By taking part you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).

## Running the site locally

The site is plain HTML, CSS and JavaScript, with no build step and no dependencies. It
loads its data with `fetch`, so it needs a local web server (opening `index.html`
directly won't work):

```bash
npm start          # same as: python3 -m http.server 8000
```

Then open <http://localhost:8000>.

## Checks

```bash
npm test           # unit tests for the syllabus logic (Node 18+)
npm run validate   # checks questions.json, exams.json, chapters.json and syllabus.json
```

CI runs both on every pull request, so please run them before you push.

## Project layout

```
index.html              page markup (all four tabs)
assets/css/styles.css   all styles, light and dark themes
assets/js/app.js        page behaviour: finder, generators, search, topics
assets/js/syllabus.js   current-syllabus logic (pure functions, unit-tested)
exams.json              whole past exams shown in "Find Exams"
questions.json          individual questions used by the generators and search
chapters.json           each course's chapters and which exams they belong on
syllabus.json           syllabus changes by quarter (see docs/syllabus-changes.md)
exams/, questions/      exam PDFs and cropped question images (UW's material)
scripts/                helpers: data validation, adding exams, quarterly reminder
tests/                  unit tests
docs/                   guides for maintainers and contributors
```

The data formats are described in [docs/data-format.md](docs/data-format.md).

## Code style

- Match the surrounding code: 2-space indent, single quotes in JS, no framework.
- Give every function a short comment saying what it does and why. Comment non-obvious lines.
- Anything that comes from the URL or from users goes through `esc()` before it is put into `innerHTML`.
- Keep `assets/js/syllabus.js` free of DOM code so it stays testable in Node.
- User-facing change? Add a line to the `CHANGELOG` array at the top of `assets/js/app.js`.

## Pull requests

1. Fork the repo and create a branch (`git checkout -b fix-dead-link`).
2. Make your change and run `npm test` and `npm run validate`.
3. Open a pull request and fill in the template. Small, focused PRs are reviewed fastest.

## About the exam material

The exams, answer keys and question images are the work of the University of Washington
Department of Mathematics and its instructors. Only add material that UW has made public,
keep the source and instructor fields accurate, and don't add anything that isn't
already public (for example, exams that haven't been released yet).

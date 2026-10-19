# Practice variants ("New Problems" tab)

The **New Problems** tab shows brand-new practice problems: real UW exam problems
with the numbers changed. Each one comes with a final answer and a full worked
solution. They are generated ahead of time and committed, so the site stays
static.

```
scripts/variants/common.py   helpers + the template contract
scripts/variants/m120.py …   templates, one file per course (m120, m124, m125, m126, m207, m208, m224)
scripts/variants/build.py    runs every template, checks every answer, writes variants/
variants/index.json          courses → topics (loaded first by the tab)
variants/math-208.json …     the problems for one course
assets/js/variants.js        the tab itself (KaTeX rendering, loaded on first open)
```

## Accuracy

A wrong answer on a problem we wrote ourselves is the worst bug this feature can have.
So every template has two halves:

1. **`make(rng)`** picks parameters, usually working backwards from a clean answer
   (e.g. choose the eigenvalues first, then build the matrix). It writes the problem,
   the answer and the worked solution, and returns the raw data.
2. **`check(data)`** re-derives the answer **a different way**, from the problem alone:
   - SymPy linear algebra (inverse, rank, eigenvectors) instead of our row reduction.
   - Numerical derivatives, limits and root-finding (implicit curves, related rates).
   - Dense sampling for extreme values, sign charts and closest-approach problems.
   - Substituting a solution back into its differential equation, or integrating the
     equation numerically.
   - Taking the Laplace transform of the answer.
   - Redoing a polar, cylindrical or spherical integral in Cartesian coordinates.
   - Computing a Green's, Stokes' or divergence-theorem answer as the line or surface
     integral it replaces.

`build.py` runs `check()` on every variant and stops with an error if any answer
disagrees. CI runs `build.py --check` on every pull request: it regenerates
everything, re-runs every check and fails if `variants/` differs from what is committed.

Spotted a mistake anyway? Each problem has a **Report a mistake** link that opens a
GitHub issue with the problem's id (e.g. `m208-inverse-07`).

## Citing the original problem

Each template is modelled on a real archived problem and says so on the site
("modelled on Math 208 Final, Winter 2019, Problem 7"):

```python
based_on={'exam': 'm208finalWin2019_RG', 'problem': 7}
```

`build.py` checks that the exam and problem exist in `exams.json` and
`questions.json`. A few Math 224 topics have no archived problems yet (surface area,
change of variables, Green's theorem). Those templates follow the textbook section
instead, and the site says so:

```python
based_on={'style': 'Stewart §16.4'}
```

## Adding a template

1. Pick a real problem from the archive and note its exam id and problem number.
2. In the course's file, write `make(rng)` and a separate `check(data)` and register them:

   ```python
   @template(course='Math 208', chapter='determinants', id='m208-det-cofactor',
             title='A 4×4 determinant by cofactor expansion',
             based_on={'exam': 'm208finalSpr2022_HR', 'problem': 1}, check=chk_det)
   def det_cofactor(rng):
       ...
       return {'problem': html, 'answer': html, 'solution': html, 'data': {...}}
   ```

   - Write the text as HTML with math in `$…$` or `\[…\]` (rendered by KaTeX).
   - `chapter` must be one of the course's ids in `chapters.json`.
   - `raise Reject` for parameters that give an ugly or degenerate problem; another
     seed is tried.
3. Build and look at a few variants:

   ```bash
   pip install -r scripts/variants/requirements.txt    # Python 3.12+
   python3 scripts/variants/build.py --show m208-det-cofactor 3
   python3 scripts/variants/build.py --course 'Math 208'   # rebuild just that course
   python3 scripts/variants/build.py                       # everything (what CI checks)
   ```

4. Open the New Problems tab locally and read a few rendered solutions before
   opening a pull request.

Variants are seeded by template id, so rebuilding only changes the output when a
template changes.

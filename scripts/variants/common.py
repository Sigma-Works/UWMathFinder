"""Shared helpers for the practice-problem generators (see build.py).

A template is a function make(rng) that picks parameters, writes the problem,
the final answer and a worked solution, and returns them with the raw data.
Every template also has a check(data) that recomputes the answer a different
way (usually with SymPy from the problem's inputs alone, or by numerical
integration) and raises if the two disagree. build.py runs check() on every
variant before writing it, so no unverified answer reaches the site.

Text is HTML with math in $...$ (inline) or \\[...\\] (display), rendered with KaTeX.
"""
from fractions import Fraction as F
from math import lcm
import mpmath
import sympy as sp

mpmath.mp.dps = 20   # plenty for the 1e-7..1e-10 agreement the checks ask for
TEMPLATES = []


def template(**meta):
    """Register a template: @template(course=, chapter=, id=, title=, based_on=, check=)."""
    assert callable(meta.get('check')), f"{meta.get('id')}: every template needs a check()"
    def wrap(fn):
        TEMPLATES.append({**meta, 'make': fn})
        return fn
    return wrap


class Reject(Exception):
    """These parameters give a degenerate or ugly problem; build.py tries others."""


def need(cond, msg='check failed'):
    """Assert in a check() (kept on with python -O, unlike assert)."""
    if not cond:
        raise AssertionError(msg)


def close(a, b, tol=1e-9):
    """Numerical agreement, relative for large values."""
    a, b = complex(a), complex(b)
    return abs(a - b) <= tol * max(1, abs(a), abs(b))


# ── LaTeX ─────────────────────────────────────────────────────────────
def L(e):
    """SymPy expression (or number) as LaTeX."""
    return sp.latex(sp.sympify(e), ln_notation=True)


def fx(x):
    """A Fraction or integer as LaTeX."""
    x = F(x)
    if x.denominator == 1:
        return str(x.numerator)
    return ('-' if x < 0 else '') + f'\\tfrac{{{abs(x.numerator)}}}{{{x.denominator}}}'


def mat(A, bar=None):
    """Matrix as LaTeX; bar = number of columns before an augmentation line."""
    rows = ' \\\\ '.join(' & '.join(v if isinstance(v, str) else fx(v) for v in r) for r in A)
    frac = '\\tfrac' in rows
    if frac:
        rows = rows.replace('\\tfrac', '\\dfrac')
    if bar is None:
        body = f'\\begin{{bmatrix}}{rows}\\end{{bmatrix}}'
    else:
        n = len(A[0])
        spec = 'r' * bar + '|' + 'r' * (n - bar)
        body = f'\\left[\\begin{{array}}{{{spec}}}{rows}\\end{{array}}\\right]'
    return '{\\def\\arraystretch{1.6}' + body + '}' if frac else body


def vec(v):
    return mat([[x] for x in v])


def poly_latex(coeffs, var='x'):
    """[a, b, c] -> 'a x^2 + b x + c' with tidy signs (integer or Fraction coefficients)."""
    n = len(coeffs) - 1
    out = []
    for i, c in enumerate(coeffs):
        c = F(c)
        if c == 0:
            continue
        p = n - i
        mon = '' if p == 0 else (var if p == 1 else f'{var}^{{{p}}}')
        a = abs(c)
        coef = fx(a) if (a != 1 or p == 0) else ''
        out.append(('-' if c < 0 else '+') + coef + mon)
    s = ''.join(out) or '0'
    return s[1:] if s.startswith('+') else s


# ── exact linear algebra with working (Fractions) ────────────────────
def M(rows):
    return [[F(x) for x in r] for r in rows]


def _term(c, r):
    c = F(c)
    a = abs(c)
    return f'{"+" if c > 0 else "-"}{"" if a == 1 else fx(a)}R_{r}'


def rref_steps(A, bar=None, per_line=1):
    """Gauss-Jordan elimination, one operation type per step (swap, scale, or clearing a column).
    Returns (LaTeX display block, reduced matrix, pivot columns)."""
    A = [r[:] for r in A]
    m = len(A)
    ncols = bar if bar is not None else len(A[0])
    start = mat(A, bar)
    steps, piv, r = [], [], 0
    for c in range(ncols):
        cand = [i for i in range(r, m) if A[i][c] != 0]
        if not cand:
            continue
        p = next((i for i in cand if abs(A[i][c]) == 1), cand[0])
        if p != r:
            A[r], A[p] = A[p], A[r]
            steps.append((f'R_{r+1}\\leftrightarrow R_{p+1}', mat(A, bar)))
        if A[r][c] != 1:
            k = 1 / A[r][c]
            A[r] = [k * x for x in A[r]]
            lab = f'-R_{r+1}' if k == -1 else f'{"-" if k < 0 else ""}{fx(abs(k))}R_{r+1}'
            steps.append((lab, mat(A, bar)))
        labels = []
        for i in range(m):
            if i != r and A[i][c] != 0:
                f = A[i][c]
                A[i] = [a - f * b for a, b in zip(A[i], A[r])]
                labels.append(f'R_{i+1}{_term(-f, r+1)}')
        if labels:
            steps.append((',\\ '.join(labels), mat(A, bar)))
        piv.append(c)
        r += 1
        if r == m:
            break
    if not steps:
        return '\\[' + start + '\\quad\\text{(already reduced)}\\]', A, piv
    chunks = [f'\\xrightarrow{{{lab}}}{mt}' for lab, mt in steps]
    rows = [' '.join(chunks[i:i + per_line]) for i in range(0, len(chunks), per_line)]
    body = '\\begin{aligned}' + start + ' &' + rows[0] + ''.join('\\\\ &' + rw for rw in rows[1:]) + '\\end{aligned}'
    return '\\[' + body + '\\]', A, piv


def nullspace(R, piv, n):
    """Integer-scaled null-space basis from a reduced matrix, and the free columns."""
    free = [j for j in range(n) if j not in piv]
    basis = []
    for f in free:
        v = [F(0)] * n
        v[f] = F(1)
        for i, p in enumerate(piv):
            v[p] = -R[i][f]
        k = lcm(*[x.denominator for x in v])
        basis.append([x * k for x in v])
    return basis, free


def mul(A, B):
    return [[sum(a * b for a, b in zip(r, c)) for c in zip(*B)] for r in A]


def sym(A):
    """Fractions -> SymPy Matrix (for independent checks)."""
    return sp.Matrix([[sp.Rational(x.numerator, x.denominator) if isinstance(x, F) else x for x in r] for r in A])


def rand_unimodular(rng, n, steps=None, maxent=6):
    """A random integer matrix with determinant ±1 (so its inverse is an integer matrix)."""
    while True:
        A = [[int(i == j) for j in range(n)] for i in range(n)]
        for _ in range(steps or 2 * n):
            i, j = rng.sample(range(n), 2)
            k = rng.choice([-2, -1, 1, 2])
            A[i] = [a + k * b for a, b in zip(A[i], A[j])]
        rng.shuffle(A)
        if all(abs(x) <= maxent for r in A for x in r) and sum(x != 0 for r in A for x in r) >= n + 2:
            return A


def nz(rng, lo, hi):
    """Random nonzero integer in [lo, hi]."""
    return rng.choice([k for k in range(lo, hi + 1) if k != 0])


# ── numerical integration (for independent checks) ───────────────────
def quad(f, a, b):
    return mpmath.quad(f, [a, b])


def quad2(f, x0, x1, y0, y1):
    """∫_{x0}^{x1} ∫_{y0(x)}^{y1(x)} f(x, y) dy dx; y0/y1 may be numbers or functions of x."""
    g0 = y0 if callable(y0) else (lambda x, c=y0: c)
    g1 = y1 if callable(y1) else (lambda x, c=y1: c)
    return mpmath.quad(lambda x: mpmath.quad(lambda y: f(x, y), [g0(x), g1(x)]), [x0, x1])


def quad3(f, a, b, c, d, e, g):
    """Iterated triple integral with constant limits: ∫_a^b ∫_c^d ∫_e^g f(u, v, w) dw dv du."""
    return mpmath.quad(f, [a, b], [c, d], [e, g])


def rk4(f, t0, y0, t1, steps=4000):
    """Integrate y' = f(t, y) (y a list of floats) from t0 to t1 with classical Runge-Kutta; returns y(t1)."""
    h = (t1 - t0) / steps
    tt, yv = t0, list(y0)
    for _ in range(steps):
        k1 = f(tt, yv)
        k2 = f(tt + h / 2, [a + h / 2 * b for a, b in zip(yv, k1)])
        k3 = f(tt + h / 2, [a + h / 2 * b for a, b in zip(yv, k2)])
        k4 = f(tt + h, [a + h * b for a, b in zip(yv, k3)])
        yv = [a + h / 6 * (b + 2 * c + 2 * d + e) for a, b, c, d, e in zip(yv, k1, k2, k3, k4)]
        tt += h
        if any(abs(a) > 1e6 for a in yv):
            return [float('inf') if a > 0 else float('-inf') for a in yv]
    return yv


def num(e, **subs):
    """Evaluate a SymPy expression numerically (mpmath precision)."""
    return complex(sp.N(sp.sympify(e).subs(subs), 30))

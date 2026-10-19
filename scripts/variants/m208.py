"""Math 208 (Linear Algebra) practice-problem templates. See common.py for the contract."""
from fractions import Fraction as F
from itertools import permutations
import sympy as sp

from common import (template, Reject, need, M, fx, mat, vec, rref_steps, nullspace, mul, sym,
                    rand_unimodular, nz)

C = 'Math 208'


# ── helpers ──────────────────────────────────────────────────────────
def lin(row, names):
    """Coefficients and variable names -> '2x_1 - x_2 + 3x_4'."""
    out = ''
    for c, n in zip(row, names):
        c = F(c)
        if c == 0:
            continue
        a = abs(c)
        t = n if a == 1 else f'{fx(a)}{n}'
        out += (' - ' if c < 0 else (' + ' if out else '')) + t
    return out.strip() or '0'


def system(A, b, names):
    rows = ' \\\\ '.join(f'{lin(r, names)} &= {fx(v)}' for r, v in zip(A, b))
    return f'\\[\\begin{{aligned}}{rows}\\end{{aligned}}\\]'


def xs(n):
    return [f'x_{{{i + 1}}}' for i in range(n)]


def rref_pattern(rng, m, n, r, lo=-3, hi=3):
    """A random m×n matrix in reduced echelon form with rank r (pivot in column 1)."""
    piv = sorted([0] + rng.sample(range(1, n), r - 1))
    R = [[0] * n for _ in range(m)]
    for i, p in enumerate(piv):
        R[i][p] = 1
        for j in range(p + 1, n):
            if j not in piv:
                R[i][j] = rng.randint(lo, hi)
    return R, piv


def scramble(rng, R, maxent=9):
    """E·R for a random invertible integer E, so R is the reduced echelon form of the result."""
    m = len(R)
    E = rand_unimodular(rng, m, maxent=4)
    A = mul(E, R)
    if any(abs(x) > maxent for r in A for x in r) or any(all(x == 0 for x in r) for r in A[:2]):
        raise Reject
    return A


def det_rows(A):
    return sym(M(A)).det()


def two_by_two(a, b, c, d):
    return f'({fx(a)})({fx(d)})-({fx(b)})({fx(c)})'


def combo_tex(cs, labs):
    """[2, -1, 0, 1] with labels -> '2v_1 - v_2 + v_4'."""
    out = ''
    for c, l in zip(cs, labs):
        c = F(c)
        if c == 0:
            continue
        t = l if abs(c) == 1 else f'{fx(abs(c))}{l}'
        out += (('-' if not out else ' - ') if c < 0 else (' + ' if out else '')) + t
    return out or '\\mathbf 0'


def coef(c):
    """Coefficient in front of a symbol: 1 -> '', -1 -> '-', else the number."""
    c = F(c)
    return '' if c == 1 else '-' if c == -1 else fx(c)


def vmat(B):
    return '\\begin{vmatrix}' + ' \\\\ '.join(' & '.join(fx(x) for x in r) for r in B) + '\\end{vmatrix}'


def par(x):
    """Parenthesise negative numbers."""
    return f'({fx(x)})' if F(x) < 0 else fx(x)


# ── linear systems ───────────────────────────────────────────────────
def chk_general(d):
    A, b, p, vs = sym(d['A']), sym([[x] for x in d['b']]), sym([[x] for x in d['p']]), [sym([[x] for x in v]) for v in d['vs']]
    need(A * p == b, 'particular solution')
    need(all(A * v == sp.zeros(A.rows, 1) for v in vs), 'homogeneous directions')
    need(len(vs) == A.cols - A.rank(), 'number of free parameters')
    need(not vs or sp.Matrix.hstack(*vs).rank() == len(vs), 'directions independent')


@template(course=C, chapter='linear_systems_and_echelon', id='m208-general-solution',
          title='General solution of a linear system (parametric vector form)',
          based_on={'exam': 'm208mid1Spr2025_SB', 'problem': 2}, check=chk_general)
def general_solution(rng):
    n = rng.choice([4, 4, 5])
    r = 3 if n == 5 else rng.choice([2, 3])
    R, _ = rref_pattern(rng, 3, n, r)
    A = scramble(rng, R)
    p = [rng.randint(-3, 3) for _ in range(n)]
    b = [sum(a * x for a, x in zip(row, p)) for row in A]
    if any(abs(v) > 30 for v in b):
        raise Reject
    names = xs(n)
    steps, Rr, piv = rref_steps(M([row + [v] for row, v in zip(A, b)]), bar=n)
    free = [j for j in range(n) if j not in piv]
    p0 = [F(0)] * n
    for i, c in enumerate(piv):
        p0[c] = Rr[i][n]
    vs = []
    for f in free:
        v = [F(0)] * n
        v[f] = F(1)
        for i, c in enumerate(piv):
            v[c] = -Rr[i][f]
        vs.append(v)
    eqs = []
    for i, c in enumerate(piv):
        rhs = fx(Rr[i][n])
        for f in free:
            k = -Rr[i][f]
            if k:
                rhs += (' - ' if k < 0 else ' + ') + (names[f] if abs(k) == 1 else f'{fx(abs(k))}{names[f]}')
        eqs.append(f'{names[c]} &= {rhs}')
    eqs += [f'{names[f]} &\\text{{ is free}}' for f in free]
    form = vec(p0) + ''.join(f' + {names[f]}{vec(v)}' for f, v in zip(free, vs))
    problem = (f'<p>Find the general solution of the system below by row reducing its augmented matrix to reduced '
               f'echelon form. Write your answer in parametric vector form.</p>{system(A, b, names)}')
    sol = (f'<p>Row reduce the augmented matrix:</p>{steps}'
           f'<p>The pivots are in columns {", ".join(str(c + 1) for c in piv)}, so the leading variables are '
           f'{", ".join("$" + names[c] + "$" for c in piv)} and the free variables are {", ".join("$" + names[f] + "$" for f in free)}. '
           f'Reading off each row:</p>\\[\\begin{{aligned}}{" \\\\ ".join(eqs)}\\end{{aligned}}\\]'
           f'<p>Collecting the constants and each free variable into vectors:</p>\\[\\mathbf x={form}\\]'
           f'<p><strong>Check:</strong> substituting the first vector gives $A\\mathbf x=\\mathbf b$, and each vector multiplying a free variable solves $A\\mathbf x=\\mathbf 0$.</p>')
    return {'problem': problem, 'answer': f'\\[\\mathbf x={form}\\]', 'solution': sol,
            'data': {'A': A, 'b': b, 'p': p0, 'vs': vs}}


def classify(A, b):
    A, Ab = sp.Matrix(A), sp.Matrix.hstack(sp.Matrix(A), sp.Matrix(b))
    if A.rank() < Ab.rank():
        return 'none'
    return 'one' if A.rank() == A.cols else 'many'


def chk_param(d):
    k = sp.Symbol('k')
    A, b = sp.Matrix(d['A']), sp.Matrix(d['b'])
    roots = set(sp.solve(sp.Eq(A.det(), 0), k))
    need(roots == set(d['none']) | set(d['many']), 'values where A is singular')
    for r in d['none']:
        need(classify(A.subs(k, r), b.subs(k, r)) == 'none', f'k={r} should be inconsistent')
    for r in d['many']:
        need(classify(A.subs(k, r), b.subs(k, r)) == 'many', f'k={r} should give infinitely many')
    for r in range(-8, 9):
        if r not in roots:
            need(classify(A.subs(k, r), b.subs(k, r)) == 'one', f'k={r} should give one solution')


@template(course=C, chapter='linear_systems_and_echelon', id='m208-parameter-k',
          title='For which k does a system have no, one, or infinitely many solutions?',
          based_on={'exam': 'm208mid1Spr2022_EP', 'problem': 1}, check=chk_param)
def parameter_k(rng):
    k = sp.Symbol('k')
    for _ in range(400):
        A = [[nz(rng, -3, 3) if rng.random() < 0.8 else 0 for _ in range(3)] for _ in range(3)]
        A[0][0] = 1
        (i1, j1), (i2, j2) = rng.choice([((1, 2), (2, 1)), ((1, 1), (2, 2)), ((2, 2), (1, 1)), ((1, 2), (2, 2))])
        A[i1][j1], A[i2][j2] = k, k
        b = [rng.randint(0, 3) * k + rng.randint(-3, 3) if rng.random() < 0.7 else rng.randint(-4, 4) for _ in range(3)]
        Am, bm = sp.Matrix(A), sp.Matrix(b)
        det = sp.factor(Am.det())
        roots = sp.solve(sp.Eq(Am.det(), 0), k)
        if sp.degree(Am.det(), k) != 2 or len(roots) != 2 or not all(r.is_integer and abs(r) <= 6 for r in roots):
            continue
        kinds = {r: classify(Am.subs(k, r), bm.subs(k, r)) for r in roots}
        if sorted(kinds.values()) != ['many', 'none']:
            continue
        break
    else:
        raise Reject
    none = [r for r in roots if kinds[r] == 'none']
    many = [r for r in roots if kinds[r] == 'many']
    names = ['x', 'y', 'z']
    eq = ' \\\\ '.join(_lin_sym(row, names) + f' &= {sp.latex(v)}' for row, v in zip(A, b))
    # cofactor expansion along the first row, kept symbolic in k
    terms, parts = [], []
    for j in range(3):
        a = Am[0, j]
        if a == 0:
            continue
        minor = Am.minor_submatrix(0, j)
        sign = (-1) ** j
        coef = sign * a
        terms.append(f'{"-" if coef < 0 else "+"}{"" if abs(coef) == 1 else abs(coef)}\\begin{{vmatrix}}{sp.latex(minor[0, 0])} & {sp.latex(minor[0, 1])}\\\\ {sp.latex(minor[1, 0])} & {sp.latex(minor[1, 1])}\\end{{vmatrix}}')
        parts.append(sign * a * sp.expand(minor.det()))
    expand = ' '.join(terms).lstrip('+')
    expanded = sp.expand(sum(parts))
    mid = ' + '.join(f'\\big({sp.latex(p)}\\big)' for p in parts)
    sol = [f'<p>A square system has exactly one solution exactly when its coefficient matrix is invertible, i.e. when $\\det A\\neq0$. '
           f'Expand along the first row:</p>\\[\\det A={expand}={mid}={sp.latex(expanded)}={sp.latex(det)}.\\]'
           f'<p>So there is exactly one solution unless $k={sp.latex(roots[0])}$ or $k={sp.latex(roots[1])}$. Check those two values by row reduction.</p>']
    for r in roots:
        aug = M([[int(Am[i, j].subs(k, r)) for j in range(3)] + [int(bm[i].subs(k, r))] for i in range(3)])
        steps, _, _ = rref_steps(aug, bar=3)
        verdict = ('the last row says $0=$ a nonzero number, so the system is <strong>inconsistent</strong> (no solutions).'
                   if kinds[r] == 'none' else
                   'there is no contradictory row and a column without a pivot, so there is a free variable: <strong>infinitely many solutions</strong>.')
        sol.append(f'<p><strong>$k={sp.latex(r)}$:</strong></p>{steps}<p>Here {verdict}</p>')
    answer = (f'<p>No solutions: $k={sp.latex(none[0])}$.<br>Exactly one solution: $k\\neq{sp.latex(roots[0])},\\ {sp.latex(roots[1])}$.<br>'
              f'Infinitely many solutions: $k={sp.latex(many[0])}$.</p>')
    problem = (f'<p>Consider the system</p>\\[\\begin{{aligned}}{eq}\\end{{aligned}}\\]'
               '<p>For which values of $k$ does the system have (a) no solutions, (b) exactly one solution, (c) infinitely many solutions?</p>')
    return {'problem': problem, 'answer': answer, 'solution': ''.join(sol),
            'data': {'A': A, 'b': b, 'none': none, 'many': many}}


def _lin_sym(row, names):
    out = ''
    for c, n in zip(row, names):
        if c == 0:
            continue
        if c == 1:
            t, neg = n, False
        elif c == -1:
            t, neg = n, True
        elif isinstance(c, sp.Basic) and not c.is_number:
            t, neg = f'{sp.latex(c)}{n}', False
        else:
            t, neg = f'{abs(int(c))}{n}', c < 0
        out += (' - ' if neg else (' + ' if out else '')) + t
    return out


# ── inverse ──────────────────────────────────────────────────────────
def chk_inverse(d):
    A = sp.Matrix(d['A'])
    need(A.inv() == sym(d['Ainv']), 'inverse')
    need(A * sym([[x] for x in d['x']]) == sp.Matrix(d['b']), 'solution of Ax=b')


@template(course=C, chapter='matrix_operations_and_inverse', id='m208-inverse',
          title='Find a 3×3 inverse by row reduction and use it to solve a system',
          based_on={'exam': 'm208mid2Aut2023_TD', 'problem': 3}, check=chk_inverse)
def inverse(rng):
    A = rand_unimodular(rng, 3, maxent=5)
    I = [[int(i == j) for j in range(3)] for i in range(3)]
    steps, R, _ = rref_steps(M([a + e for a, e in zip(A, I)]), bar=3)
    Ainv = [row[3:] for row in R]
    if any(abs(x) > 15 for r in Ainv for x in r):
        raise Reject
    b = [rng.randint(-5, 5) for _ in range(3)]
    x = [sum(a * v for a, v in zip(row, b)) for row in Ainv]
    prod = ' \\\\ '.join(' + '.join(f'{par(a)}{par(v)}' for a, v in zip(row, b)) for row in Ainv)
    problem = (f'<p>Let</p>\\[A={mat(A)},\\qquad \\mathbf b={vec(b)}.\\]'
               '<p>(a) Find $A^{-1}$ by row reducing $[\\,A\\mid I\\,]$.<br>(b) Use $A^{-1}$ to solve $A\\mathbf x=\\mathbf b$.</p>')
    sol = (f'<p><strong>(a)</strong> Row reduce $[\\,A\\mid I\\,]$:</p>{steps}'
           f'<p>The left block is now $I$, so the right block is the inverse:</p>\\[A^{{-1}}={mat(Ainv)}.\\]'
           f'<p><strong>(b)</strong> $\\mathbf x=A^{{-1}}\\mathbf b$:</p>\\[\\mathbf x={mat(Ainv)}{vec(b)}=\\begin{{bmatrix}}{prod}\\end{{bmatrix}}={vec(x)}.\\]'
           f'<p><strong>Check:</strong> $A\\mathbf x={vec([r[0] for r in mul(A, [[v] for v in x])])}=\\mathbf b$.</p>')
    return {'problem': problem, 'answer': f'\\[A^{{-1}}={mat(Ainv)},\\qquad \\mathbf x={vec(x)}\\]', 'solution': sol,
            'data': {'A': A, 'Ainv': Ainv, 'b': b, 'x': x}}


# ── determinants ─────────────────────────────────────────────────────
def expand_line(A):
    """Pick the row or column with the most zeros. Returns ('row'|'col', index)."""
    n = len(A)
    best = max([('row', i, sum(x == 0 for x in A[i])) for i in range(n)] +
               [('col', j, sum(A[i][j] == 0 for i in range(n))) for j in range(n)], key=lambda t: t[2])
    return best[0], best[1]


def minor(A, i, j):
    return [[A[r][c] for c in range(len(A)) if c != j] for r in range(len(A)) if r != i]


def det3_steps(B):
    """Cofactor expansion of a 3×3 determinant, with the 2×2 determinants written out."""
    kind, k = expand_line(B)
    terms, nums, total = [], [], 0
    for t in range(3):
        i, j = (k, t) if kind == 'row' else (t, k)
        a = B[i][j]
        if a == 0:
            continue
        m2 = minor(B, i, j)
        d2 = m2[0][0] * m2[1][1] - m2[0][1] * m2[1][0]
        s = (-1) ** (i + j)
        terms.append(f'{"-" if s * a < 0 else "+"}{abs(a) if abs(a) != 1 else ""}\\begin{{vmatrix}}{m2[0][0]}&{m2[0][1]}\\\\{m2[1][0]}&{m2[1][1]}\\end{{vmatrix}}')
        nums.append(f'{"-" if s * a < 0 else "+"}{abs(a)}\\,({two_by_two(*m2[0], *m2[1])})')
        total += s * a * d2
    line = f'{"row" if kind == "row" else "column"} {k + 1}'
    if not terms:
        return line, '0', '0', 0
    return line, ' '.join(terms).lstrip('+'), ' '.join(nums).lstrip('+'), total


def chk_det(d):
    need(sp.Matrix(d['A']).det() == d['det'], 'determinant')


@template(course=C, chapter='determinants', id='m208-det-cofactor',
          title='A 4×4 determinant by cofactor expansion',
          based_on={'exam': 'm208finalSpr2022_HR', 'problem': 1}, check=chk_det)
def det_cofactor(rng):
    A = [[rng.randint(-3, 4) for _ in range(4)] for _ in range(4)]
    r = rng.randrange(4)
    zs = rng.sample(range(4), 2)
    for j in zs:
        A[r][j] = 0
    if any(A[r][j] == 0 for j in range(4) if j not in zs):
        raise Reject
    for i in range(4):
        if i != r and rng.random() < 0.35:
            A[i][rng.randrange(4)] = 0
    if rng.random() < 0.5:
        A = [list(c) for c in zip(*A)]
    D = det_rows(A)
    if D == 0 or abs(D) > 200:
        raise Reject
    kind, k = expand_line(A)
    parts, subs, total = [], [], 0
    for t in range(4):
        i, j = (k, t) if kind == 'row' else (t, k)
        a = A[i][j]
        if a == 0:
            continue
        s = (-1) ** (i + j)
        B = minor(A, i, j)
        line, sym3, nums3, d3 = det3_steps(B)
        total += s * a * d3
        parts.append((s, a, B, d3))
        subs.append(f'<p>$M_{{{i + 1}{j + 1}}}$: expand along {line}:</p>'
                    f'\\[{vmat(B)}={sym3}={nums3}={d3}.\\]')
    need(total == D, 'cofactor expansion disagrees with the determinant')
    first, short = [], []
    for t in range(4):
        i, j = (k, t) if kind == 'row' else (t, k)
        if A[i][j] == 0:
            continue
        s, a = (-1) ** (i + j), A[i][j]
        first.append(f'{par(a)}\\cdot(-1)^{{{i + 1}+{j + 1}}}M_{{{i + 1}{j + 1}}}')
        short.append(f'{"-" if s * a < 0 else "+"}{abs(a) if abs(a) != 1 else ""}\\,M_{{{i + 1}{j + 1}}}')
    final = ' '.join(f'{"-" if s * a < 0 else "+"}{abs(a)}({d3})' for s, a, _, d3 in parts).lstrip('+')
    line = f'{"row" if kind == "row" else "column"} {k + 1}'
    problem = f'<p>Compute the determinant of</p>\\[A={mat(A)}.\\]'
    sol = (f'<p>Expand along {line}, which has the most zeros. With $M_{{ij}}$ the determinant left after deleting row $i$ and column $j$, '
           f'and cofactor signs $(-1)^{{i+j}}$:</p>\\[\\det A={" + ".join(first)}={" ".join(short).lstrip("+")}.\\]' + ''.join(subs) +
           f'<p>So</p>\\[\\det A={final}={D}.\\]')
    return {'problem': problem, 'answer': f'$\\det A={D}$', 'solution': sol, 'data': {'A': A, 'det': D}}


def chk_det_props(d):
    A = sp.Matrix(d['A'])
    need(A.det() == d['detA'], 'det A')
    cols = [A[:, j] for j in range(3)]
    p, k, m = d['perm'], d['k'], d['m']
    B = sp.Matrix.hstack(k * cols[p[0]], cols[p[1]], cols[p[2]] + m * cols[p[0]])
    need(B.det() == d['detB'], 'det B')
    need((d['c'] * A.inv() * B.T).det() == d['det2'], 'det(cA^{-1}B^T)')


@template(course=C, chapter='determinants', id='m208-det-properties',
          title='Determinants from column operations and products',
          based_on={'exam': 'm208finalWin2024_YZ', 'problem': 8}, check=chk_det_props)
def det_properties(rng):
    d = nz(rng, -6, 6)
    perm = rng.choice([p for p in permutations(range(3))])
    k = rng.choice([-3, -2, 2, 3, 4])
    m = nz(rng, -3, 3)
    c = rng.choice([-2, 2, 3])
    sgn = sp.Matrix([[int(perm[i] == j) for j in range(3)] for i in range(3)]).det()
    detB = k * sgn * d
    det2 = sp.Rational(c ** 3 * detB, d)
    # a concrete A with det A = d, used only by the check
    U = rand_unimodular(rng, 3, maxent=4)
    if det_rows(U) == -1:
        U[0] = [-x for x in U[0]]
    U[0] = [d * x for x in U[0]]
    lab = ['\\mathbf a_1', '\\mathbf a_2', '\\mathbf a_3']
    c3 = f'{lab[perm[2]]}{" + " if m > 0 else " - "}{"" if abs(m) == 1 else abs(m)}{lab[perm[0]]}'
    swaps = {1: 'an even number of swaps (or none)', -1: 'one swap'}[int(sgn)]
    problem = (f'<p>$A=[\\,\\mathbf a_1\\ \\mathbf a_2\\ \\mathbf a_3\\,]$ is a $3\\times3$ matrix with $\\det A={d}$. Let</p>'
               f'\\[B=\\big[\\ {k}{lab[perm[0]]}\\quad {lab[perm[1]]}\\quad {c3}\\ \\big].\\]'
               f'<p>(a) Find $\\det B$.<br>(b) Find $\\det\\!\\big({c}A^{{-1}}B^{{T}}\\big)$.</p>')
    sol = (f'<p><strong>(a)</strong> Build $B$ from $A$ one column operation at a time.</p><ul>'
           f'<li>Reordering the columns to ${lab[perm[0]]},\\ {lab[perm[1]]},\\ {lab[perm[2]]}$ takes {swaps}, multiplying the determinant by ${int(sgn)}$: it becomes ${int(sgn) * d}$.</li>'
           f'<li>Adding ${m}$ times column 1 to column 3 does not change the determinant.</li>'
           f'<li>Multiplying column 1 by ${k}$ multiplies the determinant by ${k}$.</li></ul>'
           f'\\[\\det B={k}\\cdot({int(sgn)})\\cdot({d})={detB}.\\]'
           f'<p><strong>(b)</strong> For $3\\times3$ matrices $\\det(cM)=c^3\\det M$, $\\det(A^{{-1}})=1/\\det A$ and $\\det(B^T)=\\det B$:</p>'
           f'\\[\\det\\!\\big({c}A^{{-1}}B^{{T}}\\big)=({c})^3\\cdot\\frac{{1}}{{{d}}}\\cdot({detB})={sp.latex(det2)}.\\]')
    return {'problem': problem, 'answer': f'(a) $\\det B={detB}$ &nbsp; (b) ${sp.latex(det2)}$', 'solution': sol,
            'data': {'A': U, 'detA': d, 'perm': perm, 'k': k, 'm': m, 'c': c, 'detB': detB, 'det2': det2}}


# ── subspaces, independence, bases ───────────────────────────────────
def chk_nul_col(d):
    A = sp.Matrix(d['A'])
    nul = [sym([[x] for x in v]) for v in d['nul']]
    need(all(A * v == sp.zeros(A.rows, 1) for v in nul), 'Nul vectors')
    need(len(nul) == A.cols - A.rank() and (not nul or sp.Matrix.hstack(*nul).rank() == len(nul)), 'Nul basis size')
    cols = [A[:, j] for j in d['pivots']]
    need(len(cols) == A.rank() and sp.Matrix.hstack(*cols).rank() == A.rank(), 'Col basis')


@template(course=C, chapter='vector_spaces_and_subspaces', id='m208-nul-col',
          title='Bases for the null space and column space',
          based_on={'exam': 'm208mid2Spr2025_SB', 'problem': 2}, check=chk_nul_col)
def nul_col(rng):
    n = rng.choice([4, 5, 5])
    r = rng.choice([2, 3]) if n == 5 else 2
    R, _ = rref_pattern(rng, 3, n, r)
    A = scramble(rng, R)
    steps, Rr, piv = rref_steps(M(A))
    basis, free = nullspace(Rr, piv, n)
    names = xs(n)
    eqs = []
    for i, c in enumerate(piv):
        rhs = ''
        for f in free:
            k = -Rr[i][f]
            if k:
                rhs += (' - ' if k < 0 else (' + ' if rhs else '')) + (names[f] if abs(k) == 1 else f'{fx(abs(k))}{names[f]}')
        eqs.append(f'{names[c]} &= {rhs or "0"}')
    col = ',\\ '.join(vec([A[i][c] for i in range(3)]) for c in piv)
    nulb = ',\\ '.join(vec(v) for v in basis)
    problem = f'<p>Let</p>\\[A={mat(A)}.\\]<p>Find a basis for $\\operatorname{{Nul}}A$ and a basis for $\\operatorname{{Col}}A$, and state the dimension of each.</p>'
    sol = (f'<p>Row reduce $A$:</p>{steps}'
           f'<p><strong>Column space.</strong> The pivots are in columns {", ".join(str(c + 1) for c in piv)}, so those columns <em>of the original $A$</em> form a basis:</p>'
           f'\\[\\operatorname{{Col}}A=\\operatorname{{span}}\\left\\{{{col}\\right\\}},\\qquad \\dim\\operatorname{{Col}}A={len(piv)}.\\]'
           f'<p><strong>Null space.</strong> Solve $A\\mathbf x=\\mathbf 0$ from the reduced form, with {", ".join("$" + names[f] + "$" for f in free)} free:</p>'
           f'\\[\\begin{{aligned}}{" \\\\ ".join(eqs)}\\end{{aligned}}\\]'
           f'<p>Setting each free variable to 1 in turn (the others 0) gives one basis vector each:</p>'
           f'\\[\\operatorname{{Nul}}A=\\operatorname{{span}}\\left\\{{{nulb}\\right\\}},\\qquad \\dim\\operatorname{{Nul}}A={len(basis)}.\\]'
           f'<p><strong>Check:</strong> $\\dim\\operatorname{{Col}}A+\\dim\\operatorname{{Nul}}A={len(piv)}+{len(basis)}={n}$, the number of columns.</p>')
    answer = (f'\\[\\operatorname{{Nul}}A:\\ \\left\\{{{nulb}\\right\\}}\\ (\\dim {len(basis)}),\\qquad '
              f'\\operatorname{{Col}}A:\\ \\left\\{{{col}\\right\\}}\\ (\\dim {len(piv)})\\]')
    return {'problem': problem, 'answer': answer, 'solution': sol, 'data': {'A': A, 'nul': basis, 'pivots': piv}}


def chk_indep(d):
    V = sp.Matrix(d['V'])
    need((V.rank() == V.cols) == d['independent'], 'independence')
    if not d['independent']:
        rel = sym([[x] for x in d['rel']])
        need(any(x != 0 for x in d['rel']) and V * rel == sp.zeros(V.rows, 1), 'dependence relation')


@template(course=C, chapter='linear_independence_and_basis', id='m208-independence',
          title='Linear independence and a dependence relation',
          based_on={'exam': 'm208finalWin2019_RG', 'problem': 1}, check=chk_indep)
def independence(rng):
    v1 = [rng.randint(-3, 3) for _ in range(4)]
    v2 = [rng.randint(-3, 3) for _ in range(4)]
    dep = rng.random() < 0.6
    if dep:
        a, b = nz(rng, -3, 3), nz(rng, -3, 3)
        v3 = [a * x + b * y for x, y in zip(v1, v2)]
    else:
        v3 = [rng.randint(-4, 4) for _ in range(4)]
    V = [[v1[i], v2[i], v3[i]] for i in range(4)]
    rank = sp.Matrix(V).rank()
    if (dep and rank != 2) or (not dep and rank != 3) or any(abs(x) > 12 for r in V for x in r):
        raise Reject
    steps, R, piv = rref_steps(M(V))
    lab = ['\\mathbf v_1', '\\mathbf v_2', '\\mathbf v_3']
    problem = (f'<p>Let</p>\\[\\mathbf v_1={vec(v1)},\\quad \\mathbf v_2={vec(v2)},\\quad \\mathbf v_3={vec(v3)}.\\]'
               '<p>Is $\\{\\mathbf v_1,\\mathbf v_2,\\mathbf v_3\\}$ linearly independent? If not, find a linear dependence relation among them.</p>')
    sol = f'<p>The vectors are independent exactly when $[\\,\\mathbf v_1\\ \\mathbf v_2\\ \\mathbf v_3\\,]\\mathbf c=\\mathbf 0$ has only the trivial solution. Row reduce:</p>{steps}'
    if not dep:
        sol += '<p>Every column has a pivot, so there are no free variables and only $\\mathbf c=\\mathbf 0$ works: the set is <strong>linearly independent</strong>.</p>'
        return {'problem': problem, 'answer': '<p>Yes, linearly independent.</p>', 'solution': sol,
                'data': {'V': V, 'independent': True}}
    a, b = R[0][2], R[1][2]
    rel = [-a, -b, F(1)]
    rel_tex = combo_tex([-a, -b, 1], lab)
    expr = combo_tex([a, b], lab[:2])
    sol += (f'<p>Column 3 has no pivot, so $c_3$ is free and the set is <strong>linearly dependent</strong>. '
            f'The reduced form says $c_1={coef(-a)}c_3$ and $c_2={coef(-b)}c_3$. Taking $c_3=1$:</p>'
            f'\\[{rel_tex}=\\mathbf 0,\\qquad\\text{{i.e.}}\\quad {lab[2]}={expr}.\\]'
            f'<p><strong>Check:</strong> ${expr}={vec([a * x + b * y for x, y in zip(v1, v2)])}={lab[2]}$.</p>')
    return {'problem': problem, 'answer': f'<p>No, dependent: ${lab[2]}={expr}$.</p>', 'solution': sol,
            'data': {'V': V, 'independent': False, 'rel': rel}}


def chk_coords(d):
    P, x = sp.Matrix(d['P']), sp.Matrix(d['x'])
    need(P.det() != 0, 'basis')
    need(P.solve(x) == sym([[v] for v in d['c']]), 'coordinates')


@template(course=C, chapter='linear_independence_and_basis', id='m208-coordinates',
          title='Coordinates relative to a basis',
          based_on={'exam': 'm208finalWin2019_RG', 'problem': 3}, check=chk_coords)
def coordinates(rng):
    n = rng.choice([2, 3, 3])
    P = rand_unimodular(rng, n, maxent=4)
    c = [nz(rng, -4, 4) for _ in range(n)]
    x = [sum(P[i][j] * c[j] for j in range(n)) for i in range(n)]
    if any(abs(v) > 20 for v in x):
        raise Reject
    bs = [[P[i][j] for i in range(n)] for j in range(n)]
    steps, R, _ = rref_steps(M([P[i] + [x[i]] for i in range(n)]), bar=n)
    names = ',\\ '.join(f'\\mathbf b_{j + 1}={vec(b)}' for j, b in enumerate(bs))
    combo = ' + '.join(f'({c[j]}){vec(bs[j])}' for j in range(n))
    problem = (f'<p>$\\mathcal B=\\{{{",".join(f"\\mathbf b_{j + 1}" for j in range(n))}\\}}$ is a basis of $\\mathbb R^{n}$, where</p>'
               f'\\[{names}.\\]<p>Find the coordinate vector $[\\mathbf x]_{{\\mathcal B}}$ of $\\mathbf x={vec(x)}$.</p>')
    sol = (f'<p>$[\\mathbf x]_{{\\mathcal B}}$ holds the weights $c_j$ with $c_1\\mathbf b_1+\\dots+c_{n}\\mathbf b_{n}=\\mathbf x$. Row reduce $[\\,\\mathbf b_1\\ \\cdots\\ \\mathbf b_{n}\\mid\\mathbf x\\,]$:</p>{steps}'
           f'\\[[\\mathbf x]_{{\\mathcal B}}={vec(c)}.\\]<p><strong>Check:</strong> ${combo}={vec(x)}=\\mathbf x$.</p>')
    return {'problem': problem, 'answer': f'$[\\mathbf x]_{{\\mathcal B}}={vec(c)}$', 'solution': sol,
            'data': {'P': P, 'x': x, 'c': c}}


# ── linear transformations ───────────────────────────────────────────
def chk_images(d):
    U, W = sp.Matrix(d['U']), sp.Matrix(d['W'])
    A = W * U.inv()
    need(A == sym(d['A']), 'standard matrix')
    need(A * sp.Matrix(d['x']) == sym([[v] for v in d['Tx']]), 'T(x)')


@template(course=C, chapter='linear_transformations', id='m208-matrix-from-images',
          title='The standard matrix of T from the images of two vectors',
          based_on={'exam': 'm208finalWin2019_RG', 'problem': 5}, check=chk_images)
def matrix_from_images(rng):
    m = rng.choice([2, 2, 3])
    A = [[rng.randint(-3, 3) for _ in range(2)] for _ in range(m)]
    U = [[nz(rng, -3, 3) for _ in range(2)] for _ in range(2)]
    dU = U[0][0] * U[1][1] - U[0][1] * U[1][0]
    if dU == 0 or abs(dU) > 5 or all(x == 0 for r in A for x in r):
        raise Reject
    W = mul(A, U)
    x = [rng.randint(-4, 4) for _ in range(2)]
    Tx = [sum(a * v for a, v in zip(row, x)) for row in A]
    u = [[U[0][j], U[1][j]] for j in range(2)]
    w = [[W[i][j] for i in range(m)] for j in range(2)]
    adj = [[U[1][1], -U[0][1]], [-U[1][0], U[0][0]]]
    WA = mul(W, adj)
    space = f'\\mathbb R^{m}'
    problem = (f'<p>$T:\\mathbb R^2\\to {space}$ is a linear transformation with</p>'
               f'\\[T\\left({vec(u[0])}\\right)={vec(w[0])},\\qquad T\\left({vec(u[1])}\\right)={vec(w[1])}.\\]'
               f'<p>(a) Find the standard matrix $A$ of $T$.<br>(b) Find $T\\left({vec(x)}\\right)$.</p>')
    sol = (f'<p><strong>(a)</strong> Put the inputs and outputs side by side as columns: $A{mat(U)}={mat(W)}$. '
           f'The input matrix has determinant ${two_by_two(U[0][0], U[0][1], U[1][0], U[1][1])}={dU}\\neq0$, so it is invertible:</p>'
           f'\\[{mat(U)}^{{-1}}=\\frac{{1}}{{{dU}}}{mat(adj)},\\qquad A={mat(W)}\\cdot\\frac{{1}}{{{dU}}}{mat(adj)}=\\frac{{1}}{{{dU}}}{mat(WA)}={mat(A)}.\\]'
           f'<p><strong>Check:</strong> $A{vec(u[0])}={vec(w[0])}$ and $A{vec(u[1])}={vec(w[1])}$.</p>'
           f'<p><strong>(b)</strong></p>\\[T\\left({vec(x)}\\right)={mat(A)}{vec(x)}={vec(Tx)}.\\]')
    return {'problem': problem, 'answer': f'(a) $A={mat(A)}$ &nbsp; (b) ${vec(Tx)}$', 'solution': sol,
            'data': {'U': U, 'W': W, 'A': A, 'x': x, 'Tx': Tx}}


def chk_onto(d):
    A = sp.Matrix(d['A'])
    need((A.rank() == A.cols) == d['one_to_one'], 'one-to-one')
    need((A.rank() == A.rows) == d['onto'], 'onto')


@template(course=C, chapter='linear_transformations', id='m208-one-to-one-onto',
          title='Is T(x) = Ax one-to-one? Onto?',
          based_on={'exam': 'm208mid2Spr2025_SB', 'problem': 4}, check=chk_onto)
def one_to_one_onto(rng):
    m, n = rng.choice([(2, 3), (3, 2), (3, 3), (3, 3), (3, 4), (4, 3)])
    r = rng.choice([x for x in range(1, min(m, n) + 1) if x >= min(m, n) - 1])
    if r == 1:
        raise Reject
    R, _ = rref_pattern(rng, m, n, r)
    A = scramble(rng, R)
    steps, Rr, piv = rref_steps(M(A))
    one, onto = len(piv) == n, len(piv) == m
    problem = (f'<p>Let $T:\\mathbb R^{n}\\to\\mathbb R^{m}$ be $T(\\mathbf x)=A\\mathbf x$, where</p>\\[A={mat(A)}.\\]'
               '<p>(a) Is $T$ one-to-one? (b) Is $T$ onto? Justify both answers.</p>')
    sol = (f'<p>Row reduce $A$:</p>{steps}<p>There are {len(piv)} pivots (columns {", ".join(str(c + 1) for c in piv)}).</p>'
           f'<p><strong>(a)</strong> $T$ is one-to-one exactly when every column of $A$ has a pivot (no free variables in $A\\mathbf x=\\mathbf 0$). '
           + (f'All {n} columns have pivots, so $T$ <strong>is one-to-one</strong>.' if one else
              f'Only {len(piv)} of the {n} columns have pivots, so $A\\mathbf x=\\mathbf 0$ has a free variable and $T$ is <strong>not one-to-one</strong>.')
           + f'</p><p><strong>(b)</strong> $T$ is onto $\\mathbb R^{m}$ exactly when every row of $A$ has a pivot. '
           + (f'All {m} rows have pivots, so $T$ <strong>is onto</strong>.' if onto else
              f'Only {len(piv)} of the {m} rows have pivots (the reduced form has a zero row), so $T$ is <strong>not onto</strong>.') + '</p>')
    return {'problem': problem, 'answer': f'(a) {"Yes" if one else "No"} &nbsp; (b) {"Yes" if onto else "No"} ({len(piv)} pivots, ${m}\\times{n}$ matrix)',
            'solution': sol, 'data': {'A': A, 'one_to_one': one, 'onto': onto}}


# ── eigenvalues ──────────────────────────────────────────────────────
def charpoly_tex(vals):
    lam = sp.Symbol('lambda')
    return sp.latex(sp.expand(sp.prod([lam - v for v in vals]))), ''.join(f'(\\lambda{"-" if v >= 0 else "+"}{abs(v)})' if v else '\\lambda' for v in vals)


def chk_diag(d):
    A, P, D = sp.Matrix(d['A']), sym(d['P']), sp.diag(*d['vals'])
    need(P.det() != 0, 'P invertible')
    need(A * P == P * D, 'AP = PD')
    lam = sp.Symbol('lambda')
    need(sp.Poly(A.charpoly(lam).as_expr(), lam) == sp.Poly(sp.prod([lam - v for v in d['vals']]), lam), 'characteristic polynomial')


@template(course=C, chapter='eigenvalues_and_diagonalization', id='m208-diagonalize-2x2',
          title='Diagonalize a 2×2 matrix',
          based_on={'exam': 'm208finalWin2019_RG', 'problem': 7}, check=chk_diag)
def diagonalize2(rng):
    l1, l2 = sorted(rng.sample(range(-4, 6), 2))
    P = rand_unimodular(rng, 2, maxent=3)
    Pinv = [[F(x) for x in r] for r in sp.Matrix(P).inv().tolist()]
    A = mul(mul(M(P), M([[l1, 0], [0, l2]])), Pinv)
    if any(abs(x) > 12 or x.denominator != 1 for r in A for x in r):
        raise Reject
    tr, dt = A[0][0] + A[1][1], A[0][0] * A[1][1] - A[0][1] * A[1][0]
    lam = sp.Symbol('lambda')
    poly = sp.latex(sp.expand((A[0][0] - lam) * (A[1][1] - lam) - A[0][1] * A[1][0]).subs({}))
    blocks, vecs = [], []
    for l in (l1, l2):
        B = [[A[0][0] - l, A[0][1]], [A[1][0], A[1][1] - l]]
        steps, R, piv = rref_steps(B)
        (v,), _ = nullspace(R, piv, 2)
        vecs.append(v)
        blocks.append(f'<p>$\\lambda={l}$: row reduce $A-({l})I$:</p>{steps}<p>so an eigenvector is $\\mathbf v={vec(v)}$.</p>')
    Pm = [[vecs[0][0], vecs[1][0]], [vecs[0][1], vecs[1][1]]]
    a, b, c, d = (int(A[0][0]), int(A[0][1]), int(A[1][0]), int(A[1][1]))
    problem = f'<p>Diagonalize</p>\\[A={mat(A)},\\]<p>that is, find an invertible $P$ and a diagonal $D$ with $A=PDP^{{-1}}$.</p>'
    sol = (f'<p><strong>Eigenvalues.</strong></p>\\[\\det(A-\\lambda I)=\\begin{{vmatrix}}{a}-\\lambda & {b}\\\\ {c} & {d}-\\lambda\\end{{vmatrix}}'
           f'=({a}-\\lambda)({d}-\\lambda)-({b})({c})={poly}=(\\lambda{"-" if l1 >= 0 else "+"}{abs(l1)})(\\lambda{"-" if l2 >= 0 else "+"}{abs(l2)}),\\]'
           f'<p>so $\\lambda={l1}$ and $\\lambda={l2}$ (check: they add to $\\operatorname{{tr}}A={tr}$ and multiply to $\\det A={dt}$).</p>'
           f'<p><strong>Eigenvectors.</strong></p>{"".join(blocks)}'
           f'<p>Two distinct eigenvalues give two independent eigenvectors, so $A$ is diagonalizable. Put the eigenvectors in $P$ and the matching eigenvalues in $D$:</p>'
           f'\\[P={mat(Pm)},\\qquad D={mat([[l1, 0], [0, l2]])}.\\]'
           f'<p><strong>Check:</strong> $AP={mat(mul(A, M(Pm)))}=PD$.</p>')
    return {'problem': problem, 'answer': f'$P={mat(Pm)},\\ D={mat([[l1, 0], [0, l2]])}$ (columns of $P$ may be scaled or both swapped with $D$)',
            'solution': sol, 'data': {'A': A, 'P': Pm, 'vals': [l1, l2]}}


def chk_eig3(d):
    A = sp.Matrix(d['A'])
    ev = {val: (mult, len(vs)) for val, mult, vs in A.eigenvects()}
    need(set(ev) == set(d['spaces']), 'eigenvalues')
    for val, basis in d['spaces'].items():
        need(ev[val][1] == len(basis), f'dim of eigenspace {val}')
        need(ev[val][0] == d['mult'][val], f'multiplicity of {val}')
        for v in basis:
            x = sym([[t] for t in v])
            need(A * x == val * x, 'eigenvector')
    need(A.is_diagonalizable() == d['diag'], 'diagonalizable')


@template(course=C, chapter='eigenvalues_and_diagonalization', id='m208-eigen-3x3',
          title='Eigenvalues and eigenspaces of a 3×3 matrix; is it diagonalizable?',
          based_on={'exam': 'm208finalWin2019_RG', 'problem': 8}, check=chk_eig3)
def eigen3(rng):
    m1, m2 = rng.sample(range(-3, 5), 2)
    Q = rand_unimodular(rng, 2, maxent=3)
    Qi = [[F(x) for x in r] for r in sp.Matrix(Q).inv().tolist()]
    B = mul(mul(M(Q), M([[m1, 0], [0, m2]])), Qi)
    a = rng.choice([m1, m2]) if rng.random() < 0.45 else rng.choice([x for x in range(-3, 5) if x not in (m1, m2)])
    p, q = rng.randint(-3, 3), rng.randint(-3, 3)
    A = [[F(a), F(p), F(q)], [F(0), B[0][0], B[0][1]], [F(0), B[1][0], B[1][1]]]
    if any(x.denominator != 1 or abs(x) > 9 for r in A for x in r):
        raise Reject
    vals = sorted({a, m1, m2})
    mult = {v: [a, m1, m2].count(v) for v in vals}
    lam = sp.Symbol('lambda')
    Bp = sp.expand((B[0][0] - lam) * (B[1][1] - lam) - B[0][1] * B[1][0])
    spaces, blocks = {}, []
    for v in vals:
        Mv = [[A[i][j] - (v if i == j else 0) for j in range(3)] for i in range(3)]
        steps, R, piv = rref_steps(Mv)
        basis, _ = nullspace(R, piv, 3)
        spaces[v] = basis
        blocks.append(f'<p>$\\lambda={v}$ (multiplicity {mult[v]}): row reduce $A-({v})I$:</p>{steps}'
                      f'<p>{3 - len(piv)} free variable{"s" if 3 - len(piv) > 1 else ""}, so a basis of the eigenspace is '
                      f'$\\left\\{{{",".join(vec(b) for b in basis)}\\right\\}}$.</p>')
    diag = sum(len(b) for b in spaces.values()) == 3
    fac = ''.join(f'(\\lambda{"-" if v >= 0 else "+"}{abs(v)})' + (f'^{mult[v]}' if mult[v] > 1 else '') for v in vals)
    problem = (f'<p>Let</p>\\[A={mat(A)}.\\]<p>(a) Find the eigenvalues of $A$ and their algebraic multiplicities.<br>'
               '(b) Find a basis for each eigenspace.<br>(c) Is $A$ diagonalizable? Explain.</p>')
    sol = (f'<p><strong>(a)</strong> Expand $\\det(A-\\lambda I)$ along the first column (only its top entry is nonzero):</p>'
           f'\\[\\det(A-\\lambda I)=({a}-\\lambda)\\begin{{vmatrix}}{fx(B[0][0])}-\\lambda & {fx(B[0][1])}\\\\ {fx(B[1][0])} & {fx(B[1][1])}-\\lambda\\end{{vmatrix}}'
           f'=({a}-\\lambda)\\big({sp.latex(Bp)}\\big)=-{fac}.\\]'
           f'<p>The eigenvalues are {", ".join(f"${v}$" + (f" (multiplicity {mult[v]})" if mult[v] > 1 else "") for v in vals)}.</p>'
           f'<p><strong>(b)</strong></p>{"".join(blocks)}'
           f'<p><strong>(c)</strong> ' + (f'The eigenspace dimensions add up to $3$, so $A$ has three independent eigenvectors and <strong>is diagonalizable</strong>.'
                                         if diag else
                                         f'The eigenspace dimensions add up to only {sum(len(b) for b in spaces.values())} &lt; 3 '
                                         f'(the repeated eigenvalue has a 1-dimensional eigenspace), so $A$ is <strong>not diagonalizable</strong>.') + '</p>')
    answer = ('<p>' + '; '.join(f'$\\lambda={v}$' + (f' (mult. {mult[v]})' if mult[v] > 1 else '') + f': $\\left\\{{{",".join(vec(b) for b in spaces[v])}\\right\\}}$' for v in vals)
              + f'. {"Diagonalizable." if diag else "Not diagonalizable."}</p>')
    return {'problem': problem, 'answer': answer, 'solution': sol,
            'data': {'A': A, 'spaces': spaces, 'mult': mult, 'diag': diag}}


def chk_power(d):
    A, x0 = sp.Matrix(d['A']), sp.Matrix(d['x0'])
    for v, l in zip(d['vs'], d['vals']):
        need(A * sp.Matrix(v) == l * sp.Matrix(v), 'eigenpair')
    need(A ** d['k'] * x0 == sp.Matrix(d['Akx']), 'A^k x0')
    n = sp.Symbol('n')
    for t in range(0, 7):
        need(A ** t * x0 == sp.Matrix(d['formula']).subs(n, t), 'general formula')


@template(course=C, chapter='eigenvalues_and_diagonalization', id='m208-matrix-power',
          title='Use eigenvectors to compute Aᵏx',
          based_on={'exam': 'm208finalSpr2022_HR', 'problem': 9}, check=chk_power)
def matrix_power(rng):
    l1, l2 = rng.sample([-2, -1, 2, 3, 1, 4], 2)
    P = rand_unimodular(rng, 2, maxent=3)
    v1, v2 = [P[0][0], P[1][0]], [P[0][1], P[1][1]]
    A = mul(mul(M(P), M([[l1, 0], [0, l2]])), [[F(x) for x in r] for r in sp.Matrix(P).inv().tolist()])
    if any(abs(x) > 12 for r in A for x in r):
        raise Reject
    c1, c2 = nz(rng, -3, 3), nz(rng, -3, 3)
    x0 = [c1 * a + c2 * b for a, b in zip(v1, v2)]
    k = rng.choice([3, 4, 5])
    Akx = [c1 * l1 ** k * a + c2 * l2 ** k * b for a, b in zip(v1, v2)]
    n = sp.Symbol('n')
    formula = [c1 * sp.Integer(l1) ** n * a + c2 * sp.Integer(l2) ** n * b for a, b in zip(v1, v2)]
    Av1, Av2 = [l1 * x for x in v1], [l2 * x for x in v2]
    steps, R, _ = rref_steps(M([[v1[0], v2[0], x0[0]], [v1[1], v2[1], x0[1]]]), bar=2)
    pw = lambda l: f'({l})^{{n}}' if l < 0 else f'{l}^{{n}}'
    problem = (f'<p>Let</p>\\[A={mat(A)},\\qquad \\mathbf v_1={vec(v1)},\\quad \\mathbf v_2={vec(v2)},\\quad \\mathbf x={vec(x0)}.\\]'
               f'<p>(a) Show that $\\mathbf v_1$ and $\\mathbf v_2$ are eigenvectors of $A$ and find their eigenvalues.<br>'
               f'(b) Write $\\mathbf x$ as a combination of $\\mathbf v_1$ and $\\mathbf v_2$.<br>(c) Find $A^{{{k}}}\\mathbf x$, and a formula for $A^n\\mathbf x$.</p>')
    sol = (f'<p><strong>(a)</strong></p>\\[A\\mathbf v_1={vec(Av1)}={l1}\\,\\mathbf v_1,\\qquad A\\mathbf v_2={vec(Av2)}={l2}\\,\\mathbf v_2,\\]'
           f'<p>so the eigenvalues are $\\lambda_1={l1}$ and $\\lambda_2={l2}$.</p>'
           f'<p><strong>(b)</strong> Solve $c_1\\mathbf v_1+c_2\\mathbf v_2=\\mathbf x$:</p>{steps}<p>so $\\mathbf x={combo_tex([c1, c2], ["\\mathbf v_1", "\\mathbf v_2"])}$.</p>'
           f'<p><strong>(c)</strong> Each application of $A$ multiplies $\\mathbf v_i$ by $\\lambda_i$, so $A^n\\mathbf x=c_1\\lambda_1^n\\mathbf v_1+c_2\\lambda_2^n\\mathbf v_2$:</p>'
           f'\\[A^n\\mathbf x={c1}\\cdot {pw(l1)}{vec(v1)}+({c2})\\cdot {pw(l2)}{vec(v2)}=\\begin{{bmatrix}}{sp.latex(formula[0])}\\\\ {sp.latex(formula[1])}\\end{{bmatrix}}.\\]'
           f'<p>With $n={k}$: $({l1})^{k}={l1 ** k}$ and $({l2})^{k}={l2 ** k}$, so</p>'
           f'\\[A^{{{k}}}\\mathbf x={c1}({l1 ** k}){vec(v1)}+({c2})({l2 ** k}){vec(v2)}={vec(Akx)}.\\]')
    return {'problem': problem, 'answer': f'$\\lambda_1={l1},\\ \\lambda_2={l2}$; $\\mathbf x={combo_tex([c1, c2], ["\\mathbf v_1", "\\mathbf v_2"])}$; $A^{{{k}}}\\mathbf x={vec(Akx)}$',
            'solution': sol, 'data': {'A': A, 'x0': x0, 'vs': [v1, v2], 'vals': [l1, l2], 'k': k, 'Akx': Akx, 'formula': formula}}

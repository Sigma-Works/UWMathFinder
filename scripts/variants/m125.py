"""Math 125 (Calculus II) practice-problem templates. See common.py for the contract.

Checks recompute each answer another way: differentiate an antiderivative back,
integrate numerically, slice a solid the other way (washers instead of shells),
use a different numerical-rule identity, or substitute a solution back into its
differential equation.
"""
import math
import mpmath
import sympy as sp

from common import template, Reject, need, close, nz, quad, quad2

C = 'Math 125'
x, y, t, u, th = sp.symbols('x y t u theta', real=True)


def L(e):
    return sp.latex(e, ln_notation=True)


def num(e, v=x):
    return sp.lambdify(v, e, 'mpmath')


def deriv_ok(F, f, pts=(0.3, 0.7, 1.3, 2.1)):
    """F' = f, exactly or at several points."""
    d = sp.diff(F, x) - f
    if sp.simplify(d) == 0:
        return True
    pts = [sp.nsimplify(p) for p in pts]          # exact sample points, evaluated to 30 digits
    return all(abs(complex(d.subs(x, p).evalf(30))) < 1e-20 * max(1, abs(complex(f.subs(x, p).evalf(30)))) for p in pts)


def chk_antideriv(d):
    need(deriv_ok(d['F'], d['f'], d.get('pts', (0.3, 0.7, 1.3, 2.1))), 'the derivative of the answer is the integrand')


def chk_definite(d):
    need(close(quad(num(d['f']), d['a'], d['b']), sp.N(d['I'], 25), 1e-10), 'definite integral (numerical)')


# ── techniques of integration ────────────────────────────────────────
@template(course=C, chapter='trig_substitution', id='m125-u-substitution',
          title='A definite integral by substitution',
          based_on={'exam': 'm125finalWin2015', 'problem': 2}, check=chk_definite)
def u_sub(rng):
    B = rng.choice([4, 9, 5, 10, 16])
    lo2, hi2 = sorted(rng.sample([s_ * s_ for s_ in range(0, 5) if s_ * s_ <= B], 2))
    a, b = B - hi2, B - lo2               # u = B - x then runs between perfect squares
    k = rng.choice([1, 2, 3])
    f = k * x * sp.sqrt(B - x)
    g = k * (B - u) * sp.sqrt(u)
    I = sp.integrate(g, (u, lo2, hi2))
    G = sp.integrate(sp.expand(g), u)
    problem = f'<p>Evaluate</p>\\[\\int_{{{a}}}^{{{b}}}{L(f)}\\,dx.\\]'
    sol = (f'<p>Let $u={B}-x$, so $x={B}-u$ and $dx=-du$. When $x={a}$, $u={hi2}$; when $x={b}$, $u={lo2}$:</p>'
           f'\\[\\int_{{{a}}}^{{{b}}}{L(f)}\\,dx=-\\int_{{{hi2}}}^{{{lo2}}}{L(g)}\\,du=\\int_{{{lo2}}}^{{{hi2}}}\\left({L(sp.expand(g))}\\right)du'
           f'=\\left[{L(G)}\\right]_{{{lo2}}}^{{{hi2}}}={L(I)}.\\]')
    return {'problem': problem, 'answer': f'${L(I)}$', 'solution': sol, 'data': {'f': f, 'a': a, 'b': b, 'I': I}}


@template(course=C, chapter='trig_substitution', id='m125-trig-integral',
          title='A trigonometric integral', based_on={'exam': 'm125finalWin2015', 'problem': 1}, check=chk_antideriv)
def trig_integral(rng):
    fam = rng.choice(['sin-odd', 'cos-odd', 'sec4', 'tan-sec'])
    k = rng.choice([1, 1, 2])
    kx = L(k * x)
    kk = '' if k == 1 else str(k)
    pre = '' if k == 1 else f'\\frac{{1}}{{{k}}}'
    w = sp.Symbol('w')
    if fam in ('sin-odd', 'cos-odd'):
        m, nn = rng.choice([3, 5]), rng.choice([0, 2, 4])
        inner = sp.expand((1 - w ** 2) ** ((m - 1) // 2) * w ** nn)
        Fw = sp.integrate(inner, w)
        if fam == 'sin-odd':
            f = sp.sin(k * x) ** m * sp.cos(k * x) ** nn
            F = -Fw.subs(w, sp.cos(k * x)) / k
            work = (f'<p>The power of $\\sin$ is odd: save one $\\sin {kx}$ and rewrite the rest with $\\sin^2=1-\\cos^2$. With $w=\\cos {kx}$, '
                    f'$dw=-{kk}\\sin {kx}\\,dx$:</p>\\[\\int {L(f)}\\,dx=-{pre}\\int \\left({L(inner)}\\right)dw=-{pre}\\left({L(Fw)}\\right)+C.\\]')
        else:
            f = sp.cos(k * x) ** m * sp.sin(k * x) ** nn
            F = Fw.subs(w, sp.sin(k * x)) / k
            work = (f'<p>The power of $\\cos$ is odd: save one $\\cos {kx}$ and rewrite the rest with $\\cos^2=1-\\sin^2$. With $w=\\sin {kx}$, '
                    f'$dw={kk}\\cos {kx}\\,dx$:</p>\\[\\int {L(f)}\\,dx={pre}\\int \\left({L(inner)}\\right)dw={pre}\\left({L(Fw)}\\right)+C.\\]')
    elif fam == 'sec4':
        nn = rng.choice([0, 1, 2, 3])
        f = sp.tan(k * x) ** nn * sp.sec(k * x) ** 4
        inner = sp.expand(w ** nn * (1 + w ** 2))
        Fw = sp.integrate(inner, w)
        F = Fw.subs(w, sp.tan(k * x)) / k
        work = (f'<p>Save $\\sec^2{kx}$ and write the other $\\sec^2=1+\\tan^2$. With $w=\\tan {kx}$, $dw={kk}\\sec^2{kx}\\,dx$:</p>'
                f'\\[\\int {L(f)}\\,dx={pre}\\int \\left({L(inner)}\\right)dw={pre}\\left({L(Fw)}\\right)+C.\\]')
    else:
        m = rng.choice([3, 5])
        f = sp.tan(k * x) ** m * sp.sec(k * x)
        inner = sp.expand((w ** 2 - 1) ** ((m - 1) // 2))
        Fw = sp.integrate(inner, w)
        F = Fw.subs(w, sp.sec(k * x)) / k
        work = (f'<p>The power of $\\tan$ is odd: save $\\sec {kx}\\tan {kx}$ and rewrite the rest with $\\tan^2=\\sec^2-1$. With $w=\\sec {kx}$, '
                f'$dw={kk}\\sec {kx}\\tan {kx}\\,dx$:</p>\\[\\int {L(f)}\\,dx={pre}\\int \\left({L(inner)}\\right)dw={pre}\\left({L(Fw)}\\right)+C.\\]')
    F = sp.expand(F)
    problem = f'<p>Evaluate</p>\\[\\int {L(f)}\\,dx.\\]'
    sol = work + f'<p>Substituting back:</p>\\[\\int {L(f)}\\,dx={L(F)}+C.\\]'
    return {'problem': problem, 'answer': f'${L(F)}+C$', 'solution': sol, 'data': {'F': F, 'f': f, 'pts': (0.2, 0.4, 0.6)}}


def chk_trigsub(d):
    need(close(quad(num(d['f']), 0, mpmath.mpf(str(sp.N(d['b'], 30)))), sp.N(d['I'], 25), 1e-10), 'definite integral (numerical)')


@template(course=C, chapter='trig_substitution', id='m125-trig-substitution',
          title='A definite integral by trigonometric substitution',
          based_on={'exam': 'm125mid2Win2016_Bekyel', 'problem': 1}, check=chk_trigsub)
def trig_sub(rng):
    a = rng.choice([1, 2, 3, 4, 5])
    fam = rng.choice(['x2-over-root', 'root', 'three-halves'])
    if fam in ('x2-over-root', 'root'):
        th1 = rng.choice([sp.pi / 6, sp.pi / 4, sp.pi / 3] + ([sp.pi / 2] if fam == 'root' else []))
        b = sp.simplify(a * sp.sin(th1))
        f = x ** 2 / sp.sqrt(a * a - x ** 2) if fam == 'x2-over-root' else sp.sqrt(a * a - x ** 2)
        gth = a ** 2 * sp.sin(th) ** 2 if fam == 'x2-over-root' else a ** 2 * sp.cos(th) ** 2
        sub = f'x={a}\\sin\\theta,\\quad dx={a}\\cos\\theta\\,d\\theta,\\quad \\sqrt{{{a * a}-x^2}}={a}\\cos\\theta'
        ident = '<p>Use $\\sin^2\\theta=\\frac{1-\\cos2\\theta}{2}$.</p>' if fam == 'x2-over-root' else '<p>Use $\\cos^2\\theta=\\frac{1+\\cos2\\theta}{2}$.</p>'
    else:
        th1 = rng.choice([sp.pi / 6, sp.pi / 4, sp.pi / 3])
        b = sp.simplify(a * sp.tan(th1))
        f = 1 / (a * a + x ** 2) ** sp.Rational(3, 2)
        gth = sp.cos(th) / a ** 2
        sub = f'x={a}\\tan\\theta,\\quad dx={a}\\sec^2\\theta\\,d\\theta,\\quad ({a * a}+x^2)^{{3/2}}={a ** 3}\\sec^3\\theta'
        ident = ''
    G = sp.integrate(gth, th)
    I = sp.simplify(G.subs(th, th1) - G.subs(th, 0))
    problem = f'<p>Evaluate</p>\\[\\int_0^{{{L(b)}}}{L(f)}\\,dx.\\]'
    sol = (f'<p>Substitute ${sub}$. The limits $x=0$ and $x={L(b)}$ become $\\theta=0$ and $\\theta={L(th1)}$:</p>'
           f'\\[\\int_0^{{{L(b)}}}{L(f)}\\,dx=\\int_0^{{{L(th1)}}}{L(gth)}\\,d\\theta.\\]{ident}'
           f'\\[=\\left[{L(G)}\\right]_0^{{{L(th1)}}}={L(I)}.\\]')
    return {'problem': problem, 'answer': f'${L(I)}$', 'solution': sol, 'data': {'f': f, 'b': b, 'I': I}}


@template(course=C, chapter='trig_substitution', id='m125-partial-fractions',
          title='An integral by partial fractions',
          based_on={'exam': 'm125mid2Win2016_Bekyel', 'problem': 2}, check=chk_antideriv)
def partial_fractions(rng):
    nroots = rng.choice([2, 3])
    roots = sorted(rng.sample(range(-3, 4), nroots))
    den = sp.prod([x - r for r in roots])
    numr = sum(rng.randint(-4, 4) * x ** i for i in range(nroots))
    if numr == 0 or sp.gcd(numr, den) != 1:
        raise Reject
    f = numr / sp.expand(den)
    parts = sp.apart(numr / den, x)
    coeffs = [sp.simplify((numr / sp.prod([x - q for q in roots if q != r])).subs(x, r)) for r in roots]
    if any(sp.fraction(c_)[1] > 12 for c_ in coeffs):
        raise Reject
    F = sum(c_ * sp.log(sp.Abs(x - r)) for c_, r in zip(coeffs, roots))
    form = ' + '.join(f'\\frac{{{"ABC"[i]}}}{{{L(x - r)}}}' for i, r in enumerate(roots))
    cover = ', '.join(f'$x={r}$ gives ${"ABC"[i]}={L(coeffs[i])}$' for i, r in enumerate(roots))
    problem = f'<p>Evaluate</p>\\[\\int {L(f)}\\,dx.\\]'
    sol = (f'<p>Factor the denominator: ${L(sp.expand(den))}={L(den)}$. Write</p>\\[{L(f)}={form}.\\]'
           f'<p>Multiply through by the denominator and plug in each root: {cover}. So</p>\\[{L(f)}={L(parts)}.\\]'
           f'<p>Integrate each term:</p>\\[\\int {L(f)}\\,dx={L(F)}+C.\\]')
    return {'problem': problem, 'answer': f'${L(F)}+C$', 'solution': sol,
            'data': {'F': F, 'f': f, 'pts': tuple(r + 0.37 for r in roots) + (roots[-1] + 1.5,)}}


@template(course=C, chapter='integration_by_parts', id='m125-integration-by-parts',
          title='An integral by parts', based_on={'exam': 'm125finalAut2021', 'problem': 10}, check=chk_antideriv)
def by_parts(rng):
    fam = rng.choice(['xn-ln', 'x-exp', 'x2-exp', 'x-trig', 'x2-trig', 'ln2'])
    k = rng.choice([1, 2, 3, 4, 5])
    if fam == 'xn-ln':
        nn = rng.choice([1, 2, 3, 4, 5])
        f, U, dV, steps = x ** nn * sp.log(x), sp.log(x), x ** nn, 1
    elif fam == 'x-exp':
        e = sp.exp(rng.choice([k, -k]) * x)
        f, U, dV, steps = x * e, x, e, 1
    elif fam == 'x2-exp':
        f, U, dV, steps = x ** 2 * sp.exp(k * x), x ** 2, sp.exp(k * x), 2
    elif fam == 'x2-trig':
        tr = rng.choice([sp.sin, sp.cos])
        f, U, dV, steps = x ** 2 * tr(k * x), x ** 2, tr(k * x), 2
    elif fam == 'x-trig':
        tr = rng.choice([sp.sin, sp.cos])
        f, U, dV, steps = x * tr(k * x), x, tr(k * x), 1
    else:
        f, U, dV, steps = sp.log(x) ** 2, sp.log(x) ** 2, sp.Integer(1), 2
    V = sp.integrate(dV, x)
    dU = sp.diff(U, x)
    rest = sp.simplify(V * dU)
    F = sp.simplify(sp.integrate(f, x))
    lines = (f'<p>Take $u={L(U)}$ and $dv={L(dV)}\\,dx$, so $du={L(dU)}\\,dx$ and $v={L(V)}$:</p>'
             f'\\[\\int {L(f)}\\,dx={L(U * V)}-\\int {L(rest)}\\,dx.\\]')
    if steps == 2:
        U2 = x if fam in ('x2-exp', 'x2-trig') else sp.log(x)
        dV2 = sp.simplify(rest / U2)
        V2 = sp.integrate(dV2, x)
        lines += (f'<p>Use parts again on the last integral, with $u={L(U2)}$, $dv={L(dV2)}\\,dx$ (so $du={L(sp.diff(U2, x))}\\,dx$, $v={L(V2)}$):</p>'
                  f'\\[\\int {L(rest)}\\,dx={L(U2 * V2)}-\\int {L(sp.simplify(V2 * sp.diff(U2, x)))}\\,dx={L(sp.integrate(rest, x))}.\\]')
    else:
        lines += f'<p>The last integral is $\\int {L(rest)}\\,dx={L(sp.integrate(rest, x))}$.</p>'
    problem = f'<p>Evaluate</p>\\[\\int {L(f)}\\,dx.\\]'
    sol = lines + f'<p>So</p>\\[\\int {L(f)}\\,dx={L(F)}+C.\\]'
    return {'problem': problem, 'answer': f'${L(F)}+C$', 'solution': sol, 'data': {'F': F, 'f': f}}


# ── area and volume ──────────────────────────────────────────────────
def chk_area(d):
    gap = d['top'] - d['bottom']
    need(close(quad(num(gap), d['a'], d['b']), sp.N(d['A'], 25), 1e-10), 'area (numerical)')
    need(all(float(gap.subs(x, d['a'] + (d['b'] - d['a']) * s_)) >= -1e-12 for s_ in (0.1, 0.5, 0.9)), 'top curve is on top')


@template(course=C, chapter='area_between_curves', id='m125-area-between-curves',
          title='Area between a parabola and a line',
          based_on={'exam': 'm125finalSpr2025', 'problem': 5}, check=chk_area)
def area_between(rng):
    x1, x2 = sorted(rng.sample(range(-3, 5), 2))
    k = rng.choice([1, 2, 3])
    line = rng.randint(-3, 3) * x + rng.randint(-4, 4)
    para = sp.expand(line + k * (x - x1) * (x2 - x))     # the parabola is above the line between x1 and x2
    A = sp.Rational(k) * (x2 - x1) ** 3 / 6
    diff = sp.expand(para - line)
    problem = f'<p>Find the area of the region enclosed by $y={L(para)}$ and $y={L(line)}$.</p>'
    sol = (f'<p>The curves meet where ${L(para)}={L(line)}$, i.e. ${L(-diff)}=0$, so $x={x1}$ and $x={x2}$. '
           f'Between them the parabola is on top (test $x={L(sp.Rational(x1 + x2, 2))}$, for example).</p>'
           f'\\[A=\\int_{{{x1}}}^{{{x2}}}\\left[\\left({L(para)}\\right)-\\left({L(line)}\\right)\\right]dx=\\int_{{{x1}}}^{{{x2}}}\\left({L(diff)}\\right)dx'
           f'=\\left[{L(sp.integrate(diff, x))}\\right]_{{{x1}}}^{{{x2}}}={L(A)}.\\]')
    return {'problem': problem, 'answer': f'${L(A)}$', 'solution': sol, 'data': {'top': para, 'bottom': line, 'a': x1, 'b': x2, 'A': A}}


def chk_shells(d):
    """Redo the volume with washers (slicing horizontally) instead of shells."""
    a, b, c = d['a'], d['b'], d['c']      # region between y = a x - x^2 (top) and y = b x, rotated about x = c (c <= 0)
    ytop, ymax = b * (a - b), a * a / 4.0

    def washer(Y):
        disc = a * a - 4 * Y
        if disc < 0:
            return 0
        lo = (a - math.sqrt(disc)) / 2
        hi = min((a + math.sqrt(disc)) / 2, Y / b)
        return math.pi * ((hi - c) ** 2 - (lo - c) ** 2) if hi > lo else 0
    val = mpmath.quad(washer, sorted({0.0, float(ytop), float(ymax)}))
    need(close(val, sp.N(d['V'], 25), 1e-8), 'volume by washers')


@template(course=C, chapter='volumes_by_shells', id='m125-volume-shells',
          title='Volume of revolution by cylindrical shells',
          based_on={'exam': 'm125finalSpr2024', 'problem': 6}, check=chk_shells)
def shells(rng):
    a = rng.choice([3, 4, 5, 6])
    b = rng.choice([q for q in (1, 2, 3) if q < a])
    c = rng.choice([0, 0, -1, -2])
    top, bot = a * x - x ** 2, b * x
    xr = a - b
    radius = x - c
    V = sp.integrate(sp.expand(2 * sp.pi * radius * (top - bot)), (x, 0, xr))
    axis = 'the $y$-axis' if c == 0 else f'the line $x={c}$'
    problem = f'<p>The region between $y={L(top)}$ and $y={L(bot)}$ is rotated about {axis}. Find the volume of the solid.</p>'
    sol = (f'<p>The curves meet where ${L(top)}={L(bot)}$: $x=0$ and $x={xr}$. On $[0,{xr}]$, $y={L(top)}$ is on top, so a shell at $x$ has height ${L(sp.expand(top - bot))}$ '
           f'and radius ${L(radius)}$ (its distance from {axis}).</p>'
           f'\\[V=\\int_0^{{{xr}}}2\\pi\\left({L(radius)}\\right)\\left({L(sp.expand(top - bot))}\\right)dx=2\\pi\\int_0^{{{xr}}}\\left({L(sp.expand(radius * (top - bot)))}\\right)dx={L(V)}.\\]')
    return {'problem': problem, 'answer': f'$V={L(V)}$', 'solution': sol, 'data': {'a': a, 'b': b, 'c': c, 'V': V}}


SECTIONS = {'square': (lambda s_: s_ ** 2, 'squares', 's^2'),
            'semicircle': (lambda s_: sp.pi * s_ ** 2 / 8, 'semicircles (with the side as diameter)', '\\frac{\\pi}{8}s^2'),
            'equilateral': (lambda s_: sp.sqrt(3) * s_ ** 2 / 4, 'equilateral triangles', '\\frac{\\sqrt3}{4}s^2')}


def chk_sections(d):
    s0, shape = 1.7, d['shape']
    if shape == 'semicircle':            # half of a disk of diameter s0, by integration
        area = quad(lambda X: 2 * mpmath.sqrt((s0 / 2) ** 2 - X ** 2), -s0 / 2, s0 / 2) / 2
    elif shape == 'equilateral':
        area = s0 * (s0 * math.sqrt(3) / 2) / 2
    else:
        area = s0 * s0
    need(close(area, float(SECTIONS[shape][0](sp.Float(s0))), 1e-10), 'cross-section area formula')
    side = num(d['side'])
    Af = sp.lambdify(u, SECTIONS[shape][0](u), 'mpmath')
    need(close(quad(lambda X: Af(side(X)), d['a'], d['b']), sp.N(d['V'], 25), 1e-9), 'volume (numerical)')


@template(course=C, chapter='volumes_by_cross_sectional_area', id='m125-cross-sections',
          title='Volume of a solid with known cross-sections',
          based_on={'exam': 'm125finalSpr2015', 'problem': 5}, check=chk_sections)
def cross_sections(rng):
    shape = rng.choice(list(SECTIONS))
    Af, words, ftex = SECTIONS[shape]
    if rng.random() < 0.5:
        A_, B_ = rng.choice([1, 2, 3, 4]), rng.choice([1, 2, 3])
        side, a, b = B_ - sp.Rational(B_, A_) * x, 0, A_
        base = f'the triangle with vertices $(0,0)$, $({A_},0)$ and $(0,{B_})$'
        sdesc = f'At $x$ the section runs from $y=0$ up to the line $y={L(side)}$'
    else:
        h = rng.choice([1, 4, 9])
        r = sp.sqrt(h)
        side, a, b = h - x ** 2, -r, r
        base = f'the region between $y={h}-x^2$ and the $x$-axis'
        sdesc = f'At $x$ the section runs from $y=0$ up to $y={L(side)}$'
    integrand = sp.expand(Af(side))
    V = sp.simplify(sp.integrate(integrand, (x, a, b)))
    problem = f'<p>The base of a solid is {base}. Cross-sections perpendicular to the $x$-axis are {words}. Find the volume.</p>'
    sol = (f'<p>{sdesc}, so the side length is $s={L(side)}$ and the cross-section area is $A(x)={ftex}$ with that $s$.</p>'
           f'\\[V=\\int_{{{L(a)}}}^{{{L(b)}}}A(x)\\,dx=\\int_{{{L(a)}}}^{{{L(b)}}}\\left({L(integrand)}\\right)dx={L(V)}.\\]')
    return {'problem': problem, 'answer': f'$V={L(V)}$', 'solution': sol, 'data': {'shape': shape, 'side': side, 'a': float(a), 'b': float(b), 'V': V}}


def chk_arc(d):
    yp = sp.diff(d['f'], x)
    need(close(quad(num(sp.sqrt(1 + yp ** 2)), d['a'], d['b']), sp.N(d['L'], 25), 1e-10), 'arc length (numerical)')


@template(course=C, chapter='arc_length', id='m125-arc-length',
          title='Arc length when 1 + (y′)² is a perfect square',
          based_on={'exam': 'm125mid2Win2016_Bekyel', 'problem': 3}, check=chk_arc)
def arc_length(rng):
    m = rng.choice([2, 3, 4])
    c = rng.choice([sp.Rational(1, 2), sp.Integer(1), sp.Integer(2)])
    yp = c * x ** m - x ** (-m) / (4 * c)          # then 1 + y'^2 = (c x^m + x^{-m}/(4c))^2
    f = sp.integrate(yp, x)
    a = rng.choice([1, 1, 2])
    b = a + rng.choice([1, 2])
    plus = c * x ** m + x ** (-m) / (4 * c)
    Lval = sp.simplify(sp.integrate(plus, (x, a, b)))
    problem = f'<p>Find the length of the curve $y={L(f)}$ for ${a}\\le x\\le{b}$.</p>'
    sol = (f'<p>$y\'={L(yp)}$, so</p>\\[1+(y\')^2=1+\\left({L(yp)}\\right)^2={L(sp.expand(1 + yp ** 2))}=\\left({L(plus)}\\right)^2.\\]'
           f'<p>(The cross term of $(y\')^2$ is $-\\frac12$; adding 1 turns it into $+\\frac12$, which makes a perfect square.)</p>'
           f'\\[L=\\int_{{{a}}}^{{{b}}}\\left({L(plus)}\\right)dx=\\left[{L(sp.integrate(plus, x))}\\right]_{{{a}}}^{{{b}}}={L(Lval)}.\\]')
    return {'problem': problem, 'answer': f'$L={L(Lval)}$', 'solution': sol, 'data': {'f': f, 'a': a, 'b': b, 'L': Lval}}


# ── work, centroids ──────────────────────────────────────────────────
def chk_pump(d):
    shape, R, H, depth, spout, rho = d['shape'], d['R'], d['H'], d['depth'], d['spout'], d['rho']
    area = (lambda Y: math.pi * R * R) if shape == 'cylinder' else (lambda Y: math.pi * (R * Y / H) ** 2)
    need(close(quad(lambda Y: rho * area(Y) * (H + spout - Y), 0, depth), float(d['W']), 1e-9), 'work (numerical slices)')


@template(course=C, chapter='water_tank_problems', id='m125-pumping-work',
          title='Work to pump water out of a tank',
          based_on={'exam': 'm125finalSpr2024', 'problem': 8}, check=chk_pump)
def pumping(rng):
    shape = rng.choice(['cylinder', 'cone'])
    metric = rng.random() < 0.5
    rho, unit, wunit = (sp.Integer(9800), 'm', 'J') if metric else (sp.Rational(125, 2), 'ft', 'ft·lb')
    R, H = rng.choice([1, 2, 3, 4]), rng.choice([3, 4, 6, 8, 10])
    depth = H if rng.random() < 0.5 else rng.choice([q for q in range(1, H) if 2 * q >= H])
    spout = rng.choice([0, 0, 1, 2])
    Yv = sp.Symbol('y')
    A = sp.pi * R ** 2 if shape == 'cylinder' else sp.pi * (sp.Rational(R, H) * Yv) ** 2
    dist = H + spout - Yv
    W = sp.integrate(rho * A * dist, (Yv, 0, depth))
    tank = (f'A cylindrical tank of radius ${R}$ {unit} and height ${H}$ {unit}' if shape == 'cylinder' else
            f'A conical tank (vertex down) of height ${H}$ {unit} whose top has radius ${R}$ {unit}')
    fill = 'is full of water' if depth == H else f'holds water to a depth of ${depth}$ {unit}'
    out = 'over the top' if spout == 0 else f'out through a spout ${spout}$ {unit} above the top'
    weight = '$\\rho g=9800$ N/m³' if metric else 'water weighs $62.5$ lb/ft³'
    slice_r = f'{R}' if shape == 'cylinder' else f'\\frac{{{R}}}{{{H}}}y'
    problem = f'<p>{tank} {fill}. How much work does it take to pump all of the water {out}? (Use {weight}.)</p>'
    sol = (f'<p>Measure $y$ up from the bottom{" (the vertex)" if shape == "cone" else ""}. '
           + ('' if shape == 'cylinder' else f'By similar triangles the radius at height $y$ is $\\frac{{{R}}}{{{H}}}y$. ')
           + f'A thin slice at height $y$ has volume $\\pi\\left({slice_r}\\right)^2dy$, so it weighs ${L(rho)}\\pi\\left({slice_r}\\right)^2dy$, '
           f'and it must be lifted ${L(dist)}$ {unit}.</p>'
           f'\\[W=\\int_0^{{{depth}}}{L(rho)}\\cdot {L(A)}\\left({L(dist)}\\right)dy={L(W)}\\approx {float(W):,.0f}\\ \\text{{{wunit}}}.\\]')
    return {'problem': problem, 'answer': f'$W={L(W)}\\approx{float(W):,.0f}$ {wunit}', 'solution': sol,
            'data': {'shape': shape, 'R': R, 'H': H, 'depth': depth, 'spout': spout, 'rho': float(rho), 'W': W}}


def chk_centroid(d):
    a, b = float(d['a']), float(d['b'])
    fn = num(d['f'])
    A = quad2(lambda X, Y: 1, a, b, 0, fn)
    need(close(quad2(lambda X, Y: X, a, b, 0, fn) / A, sp.N(d['xbar'], 25), 1e-9), 'x-bar (double integral)')
    need(close(quad2(lambda X, Y: Y, a, b, 0, fn) / A, sp.N(d['ybar'], 25), 1e-9), 'y-bar (double integral)')


@template(course=C, chapter='work_and_average_value', id='m125-centroid',
          title='The centroid of a region under a curve',
          based_on={'exam': 'm125finalSpr2024', 'problem': 7}, check=chk_centroid)
def centroid(rng):
    fam = rng.choice(['x2', 'sqrt', 'inv3', 'sin', 'para', 'cube', 'exp'])
    if fam == 'cube':
        f, (a, b) = x ** 3, rng.choice([(0, 1), (0, 2), (1, 2)])
    elif fam == 'exp':
        f, (a, b) = sp.exp(x), rng.choice([(0, 1), (0, 2), (-1, 1)])
    elif fam == 'x2':
        f, (a, b) = x ** 2, sorted(rng.sample([0, 1, 2, 3], 2))
    elif fam == 'sqrt':
        f, (a, b) = sp.sqrt(x), sorted(rng.sample([0, 1, 4], 2))
    elif fam == 'inv3':
        f, (a, b) = rng.choice([2, 4]) / x ** 3, (1, rng.choice([2, 3]))
    elif fam == 'sin':
        f, (a, b) = rng.choice([1, 2]) * sp.sin(x), (0, sp.pi)
    else:
        h = rng.choice([1, 4, 9])
        f, (a, b) = h - x ** 2, (0, sp.sqrt(h))
    A = sp.integrate(f, (x, a, b))
    Mx = sp.integrate(x * f, (x, a, b))
    My = sp.integrate(f ** 2 / 2, (x, a, b))
    xbar, ybar = sp.simplify(Mx / A), sp.simplify(My / A)
    problem = f'<p>Find the centroid of the region under $y={L(f)}$ and above the $x$-axis for ${L(a)}\\le x\\le{L(b)}$.</p>'
    sol = (f'<p>Area: $A=\\int_{{{L(a)}}}^{{{L(b)}}}{L(f)}\\,dx={L(A)}$.</p>'
           f'<p>$\\bar x=\\dfrac1A\\int x\\,f(x)\\,dx$ and $\\bar y=\\dfrac1A\\int\\frac12 f(x)^2\\,dx$:</p>'
           f'\\[\\int_{{{L(a)}}}^{{{L(b)}}}{L(x * f)}\\,dx={L(Mx)},\\qquad \\int_{{{L(a)}}}^{{{L(b)}}}\\frac12\\left({L(f)}\\right)^2dx={L(My)}.\\]'
           f'\\[\\bar x=\\frac{{{L(Mx)}}}{{{L(A)}}}={L(xbar)},\\qquad \\bar y=\\frac{{{L(My)}}}{{{L(A)}}}={L(ybar)}.\\]')
    return {'problem': problem, 'answer': f'$(\\bar x,\\bar y)=\\left({L(xbar)},\\ {L(ybar)}\\right)$', 'solution': sol,
            'data': {'f': f, 'a': a, 'b': b, 'xbar': xbar, 'ybar': ybar}}


def chk_rope(d):
    Wb, w, H = d['Wb'], d['w'], d['H']
    force = lambda s_: Wb + w * (H - s_)          # bucket plus the cable still hanging after it has risen s feet
    total = quad(force, 0, H)
    need(close(total, float(d['W']), 1e-12), 'total work')
    s_half = mpmath.findroot(lambda s_: quad(force, 0, s_) - total / 2, H / 2)
    need(close(s_half, float(d['s']), 1e-9), 'height at half the work')


@template(course=C, chapter='rope_problems', id='m125-rope-work',
          title='Lifting a bucket with a heavy cable',
          based_on={'exam': 'm125finalWin2017', 'problem': 5}, check=chk_rope)
def rope(rng):
    Wb, w, H = rng.choice([10, 20, 30, 40]), rng.choice([1, 2, 3]), rng.choice([10, 20, 30])
    S = sp.Symbol('s', positive=True)
    W = Wb * H + sp.Rational(w * H * H, 2)
    Ws = sp.expand(Wb * S + w * (H * S - S ** 2 / 2))
    roots = [r for r in sp.solve(sp.Eq(Ws, W / 2), S) if r.is_real and 0 < r < H]
    if len(roots) != 1:
        raise Reject
    s_ = roots[0]
    problem = (f'<p>A cable that weighs ${w}$ lb per foot lifts a bucket of water weighing ${Wb}$ lb from the bottom of a well ${H}$ ft deep to the top.</p>'
               '<p>(a) How much work is done?<br>(b) How far above the bottom of the well is the bucket when exactly half of that work has been done?</p>')
    sol = (f'<p>Let $s$ be how far the bucket has risen. The force needed then is the bucket plus the ${H}-s$ ft of cable still hanging: $F(s)={Wb}+{w}({H}-s)$ lb.</p>'
           f'<p><strong>(a)</strong> $W=\\int_0^{{{H}}}\\big({Wb}+{w}({H}-s)\\big)ds={Wb}\\cdot{H}+{w}\\cdot\\frac{{{H}^2}}2={L(W)}$ ft·lb.</p>'
           f'<p><strong>(b)</strong> The work done raising it the first $s$ feet is $\\int_0^s F={L(Ws)}$. Set this equal to $\\frac{{{L(W)}}}2$:</p>'
           f'\\[{L(Ws)}={L(W / 2)}.\\]<p>Only one root of this quadratic lies in $[0,{H}]$: $s={L(s_)}\\approx{float(s_):.3f}$ ft above the bottom.</p>')
    return {'problem': problem, 'answer': f'(a) ${L(W)}$ ft·lb &nbsp; (b) $s={L(s_)}\\approx{float(s_):.3f}$ ft', 'solution': sol,
            'data': {'Wb': Wb, 'w': w, 'H': H, 'W': W, 's': s_}}


# ── improper integrals, approximation, Riemann sums ──────────────────
def chk_improper(d):
    f, a, b = d['f'], d['a'], d['b']
    ref = sp.integrate(f, (x, a, b))
    if d['value'] == 'diverges':
        need(not ref.is_finite, 'diverges (SymPy)')
    else:
        need(sp.simplify(ref - d['value']) == 0, 'value (SymPy)')
        lo = mpmath.mpf(float(a))
        hi = mpmath.inf if b == sp.oo else mpmath.mpf(float(b))
        need(close(mpmath.quad(num(f), [lo, hi]), sp.N(d['value'], 25), 1e-7), 'value (numerical)')


@template(course=C, chapter='improper_integrals', id='m125-improper-integral',
          title='Does the improper integral converge? If so, evaluate it',
          based_on={'exam': 'm125finalAut2015', 'problem': 3}, check=chk_improper)
def improper(rng):
    fam = rng.choice(['p-inf', 'p-zero', 'exp', 'arctan'])
    T = sp.Symbol('T', positive=True)
    k = rng.choice([1, 2, 3])
    if fam == 'p-inf':
        p = rng.choice([sp.Rational(3, 2), sp.Integer(2), sp.Integer(3), sp.Rational(1, 2), sp.Integer(1), sp.Rational(4, 3)])
        f, a, b = k * x ** (-p), 1, sp.oo
        Fp = sp.integrate(f, (x, 1, T))
        value = sp.limit(Fp, T, sp.oo)
        lim = f'\\lim_{{T\\to\\infty}}\\int_1^T{L(f)}\\,dx=\\lim_{{T\\to\\infty}}\\left({L(sp.simplify(Fp))}\\right)'
    elif fam == 'p-zero':
        p = rng.choice([sp.Rational(1, 2), sp.Rational(1, 3), sp.Rational(2, 3), sp.Integer(1), sp.Integer(2)])
        f, a, b = k * x ** (-p), 0, 1
        Fp = sp.integrate(f, (x, T, 1))
        value = sp.limit(Fp, T, 0, '+')
        lim = f'\\lim_{{T\\to0^+}}\\int_T^1{L(f)}\\,dx=\\lim_{{T\\to0^+}}\\left({L(sp.simplify(Fp))}\\right)'
    elif fam == 'exp':
        kk = rng.choice([1, 2, 3, sp.Rational(1, 2)])
        f, a, b = k * x * sp.exp(-kk * x), 0, sp.oo
        Fp = sp.integrate(f, (x, 0, T))
        value = sp.limit(Fp, T, sp.oo)
        lim = f'\\lim_{{T\\to\\infty}}\\int_0^T{L(f)}\\,dx=\\lim_{{T\\to\\infty}}\\left({L(sp.simplify(Fp))}\\right)\\quad\\text{{(by parts)}}'
    else:
        c = rng.choice([1, 2, 3])
        a = rng.choice([0, c])
        f, b = k / (x ** 2 + c * c), sp.oo
        Fp = sp.integrate(f, (x, a, T))
        value = sp.limit(Fp, T, sp.oo)
        lim = f'\\lim_{{T\\to\\infty}}\\int_{{{a}}}^T{L(f)}\\,dx=\\lim_{{T\\to\\infty}}\\left({L(sp.simplify(Fp))}\\right)'
    div = not value.is_finite
    problem = f'<p>Determine whether the integral converges or diverges, and evaluate it if it converges:</p>\\[\\int_{{{L(a)}}}^{{{L(b)}}}{L(f)}\\,dx.\\]'
    sol = (f'<p>Write it as a limit of proper integrals:</p>\\[{lim}={"\\infty" if div else L(value)}.\\]'
           + ('<p>The limit is infinite, so the integral <strong>diverges</strong>.</p>' if div else f'<p>The limit is finite, so the integral <strong>converges</strong> to ${L(value)}$.</p>'))
    return {'problem': problem, 'answer': 'Diverges' if div else f'Converges to ${L(value)}$', 'solution': sol,
            'data': {'f': f, 'a': a, 'b': b, 'value': 'diverges' if div else value}}


APPROX_F = [lambda: sp.sqrt(1 + x ** 3), lambda: sp.exp(-x ** 2), lambda: 1 / (1 + x ** 2), lambda: sp.sin(x ** 2), lambda: sp.log(1 + x), lambda: sp.cos(x) ** 2]


def chk_rules(d):
    f = sp.lambdify(x, d['f'], 'math')
    a, b, nn = d['a'], d['b'], d['n']
    h = (b - a) / nn
    trap = h * (f(a) / 2 + sum(f(a + i * h) for i in range(1, nn)) + f(b) / 2)
    mid = h * sum(f(a + (i + 0.5) * h) for i in range(nn))
    h2 = (b - a) / (nn // 2)           # Simpson with n subintervals = (T_{n/2} + 2 M_{n/2}) / 3
    T2 = h2 * (f(a) / 2 + sum(f(a + i * h2) for i in range(1, nn // 2)) + f(b) / 2)
    M2 = h2 * sum(f(a + (i + 0.5) * h2) for i in range(nn // 2))
    got = {'T': trap, 'M': mid, 'S': (T2 + 2 * M2) / 3}
    for k_, v in d['vals'].items():
        need(abs(got[k_] - v) < 5e-7, f'{k_}_n')


@template(course=C, chapter='approximating_integrals', id='m125-numerical-rules',
          title='Trapezoid, midpoint and Simpson approximations',
          based_on={'exam': 'm125finalWin2015', 'problem': 7}, check=chk_rules)
def rules(rng):
    f = rng.choice(APPROX_F)()
    a, b, nn = 0, rng.choice([1, 2]), rng.choice([4, 6])
    want = sorted(rng.sample(['T', 'M', 'S'], 2), key='TMS'.index)
    fn = sp.lambdify(x, f, 'math')
    h = sp.Rational(b - a, nn)
    nodes = [a + i * h for i in range(nn + 1)]
    mids = [a + (i + sp.Rational(1, 2)) * h for i in range(nn)]
    vals, lines = {}, []
    if 'T' in want:
        coef = [1] + [2] * (nn - 1) + [1]
        vals['T'] = round(float(h) / 2 * sum(c_ * fn(float(p)) for c_, p in zip(coef, nodes)), 6)
        lines.append(f'<p><strong>Trapezoid:</strong> $T_{{{nn}}}=\\frac{{\\Delta x}}{{2}}\\left[f(x_0)+2f(x_1)+\\cdots+2f(x_{{{nn - 1}}})+f(x_{{{nn}}})\\right]\\approx{vals["T"]:.6f}$.</p>')
    if 'M' in want:
        vals['M'] = round(float(h) * sum(fn(float(p)) for p in mids), 6)
        lines.append(f'<p><strong>Midpoint:</strong> $M_{{{nn}}}=\\Delta x\\left[f\\left({L(mids[0])}\\right)+f\\left({L(mids[1])}\\right)+\\cdots+f\\left({L(mids[-1])}\\right)\\right]\\approx{vals["M"]:.6f}$.</p>')
    if 'S' in want:
        coef = [1] + [4 if i % 2 else 2 for i in range(1, nn)] + [1]
        vals['S'] = round(float(h) / 3 * sum(c_ * fn(float(p)) for c_, p in zip(coef, nodes)), 6)
        lines.append(f'<p><strong>Simpson:</strong> $S_{{{nn}}}=\\frac{{\\Delta x}}{{3}}\\left[f(x_0)+4f(x_1)+2f(x_2)+\\cdots+4f(x_{{{nn - 1}}})+f(x_{{{nn}}})\\right]\\approx{vals["S"]:.6f}$.</p>')
    names = {'T': f'$T_{{{nn}}}$ (trapezoid)', 'M': f'$M_{{{nn}}}$ (midpoint)', 'S': f'$S_{{{nn}}}$ (Simpson)'}
    table = ''.join(f'<tr><td>${L(p)}$</td><td>{fn(float(p)):.6f}</td></tr>' for p in sorted(set(nodes + (mids if 'M' in want else [])), key=float))
    problem = f'<p>Approximate $\\displaystyle\\int_{{{a}}}^{{{b}}}{L(f)}\\,dx$ with {" and ".join(names[w_] for w_ in want)}, using $n={nn}$. Round to six decimal places.</p>'
    sol = (f'<p>$\\Delta x=\\frac{{{b}-{a}}}{{{nn}}}={L(h)}$. Values of $f(x)={L(f)}$:</p>'
           f'<table class="variant-table"><tr><th>$x$</th><th>$f(x)$</th></tr>{table}</table>' + ''.join(lines))
    return {'problem': problem, 'answer': ', '.join(f'{names[w_]} $\\approx{vals[w_]:.6f}$' for w_ in want), 'solution': sol,
            'data': {'f': f, 'a': float(a), 'b': float(b), 'n': nn, 'vals': vals}}


def chk_riemann(d):
    f = sp.lambdify(x, d['f'], 'mpmath')
    a, b, nn, kind = d['a'], d['b'], d['n'], d['kind']
    h = mpmath.mpf(b - a) / nn
    offs = {'L': 0, 'R': 1, 'M': mpmath.mpf(1) / 2}[kind]
    need(close(h * sum(f(a + (i + offs) * h) for i in range(nn)), sp.N(d['S'], 25), 1e-12), 'Riemann sum')
    need(close(quad(f, a, b), sp.N(d['I'], 25), 1e-12), 'exact area')


@template(course=C, chapter='riemann_sums_and_defining_area', id='m125-riemann-sum',
          title='Riemann sum approximation of an area',
          based_on={'exam': 'm125mid1Spr2017_Loveless', 'problem': 4}, check=chk_riemann)
def riemann(rng):
    k = rng.choice([4, 6, 8])
    fam = rng.randrange(5)
    f = [k * x - x ** 2, x ** 2 + 1, sp.Integer(k) - x, x ** 3, 2 * x + 1][fam]
    a, b = 0, (k if fam in (0, 2) else rng.choice([2, 3, 4]))
    nn, kind = rng.choice([3, 4, 6]), rng.choice(['L', 'R', 'M'])
    h = sp.Rational(b - a, nn)
    offs = {'L': 0, 'R': 1, 'M': sp.Rational(1, 2)}[kind]
    pts = [a + (i + offs) * h for i in range(nn)]
    S = h * sum(f.subs(x, p) for p in pts)
    I = sp.integrate(f, (x, a, b))
    word = {'L': 'left endpoints', 'R': 'right endpoints', 'M': 'midpoints'}[kind]
    problem = (f'<p>Let $R$ be the region under $y={L(f)}$ and above the $x$-axis for ${a}\\le x\\le{b}$.</p>'
               f'<p>(a) Write the area of $R$ as an integral and evaluate it.<br>(b) Approximate the area with $n={nn}$ rectangles using {word}.</p>')
    sol = (f'<p><strong>(a)</strong> $\\displaystyle A=\\int_{{{a}}}^{{{b}}}\\left({L(f)}\\right)dx=\\left[{L(sp.integrate(f, x))}\\right]_{{{a}}}^{{{b}}}={L(I)}$.</p>'
           f'<p><strong>(b)</strong> $\\Delta x=\\frac{{{b}-{a}}}{{{nn}}}={L(h)}$, and the sample points ({word}) are {", ".join(f"${L(p)}$" for p in pts)}:</p>'
           f'\\[{L(h)}\\left[{"+".join(f"f\\left({L(p)}\\right)" for p in pts)}\\right]={L(h)}\\left[{"+".join(L(f.subs(x, p)) for p in pts)}\\right]={L(S)}.\\]')
    return {'problem': problem, 'answer': f'(a) ${L(I)}$ &nbsp; (b) ${L(S)}$', 'solution': sol,
            'data': {'f': f, 'a': a, 'b': b, 'n': nn, 'kind': kind, 'S': S, 'I': I}}


# ── motion ───────────────────────────────────────────────────────────
def chk_motion(d):
    v = d['v']
    need(sp.diff(v, t) == d['a'] and v.subs(t, 0) == d['v0'], 'velocity from acceleration')
    vf = sp.lambdify(t, v, 'mpmath')
    need(close(quad(vf, 0, d['T']), float(d['disp']), 1e-12), 'displacement')
    need(close(mpmath.quad(lambda s_: abs(vf(s_)), [0, d['root'], d['T']]), float(d['dist']), 1e-10), 'total distance')


@template(course=C, chapter='antiderivatives_and_acceleration', id='m125-displacement-distance',
          title='Velocity from acceleration; displacement and total distance',
          based_on={'exam': 'm125finalWin2015', 'problem': 5}, check=chk_motion)
def motion(rng):
    r1, r2, k = rng.choice([1, 2, 3, 4]), rng.choice([-1, -2, -3]), rng.choice([1, 2, 3])
    v = sp.expand(k * (t - r1) * (t - r2))
    a = sp.diff(v, t)
    v0 = v.subs(t, 0)
    T = r1 + rng.choice([1, 2, 3])
    disp = sp.integrate(v, (t, 0, T))
    neg, pos = -sp.integrate(v, (t, 0, r1)), sp.integrate(v, (t, r1, T))
    dist = neg + pos
    problem = (f'<p>A particle moves along a line with acceleration $a(t)={L(a)}$ m/s² and initial velocity $v(0)={v0}$ m/s.</p>'
               f'<p>(a) Find $v(t)$.<br>(b) Find the displacement and the total distance traveled for $0\\le t\\le{T}$.</p>')
    sol = (f'<p><strong>(a)</strong> $v(t)=\\int a\\,dt={L(v - v0)}+C$, and $v(0)={v0}$ gives $C={v0}$: $v(t)={L(v)}={L(sp.factor(v))}$.</p>'
           f'<p><strong>(b)</strong> Displacement: $\\int_0^{{{T}}}v\\,dt={L(disp)}$ m.</p>'
           f'<p>$v$ changes sign at $t={r1}$ (negative before, positive after), so split the distance there:</p>'
           f'\\[\\int_0^{{{T}}}|v|\\,dt=-\\int_0^{{{r1}}}v\\,dt+\\int_{{{r1}}}^{{{T}}}v\\,dt={L(neg)}+{L(pos)}={L(dist)}\\ \\text{{m}}.\\]')
    return {'problem': problem, 'answer': f'$v(t)={L(v)}$; displacement ${L(disp)}$ m; distance ${L(dist)}$ m', 'solution': sol,
            'data': {'v': v, 'a': a, 'v0': v0, 'T': T, 'root': r1, 'disp': disp, 'dist': dist}}


# ── differential equations ───────────────────────────────────────────
def chk_sep(d):
    s_, rhs = d['sol'], d['rhs']
    need(sp.simplify(s_.subs(x, 0) - d['y0']) == 0, 'initial condition')
    res = sp.diff(s_, x) - rhs.subs(y, s_)
    need(all(abs(complex(res.subs(x, p).evalf(25))) < 1e-14 for p in (0.05, 0.1, 0.2, 0.3)), 'solves the equation')


@template(course=C, chapter='differential_equations', id='m125-separable-ivp',
          title='A separable initial value problem',
          based_on={'exam': 'm125finalWin2016', 'problem': 9}, check=chk_sep)
def separable(rng):
    g = rng.choice([x * sp.cos(x ** 2), x * sp.exp(x ** 2), 2 * x, sp.cos(x), 3 * x ** 2, x * sp.sin(x ** 2)])
    G = sp.integrate(g, x)
    kind = rng.choice(['ydy', 'expneg', 'growth'])
    if kind == 'ydy':
        y0 = rng.choice([-3, -2, 2, 3])
        rhs = g / y
        Cc = sp.Rational(y0 * y0, 2) - G.subs(x, 0)
        sol = sp.sign(y0) * sp.sqrt(2 * G + 2 * Cc)
        work = (f'\\[y\\,dy={L(g)}\\,dx\\ \\Rightarrow\\ \\frac{{y^2}}{{2}}={L(G)}+C.\\]<p>$y(0)={y0}$ gives $C={L(Cc)}$. '
                f'Take the {"positive" if y0 > 0 else "negative"} square root, since $y(0)={y0}$:</p>')
        lhs = f'y\\,\\frac{{dy}}{{dx}}={L(g)}'
    elif kind == 'expneg':
        y0 = rng.choice([0, 1, -1, 2])
        rhs = g * sp.exp(y)
        Cc = -sp.exp(-y0) - G.subs(x, 0)
        sol = -sp.log(-(G + Cc))
        work = (f'\\[e^{{-y}}dy={L(g)}\\,dx\\ \\Rightarrow\\ -e^{{-y}}={L(G)}+C.\\]<p>$y(0)={y0}$ gives $C={L(Cc)}$. Solve for $y$:</p>')
        lhs = f'\\frac{{dy}}{{dx}}={L(g)}\\,e^{{y}}'
    else:
        y0 = nz(rng, -3, 4)
        rhs = g * y
        sol = y0 * sp.exp(G - G.subs(x, 0))
        work = (f'\\[\\frac{{dy}}{{y}}={L(g)}\\,dx\\ \\Rightarrow\\ \\ln|y|={L(G)}+C\\ \\Rightarrow\\ y=Ae^{{{L(G)}}}.\\]'
                f'<p>$y(0)={y0}$ gives $A={L(y0 * sp.exp(-G.subs(x, 0)))}$:</p>')
        lhs = f'\\frac{{dy}}{{dx}}={L(g)}\\,y'
    problem = f'<p>Solve the initial value problem</p>\\[{lhs},\\qquad y(0)={y0}.\\]'
    sol_tex = f'<p>Separate the variables and integrate both sides:</p>{work}\\[y={L(sol)}.\\]'
    return {'problem': problem, 'answer': f'$y={L(sol)}$', 'solution': sol_tex, 'data': {'sol': sol, 'rhs': rhs, 'y0': y0}}


def chk_cool(d):
    A, T0, k = d['A'], d['T0'], d['k']
    T = lambda s_: A + (T0 - A) * mpmath.exp(-k * s_)
    need(close(T(d['t1']), d['T1'], 1e-12), 'matches the measurement')
    need(close(T(d['t2']), d['T2'], 1e-9), 'time to reach the target temperature')


@template(course=C, chapter='differential_equations', id='m125-newton-cooling',
          title="Newton's law of cooling",
          based_on={'exam': 'm125finalAut2015', 'problem': 10}, check=chk_cool)
def cooling(rng):
    A = rng.choice([20, 22, 4, 70])
    T0 = A + rng.choice([60, 80, -15, 50])
    t1 = rng.choice([5, 10, 4])
    frac = rng.choice([sp.Rational(1, 2), sp.Rational(3, 4), sp.Rational(5, 7), sp.Rational(2, 3)])
    T1 = A + (T0 - A) * frac
    T2 = A + (T0 - A) * rng.choice([sp.Rational(1, 4), sp.Rational(1, 5), sp.Rational(1, 10)])
    k = sp.log(1 / frac) / t1
    t2 = sp.log((T0 - A) / (T2 - A)) / k
    problem = (f'<p>An object at ${T0}$°C is placed in a room kept at ${A}$°C. After ${t1}$ minutes its temperature is ${L(T1)}$°C. '
               f'By Newton\'s law of cooling, $T\'=-k(T-{A})$. When will the object be at ${L(T2)}$°C?</p>')
    sol = (f'<p>The solution of $T\'=-k(T-{A})$ is $T(t)={A}+(T_0-{A})e^{{-kt}}={A}+({L(T0 - A)})e^{{-kt}}$.</p>'
           f'<p>Use the measurement: ${L(T1)}={A}+({L(T0 - A)})e^{{-{t1}k}}$, so $e^{{-{t1}k}}={L(frac)}$ and $k=\\dfrac{{\\ln\\left({L(1 / frac)}\\right)}}{{{t1}}}\\approx{float(k):.5f}$ per minute.</p>'
           f'<p>Now solve ${L(T2)}={A}+({L(T0 - A)})e^{{-kt}}$: $e^{{-kt}}={L((T2 - A) / (T0 - A))}$, so</p>'
           f'\\[t=\\frac{{\\ln {L((T0 - A) / (T2 - A))}}}{{k}}={t1}\\cdot\\frac{{\\ln {L((T0 - A) / (T2 - A))}}}{{\\ln\\left({L(1 / frac)}\\right)}}\\approx{float(t2):.2f}\\ \\text{{minutes}}.\\]')
    return {'problem': problem, 'answer': f'$t\\approx{float(t2):.2f}$ minutes', 'solution': sol,
            'data': {'A': A, 'T0': T0, 'k': float(k), 't1': t1, 'T1': float(T1), 't2': float(t2), 'T2': float(T2)}}


def chk_mix(d):
    yv = d['y']
    need(all(abs(float((sp.diff(yv, t) - (d['rate'] * d['cin'] - d['rate'] * yv / d['V'])).subs(t, p))) < 1e-12 for p in (0.5, 3, 10)), 'equation')
    need(sp.simplify(yv.subs(t, 0) - d['y0']) == 0, 'initial amount')
    need(abs(float(yv.subs(t, d['T'])) - d['yT']) < 0.005, 'amount at time T (rounded)')


@template(course=C, chapter='mixing_and_air_resistance', id='m125-mixing',
          title='A salt-mixing tank with constant volume',
          based_on={'exam': 'm125finalWin2015', 'problem': 10}, check=chk_mix)
def mixing(rng):
    V, rate, cin = rng.choice([20, 50, 100, 200]), rng.choice([2, 4, 5, 10]), rng.choice([1, 2, 3, 5])
    y0, T = rng.choice([0, 10, 20, 100]), rng.choice([10, 20, 30])
    eq = V * cin
    if y0 == eq:
        raise Reject
    yv = eq + (y0 - eq) * sp.exp(-sp.Rational(rate, V) * t)
    yT = round(float(yv.subs(t, T)), 2)
    problem = (f'<p>A tank holds ${V}$ L of brine containing ${y0}$ g of salt. Brine with ${cin}$ g/L of salt flows in at ${rate}$ L/min, '
               f'and the well-mixed solution flows out at the same rate.</p>'
               f'<p>(a) Find the amount of salt $y(t)$ after $t$ minutes.<br>(b) How much salt is there after ${T}$ minutes, and in the long run?</p>')
    sol = (f'<p><strong>(a)</strong> Salt in: ${rate}\\cdot{cin}={rate * cin}$ g/min. Salt out: ${rate}\\cdot\\frac{{y}}{{{V}}}$ g/min. So</p>'
           f'\\[\\frac{{dy}}{{dt}}={rate * cin}-\\frac{{{rate}}}{{{V}}}y=-{L(sp.Rational(rate, V))}\\left(y-{eq}\\right),\\qquad y(0)={y0}.\\]'
           f'<p>So $y-{eq}$ decays exponentially: $y-{eq}=({y0 - eq})e^{{-{L(sp.Rational(rate, V))}t}}$, i.e. $y(t)={L(yv)}$.</p>'
           f'<p><strong>(b)</strong> $y({T})={L(yv.subs(t, T))}\\approx{yT:.2f}$ g. As $t\\to\\infty$ the exponential dies out, so $y\\to{eq}$ g.</p>')
    return {'problem': problem, 'answer': f'$y(t)={L(yv)}$; $y({T})\\approx{yT:.2f}$ g; long run ${eq}$ g', 'solution': sol,
            'data': {'y': yv, 'rate': rate, 'cin': cin, 'V': V, 'y0': y0, 'T': T, 'yT': yT}}

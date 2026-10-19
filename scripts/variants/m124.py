"""Math 124 (Calculus I) practice-problem templates. See common.py for the contract.

Checks recompute each answer another way: numerical limits and derivatives,
root-finding (implicit curves, related rates), dense sampling for extrema and
sign charts, and direct substitution (tangency, self-intersection).
"""
import math
import mpmath
import sympy as sp

from common import template, Reject, need, close, nz

C = 'Math 124'
x, y, t, a_ = sp.symbols('x y t a', real=True)


def L(e):
    return sp.latex(e, ln_notation=True)


def nderiv(f, p):
    return mpmath.diff(sp.lambdify(x, f, 'mpmath'), p)


def line_tex(m, x0, y0):
    """y = m(x - x0) + y0, simplified."""
    return f'y={L(sp.expand(m * (x - x0) + y0))}'


# ── limits and continuity ────────────────────────────────────────────
def chk_limit(d):
    f, pt = d['f'], d['pt']
    if pt in (sp.oo, -sp.oo):
        need(sp.limit(f, x, pt) == d['L'], 'limit (SymPy)')
    else:
        need(sp.limit(f, x, pt, '+-') == d['L'], 'limit (SymPy)')
    fn = sp.lambdify(x, f, 'mpmath')
    with mpmath.workdps(40):
        if pt in (sp.oo, -sp.oo):
            v = fn(mpmath.mpf(10) ** 12 * (1 if pt == sp.oo else -1))
        else:
            p0 = mpmath.mpf(str(pt))
            v = (fn(p0 + mpmath.mpf(10) ** -12) + fn(p0 - mpmath.mpf(10) ** -12)) / 2
        need(abs(v - mpmath.mpf(str(sp.N(d['L'], 40)))) < 1e-6, 'limit (numerical)')


@template(course=C, chapter='limit_of_a_function', id='m124-limit-at-infinity',
          title='A limit at infinity with a square root',
          based_on={'exam': 'm124mid1Aut2011_Nichifor', 'problem': 1}, check=chk_limit)
def limit_infinity(rng):
    a, b = rng.choice([1, 4, 9, 16]), rng.randint(-6, 6)
    c, e = nz(rng, -5, 5), rng.randint(-12, 12)
    direction = rng.choice([sp.oo, sp.oo, -sp.oo])
    f = sp.sqrt(a * x ** 2 + b * x) / (c * x + e)
    Lval = sp.limit(f, x, direction)
    ra = math.isqrt(a)
    neg = '' if direction == sp.oo else '-'
    inner = f'{a}{"+" if b >= 0 else "-"}\\frac{{{abs(b)}}}{{x}}'
    problem = f'<p>Evaluate</p>\\[\\lim_{{x\\to{neg}\\infty}}{L(f)}.\\]'
    sol = (f'<p>Factor the largest power of $x$ out of the square root. Since $\\sqrt{{x^2}}=|x|$, which is ${neg}x$ for {"large positive" if not neg else "large negative"} $x$:</p>'
           f'\\[\\sqrt{{{L(a * x ** 2 + b * x)}}}=|x|\\sqrt{{{inner}}}={neg}x\\sqrt{{{inner}}}.\\]'
           f'<p>Divide the denominator by $x$ as well:</p>'
           f'\\[\\lim_{{x\\to{neg}\\infty}}{L(f)}=\\lim_{{x\\to{neg}\\infty}}\\frac{{{neg}\\sqrt{{{inner}}}}}{{{c}{"+" if e >= 0 else "-"}\\frac{{{abs(e)}}}{{x}}}}=\\frac{{{neg}{ra}}}{{{c}}}={L(Lval)}.\\]')
    return {'problem': problem, 'answer': f'${L(Lval)}$', 'solution': sol, 'data': {'f': f, 'pt': direction, 'L': Lval}}


@template(course=C, chapter='limit_of_a_function', id='m124-limit-indeterminate',
          title='Limits of indeterminate forms',
          based_on={'exam': 'm124finalAut2025', 'problem': 1}, check=chk_limit)
def limit_indeterminate(rng):
    fam = rng.choice(['factor', 'conjugate', 'log', 'trig'])
    if fam == 'factor':
        r, s_, q = rng.randint(-4, 4), rng.randint(-5, 5), rng.randint(-5, 5)
        if s_ == r or q == r or s_ == q:
            raise Reject
        f = sp.expand((x - r) * (x - s_)) / sp.expand((x - r) * (x - q))
        pt, Lval = r, sp.Rational(r - s_, r - q)
        sol = (f'<p>Plugging in $x={r}$ gives $\\frac00$. Factor and cancel the common factor ${L(x - r)}$:</p>'
               f'\\[\\lim_{{x\\to{r}}}\\frac{{{L((x - r) * (x - s_))}}}{{{L((x - r) * (x - q))}}}=\\lim_{{x\\to{r}}}\\frac{{{L(x - s_)}}}{{{L(x - q)}}}=\\frac{{{r - s_}}}{{{r - q}}}={L(Lval)}.\\]')
    elif fam == 'conjugate':
        k, c = rng.choice([1, 2, 3, 4, 5]), rng.choice([1, 2, 3])
        f = (sp.sqrt(c * x + k * k) - k) / x
        pt, Lval = 0, sp.Rational(c, 2 * k)
        rt = f'\\sqrt{{{L(c * x + k * k)}}}'
        sol = (f'<p>Plugging in $x=0$ gives $\\frac00$. Multiply by the conjugate:</p>'
               f'\\[\\frac{{{rt}-{k}}}{{x}}\\cdot\\frac{{{rt}+{k}}}{{{rt}+{k}}}=\\frac{{{L(c * x)}}}{{x\\left({rt}+{k}\\right)}}=\\frac{{{c}}}{{{rt}+{k}}}.\\]'
               f'<p>Now let $x\\to0$: $\\dfrac{{{c}}}{{{k}+{k}}}={L(Lval)}$.</p>')
    elif fam == 'log':
        k, m = rng.choice([1, 2, 3, 5]), rng.choice([1, 2, 3])
        f = m * x * sp.log(x + k) - m * x * sp.log(x)
        pt, Lval = sp.oo, sp.Integer(m * k)
        mm = m if m > 1 else ''
        sol = (f'<p>This is $\\infty-\\infty$. Combine the logarithms: ${L(f)}={mm}x\\ln\\left(1+\\frac{{{k}}}{{x}}\\right)=\\dfrac{{{mm}\\ln\\left(1+\\frac{{{k}}}{{x}}\\right)}}{{1/x}}$, '
               f'which is $\\frac00$ as $x\\to\\infty$. With $u=\\frac1x\\to0^+$ this is $\\dfrac{{{mm}\\ln(1+{k}u)}}{{u}}$, and by L\'Hôpital\'s rule</p>'
               f'\\[\\lim_{{u\\to0^+}}\\frac{{{mm}\\ln(1+{k}u)}}{{u}}=\\lim_{{u\\to0^+}}\\frac{{{m * k}}}{{1+{k}u}}={m * k}.\\]')
    else:
        k, m = rng.choice([2, 3, 4, 5]), rng.choice([1, 2, 3, 6])
        f = sp.sin(k * x) / (m * x)
        pt, Lval = 0, sp.Rational(k, m)
        sol = (f'<p>Use $\\lim_{{u\\to0}}\\frac{{\\sin u}}{{u}}=1$ with $u={k}x$:</p>'
               f'\\[\\lim_{{x\\to0}}\\frac{{\\sin {k}x}}{{{m if m > 1 else ""}x}}=\\frac{{{k}}}{{{m}}}\\lim_{{x\\to0}}\\frac{{\\sin {k}x}}{{{k}x}}={L(Lval)}.\\]')
    ptex = '\\infty' if pt == sp.oo else str(pt)
    problem = f'<p>Evaluate</p>\\[\\lim_{{x\\to{ptex}}}\\left({L(f)}\\right).\\]'
    return {'problem': problem, 'answer': f'${L(Lval)}$', 'solution': sol, 'data': {'f': f, 'pt': pt, 'L': Lval}}


def chk_cont(d):
    f1, f2, f3, p1, p2 = d['f1'], d['f2'], d['f3'], d['p1'], d['p2']
    need(sp.limit(f1, x, p1, '-') == sp.limit(f2, x, p1, '+') == f2.subs(x, p1), f'continuous at x={p1}')
    need(sp.limit(f2, x, p2, '-') == sp.limit(f3, x, p2, '+') == f3.subs(x, p2), f'continuous at x={p2}')


@template(course=C, chapter='continuity', id='m124-continuity-constants',
          title='Choose constants to make a piecewise function continuous',
          based_on={'exam': 'm124mid1Aut2011_Nichifor', 'problem': 4}, check=chk_cont)
def continuity(rng):
    A, B = sp.symbols('a b')
    p1, p2 = sorted(rng.sample([-1, 1, 2, 3], 2))
    g1 = rng.choice([x ** 2, 2 * x, x ** 3, 3 * x + 1])
    c0 = rng.randint(-3, 3)
    g3 = rng.choice([4, 6, 8, 12]) / (x + rng.choice([1, 2, 3]))
    if not g3.subs(x, p2).is_finite:
        raise Reject
    bv = sp.Rational(g3.subs(x, p2) - c0) / p2
    av = bv * p1 + c0 - g1.subs(x, p1)
    f1, f2, f3 = g1 + av, bv * x + c0, g3
    problem = (f'<p>Find the values of $a$ and $b$ that make $f$ continuous everywhere:</p>'
               f'\\[f(x)=\\begin{{cases}}{L(g1 + A)}, & x<{p1}\\\\ {L(B * x + c0)}, & {p1}\\le x<{p2}\\\\ {L(g3)}, & x\\ge {p2}\\end{{cases}}\\]')
    sol = (f'<p>Each piece is continuous on its own interval, so we only need the pieces to agree at the break points.</p>'
           f'<p>At $x={p2}$: the middle piece gives ${L(B * p2 + c0)}$ and the right piece gives ${L(g3.subs(x, p2))}$. So ${L(B * p2 + c0)}={L(g3.subs(x, p2))}$ and $b={L(bv)}$.</p>'
           f'<p>At $x={p1}$: the left piece gives ${L(g1.subs(x, p1) + A)}$ and the middle piece gives ${L(bv * p1 + c0)}$. So $a={L(av)}$.</p>'
           f'<p>Check: $\\lim_{{x\\to{p1}^-}}f=\\lim_{{x\\to{p1}^+}}f={L(f2.subs(x, p1))}$ and $\\lim_{{x\\to{p2}^-}}f=\\lim_{{x\\to{p2}^+}}f={L(f3.subs(x, p2))}$.</p>')
    return {'problem': problem, 'answer': f'$a={L(av)}$, $b={L(bv)}$', 'solution': sol,
            'data': {'f1': f1, 'f2': f2, 'f3': f3, 'p1': p1, 'p2': p2}}


# ── derivatives and tangent lines ────────────────────────────────────
INNER = [lambda r: x ** 2 + r.choice([1, 3]), lambda r: sp.sin(x), lambda r: r.choice([2, 3]) * x + 1, lambda r: sp.exp(x)]


def chk_dval(d):
    need(close(nderiv(d['f'], float(d['a'])), sp.N(d['val'], 25), 1e-10), "f'(a) (numerical derivative)")


@template(course=C, chapter='derivatives_and_rates_of_change', id='m124-derivative-rules',
          title="Differentiate with the product, quotient and chain rules; evaluate f′(a)",
          based_on={'exam': 'm124mid2Aut2011_Nichifor', 'problem': 1}, check=chk_dval)
def derivative_rules(rng):
    g = rng.choice(INNER)(rng)
    outer = rng.choice(['sqrt', 'ln', 'sin', 'power', 'exp'])
    h = {'sqrt': sp.sqrt(g), 'ln': sp.log(g), 'sin': sp.sin(g), 'power': g ** rng.choice([3, 4, -1]), 'exp': sp.exp(g)}[outer]
    combo = rng.choice(['product', 'quotient', 'plain'])
    other = rng.choice([x, x ** 2, 1 + x])
    f = {'product': other * h, 'quotient': h / other, 'plain': h}[combo]
    a = rng.choice([0, 1, 2]) if combo != 'quotient' else rng.choice([1, 2])
    gv = g.subs(x, a)
    if (outer in ('ln', 'sqrt') and gv <= 0) or (outer == 'power' and gv == 0):
        raise Reject
    fp = sp.diff(f, x)
    val = sp.simplify(fp.subs(x, a))
    if not val.is_finite:
        raise Reject
    rule = {'product': 'product rule $(uv)\'=u\'v+uv\'$, with the chain rule for the second factor',
            'quotient': 'quotient rule $\\left(\\frac uv\\right)\'=\\frac{u\'v-uv\'}{v^2}$, with the chain rule for the numerator', 'plain': 'chain rule'}[combo]
    approx = '' if val.is_Rational else f'\\approx{float(val):.4f}'
    problem = f'<p>Let $f(x)={L(f)}$. Find $f\'(x)$ and $f\'({a})$.</p>'
    sol = (f'<p>The inner function is $g(x)={L(g)}$ with $g\'(x)={L(sp.diff(g, x))}$, so by the chain rule $\\frac{{d}}{{dx}}\\left[{L(h)}\\right]={L(sp.diff(h, x))}$.</p>'
           f'<p>Using the {rule}:</p>\\[f\'(x)={L(fp)}.\\]<p>At $x={a}$:</p>\\[f\'({a})={L(val)}{approx}.\\]')
    return {'problem': problem, 'answer': f"$f'({a})={L(val)}$", 'solution': sol, 'data': {'f': f, 'a': a, 'val': val}}


def chk_tangent(d):
    need(close(nderiv(d['f'], float(d['a'])), sp.N(d['m'], 25), 1e-10), 'slope (numerical derivative)')
    need(sp.simplify(d['f'].subs(x, d['a']) - d['y0']) == 0, 'point on the curve')


@template(course=C, chapter='lines_circles_and_tangents', id='m124-tangent-line',
          title='Tangent line to a curve',
          based_on={'exam': 'm124mid1Aut2011_Nichifor', 'problem': 2}, check=chk_tangent)
def tangent_line(rng):
    a = rng.choice([1, 8, 1, 4])
    pows = rng.sample([sp.Rational(-1, 3), sp.Rational(1, 2), sp.Integer(-1), sp.Rational(2, 3), sp.Integer(2), sp.Rational(-1, 2)], 2)
    cs = [nz(rng, -4, 7) for _ in pows]
    f = sum(c * x ** p for c, p in zip(cs, pows)) + rng.randint(-3, 5)
    y0 = sp.simplify(f.subs(x, a))
    fp = sp.diff(f, x)
    m = sp.simplify(fp.subs(x, a))
    if not (y0.is_rational and m.is_rational):
        raise Reject
    problem = f'<p>Find an equation of the tangent line to $y={L(f)}$ at the point where $x={a}$.</p>'
    sol = (f'<p>At $x={a}$: $y={L(y0)}$. Using the power rule on each term, $y\'={L(fp)}$, so the slope is $y\'({a})={L(m)}$.</p>'
           f'<p>Point-slope form through $({a},{L(y0)})$: $y-\\left({L(y0)}\\right)={L(m)}(x-{a})$, i.e.</p>\\[{line_tex(m, a, y0)}.\\]')
    return {'problem': problem, 'answer': f'${line_tex(m, a, y0)}$', 'solution': sol, 'data': {'f': f, 'a': a, 'm': m, 'y0': y0}}


def chk_through(d):
    f, (h, k) = d['f'], d['pt']
    for m, b in d['lines']:
        need(m * h + b == k, 'line passes through the given point')
        need(sp.discriminant(sp.Poly(sp.expand(f - (m * x + b)), x)) == 0, 'line is tangent (double root)')


@template(course=C, chapter='lines_circles_and_tangents', id='m124-tangent-through-point',
          title='Tangent lines to a parabola through a point not on it',
          based_on={'exam': 'm124mid1Aut2011_Nichifor', 'problem': 6}, check=chk_through)
def tangent_through(rng):
    p, q = rng.randint(-3, 3), rng.randint(-3, 3)
    a1, a2 = sorted(rng.sample(range(-3, 5), 2))
    if (a1 + a2) % 2:
        raise Reject
    h = (a1 + a2) // 2
    k = p * h + q + a1 * a2
    f = x ** 2 + p * x + q
    lines = [(2 * a + p, sp.expand(f.subs(x, a) - (2 * a + p) * a)) for a in (a1, a2)]
    slope = f'2a{"+" if p >= 0 else "-"}{abs(p)}' if p else '2a'
    problem = f'<p>Find equations of both lines that pass through the point $({h},{k})$ and are tangent to the parabola $y={L(f)}$.</p>'
    sol = (f'<p>Let the point of tangency be $\\left(a,\\ {L(f.subs(x, a_))}\\right)$. The slope there is $y\'(a)={slope}$, so the tangent line is</p>'
           f'\\[y-\\left({L(f.subs(x, a_))}\\right)=\\left({slope}\\right)(x-a).\\]'
           f'<p>It must pass through $({h},{k})$. Substituting $x={h}$, $y={k}$ and simplifying gives</p>'
           f'\\[{L(sp.expand(a_ ** 2 - 2 * h * a_ + a1 * a2))}=0\\quad\\Longrightarrow\\quad {L(sp.factor(a_ ** 2 - 2 * h * a_ + a1 * a2))}=0,\\]'
           f'<p>so $a={a1}$ or $a={a2}$:</p><ul>'
           + ''.join(f'<li>$a={aa}$: slope ${m}$, line $y={L(m * x + b)}$.</li>' for aa, (m, b) in zip((a1, a2), lines)) + '</ul>')
    return {'problem': problem, 'answer': ' and '.join(f'$y={L(m * x + b)}$' for m, b in lines), 'solution': sol,
            'data': {'f': f, 'pt': (h, k), 'lines': lines}}


def chk_implicit(d):
    F, (x0, y0) = d['F'], d['pt']
    Fn = sp.lambdify((x, y), F, 'mpmath')
    yof = lambda X: mpmath.findroot(lambda Y: Fn(X, Y), y0)
    need(close(mpmath.diff(yof, x0), sp.N(d['m'], 25), 1e-8), 'dy/dx (numerical, solving for y)')


@template(course=C, chapter='implicit_differentiation', id='m124-implicit-tangent',
          title='Implicit differentiation and a tangent line',
          based_on={'exam': 'm124mid2Win2023', 'problem': 5}, check=chk_implicit)
def implicit_tangent(rng):
    A, B, Cc = rng.choice([1, 2, 3]), rng.randint(-4, 4), rng.choice([1, 2, 4, 8])
    x0, y0 = rng.randint(-2, 2), nz(rng, -2, 2)
    lhs = A * x ** 2 + B * x * y + Cc * y ** 2
    D = lhs.subs({x: x0, y: y0})
    if D <= 0:
        raise Reject
    F = lhs - D
    Fx, Fy = sp.diff(F, x), sp.diff(F, y)
    if Fy.subs({x: x0, y: y0}) == 0:
        raise Reject
    dydx = sp.simplify(-Fx / Fy)
    m = sp.simplify(dydx.subs({x: x0, y: y0}))
    problem = f'<p>The point $({x0},{y0})$ lies on the curve ${L(lhs)}={D}$. Find $\\dfrac{{dy}}{{dx}}$ and the tangent line at that point.</p>'
    sol = (f'<p>Differentiate both sides with respect to $x$, treating $y$ as a function of $x$ (product rule on the $xy$ term, chain rule on $y^2$):</p>'
           f'\\[{L(Fx)}+\\left({L(Fy)}\\right)y\'=0\\quad\\Longrightarrow\\quad y\'={L(dydx)}.\\]'
           f'<p>At $({x0},{y0})$: $y\'={L(m)}$. The tangent line is</p>\\[{line_tex(m, x0, y0)}.\\]')
    return {'problem': problem, 'answer': f"$y'={L(dydx)}$; ${line_tex(m, x0, y0)}$", 'solution': sol,
            'data': {'F': F, 'pt': (x0, y0), 'm': m}}


def chk_linapprox(d):
    f, a, X = d['f'], d['a'], d['X']
    need(close(nderiv(f, a), sp.N(d['m'], 25), 1e-10), "f'(a)")
    need(close(float(f.subs(x, a)) + float(d['m']) * (X - a), float(d['est']), 1e-12), 'L(X)')
    need(abs(float(f.subs(x, X)) - float(d['est'])) < 0.05 * max(1, abs(float(d['est']))), 'estimate is close to the true value')


@template(course=C, chapter='linear_approximation_and_differentials', id='m124-linear-approximation',
          title='Estimate a value with a linear approximation',
          based_on={'exam': 'm124finalAut2025', 'problem': 3}, check=chk_linapprox)
def linear_approximation(rng):
    nroot, a = rng.choice([(3, 8), (3, 27), (2, 25), (2, 16), (2, 9), (3, 64), (4, 16), (2, 4)])
    f = x ** sp.Rational(1, nroot)
    dx = rng.choice([sp.Rational(1, 10), sp.Rational(-1, 10), sp.Rational(1, 5), sp.Rational(-1, 5), sp.Rational(1, 2)])
    X = a + dx
    fa = sp.Integer(round(a ** (1 / nroot)))
    m = sp.Rational(1, nroot) * sp.Integer(a) ** (sp.Rational(1, nroot) - 1)
    est = fa + m * dx
    root = f'\\sqrt{{{float(X):g}}}' if nroot == 2 else f'\\sqrt[{nroot}]{{{float(X):g}}}'
    problem = f'<p>Use the linear approximation of $f(x)={L(f)}$ at $a={a}$ to estimate ${root}$.</p>'
    sol = (f'<p>$f({a})={L(fa)}$ and $f\'(x)=\\frac{{1}}{{{nroot}}}x^{{{L(sp.Rational(1, nroot) - 1)}}}$, so $f\'({a})={L(m)}$.</p>'
           f'\\[L(x)=f({a})+f\'({a})(x-{a})={L(fa)}+{L(m)}(x-{a}).\\]'
           f'\\[{root}\\approx L({float(X):g})={L(fa)}+{L(m)}\\left({L(dx)}\\right)={L(est)}\\approx{float(est):.5f}.\\]'
           f'<p>(The true value is about ${float(X) ** (1 / nroot):.5f}$.)</p>')
    return {'problem': problem, 'answer': f'${root}\\approx{L(est)}\\approx{float(est):.5f}$', 'solution': sol,
            'data': {'f': f, 'a': a, 'X': float(X), 'm': m, 'est': est}}


# ── related rates ────────────────────────────────────────────────────
def chk_cone(d):
    R, H, Q, h0 = d['R'], d['H'], d['Q'], d['h0']
    vol = lambda h: mpmath.pi * (R * h / H) ** 2 * h / 3
    V0 = vol(h0)
    hof = lambda s_: mpmath.findroot(lambda h: vol(h) - (V0 + Q * s_), h0)
    need(close(mpmath.diff(hof, 0), float(d['dh']), 1e-8), 'dh/dt (numerical)')


@template(course=C, chapter='related_rates', id='m124-related-rates-cone',
          title='Related rates: filling or draining a conical tank',
          based_on={'exam': 'm124mid2Aut2012_LovelessH', 'problem': 4}, check=chk_cone)
def related_cone(rng):
    R, H = rng.choice([(2, 8), (3, 6), (4, 12), (5, 10), (1, 3), (6, 9)])
    Q = rng.choice([2, 3, 5, 9, -4, -2])
    h0 = rng.randint(1, H - 1)
    k = sp.Rational(R, H)
    dh = sp.Rational(Q) / (sp.pi * k ** 2 * h0 ** 2)
    word = 'pumped into' if Q > 0 else 'drains out of'
    problem = (f'<p>Water is {word} a conical tank (vertex down) at ${abs(Q)}$ m³/min. The tank is ${H}$ m tall and its top has radius ${R}$ m. '
               f'How fast is the water level {"rising" if Q > 0 else "falling"} when the water is ${h0}$ m deep?</p>')
    sol = (f'<p>Let $h$ be the depth and $r$ the radius of the water surface. By similar triangles $\\frac{{r}}{{h}}=\\frac{{{R}}}{{{H}}}$, so $r={L(k)}h$ and</p>'
           f'\\[V=\\frac{{\\pi}}{{3}}r^2h=\\frac{{\\pi}}{{3}}\\left({L(k)}h\\right)^2h={L(sp.pi * k ** 2 / 3)}h^3.\\]'
           f'<p>Differentiate with respect to $t$: $\\dfrac{{dV}}{{dt}}={L(sp.pi * k ** 2)}h^2\\dfrac{{dh}}{{dt}}$. With $\\frac{{dV}}{{dt}}={Q}$ and $h={h0}$:</p>'
           f'\\[\\frac{{dh}}{{dt}}=\\frac{{{Q}}}{{{L(sp.pi * k ** 2)}\\cdot{h0}^2}}={L(dh)}\\approx{float(dh):.4f}\\ \\text{{m/min}}.\\]')
    return {'problem': problem, 'answer': f'$\\frac{{dh}}{{dt}}={L(dh)}\\approx{float(dh):.4f}$ m/min', 'solution': sol,
            'data': {'R': R, 'H': H, 'Q': Q, 'h0': h0, 'dh': float(dh)}}


# ── extrema, graph shape, optimization ───────────────────────────────
def chk_absext(d):
    f = sp.lambdify(x, d['f'], 'math')
    a, b = d['a'], d['b']
    vals = [f(a + (b - a) * i / 20000) for i in range(20001)]
    need(max(vals) <= float(d['max']) + 1e-9 and min(vals) >= float(d['min']) - 1e-9, 'no sampled value beats the claimed extremes')
    need(close(f(float(d['max_at'])), float(d['max']), 1e-12) and close(f(float(d['min_at'])), float(d['min']), 1e-12), 'values at the claimed points')


@template(course=C, chapter='maximum_and_minimum_values', id='m124-absolute-extrema',
          title='Absolute extrema on a closed interval',
          based_on={'exam': 'm124mid2Aut2011_LovelessH', 'problem': 3}, check=chk_absext)
def absolute_extrema(rng):
    if rng.random() < 0.5:
        r1, r2 = sorted(rng.sample(range(-3, 4), 2))
        f = sp.expand(rng.choice([1, 2]) * sp.integrate(6 * (x - r1) * (x - r2), x)) + rng.randint(-5, 5)   # critical points r1, r2
        a, b = r1 - rng.choice([1, 2]), r2 + rng.choice([0, 1, 2])
    else:
        f = x ** 2 - rng.choice([4, 6, 8]) * sp.log(x ** 2 + 1)
        a, b = rng.choice([-2, -1, 0]), rng.choice([2, 3])
    fp = sp.diff(f, x)
    crit = sorted({r for r in sp.solve(sp.Eq(fp, 0), x) if r.is_real and a < r < b}, key=float)
    cands = [(sp.nsimplify(p), sp.simplify(f.subs(x, p))) for p in [a] + crit + [b]]
    mx = max(cands, key=lambda q: float(q[1]))
    mn = min(cands, key=lambda q: float(q[1]))
    table = ''.join(f'<tr><td>${L(p)}$</td><td>${L(v)}$</td><td>{float(v):.4f}</td></tr>' for p, v in cands)
    problem = f'<p>Find the absolute maximum and minimum values of $f(x)={L(f)}$ on $[{a},{b}]$.</p>'
    sol = (f'<p>$f\'(x)={L(sp.factor(fp))}$. Critical numbers in $({a},{b})$: {", ".join(f"${L(p)}$" for p in crit) if crit else "none"}.</p>'
           f'<p>Evaluate $f$ at the critical numbers and at the endpoints:</p>'
           f'<table class="variant-table"><tr><th>$x$</th><th>$f(x)$</th><th>≈</th></tr>{table}</table>'
           f'<p>Absolute maximum ${L(mx[1])}$ at $x={L(mx[0])}$; absolute minimum ${L(mn[1])}$ at $x={L(mn[0])}$.</p>')
    return {'problem': problem, 'answer': f'max ${L(mx[1])}$ at $x={L(mx[0])}$; min ${L(mn[1])}$ at $x={L(mn[0])}$', 'solution': sol,
            'data': {'f': f, 'a': a, 'b': b, 'max': mx[1], 'min': mn[1], 'max_at': mx[0], 'min_at': mn[0]}}


INF = 1e12


def sample_pts(lo, hi):
    if lo <= -INF and hi >= INF:
        return [-30, -3, 0, 3, 30]
    if lo <= -INF:
        return [hi - 0.5, hi - 5, hi - 50]
    if hi >= INF:
        return [lo + 0.5, lo + 5, lo + 50]
    return [lo + (hi - lo) * s_ for s_ in (0.1, 0.5, 0.9)]


def chk_shape(d):
    fp, fpp = (sp.lambdify(x, sp.diff(d['f'], x, k), 'math') for k in (1, 2))
    for (lo, hi), up in d['inc']:
        need(all((fp(p) > 0) == up for p in sample_pts(lo, hi)), 'increasing/decreasing intervals')
    for (lo, hi), cu in d['conc']:
        need(all((fpp(p) > 0) == cu for p in sample_pts(lo, hi)), 'concavity intervals')


@template(course=C, chapter='derivatives_and_shapes_of_graphs', id='m124-curve-sketching',
          title='Increasing/decreasing, local extrema, concavity and inflection points',
          based_on={'exam': 'm124finalAut2025', 'problem': 8}, check=chk_shape)
def curve_sketching(rng):
    r1, r2 = sorted(rng.sample(range(-3, 4), 2))
    if rng.random() < 0.5:
        f = sp.expand(sp.integrate(6 * (x - r1) * (x - r2), x))                # cubic, critical points r1, r2
    else:
        r3 = rng.choice([q for q in range(-3, 4) if q not in (r1, r2)])
        f = sp.expand(sp.integrate(4 * (x - r1) * (x - r2) * (x - r3), x))     # quartic, three critical points
    f = rng.choice([1, -1]) * f
    fp, fpp = sp.diff(f, x), sp.diff(f, x, 2)
    crit = sorted(sp.solve(fp, x), key=float)
    infl = sorted((r for r in sp.solve(fpp, x) if r.is_real), key=float)
    def ivs(bps):
        edges = [-INF] + [float(b) for b in bps] + [INF]
        return list(zip(edges[:-1], edges[1:]))
    inc = [(iv, fp.subs(x, sample_pts(*iv)[0]) > 0) for iv in ivs(crit)]
    conc = [(iv, fpp.subs(x, sample_pts(*iv)[0]) > 0) for iv in ivs(infl)]
    def fmt(lo, hi):
        left = '-\\infty' if lo <= -INF else L(sp.nsimplify(lo))
        right = '\\infty' if hi >= INF else L(sp.nsimplify(hi))
        return f'({left},{right})'
    cup = lambda xs: '\\cup'.join(xs) or '\\varnothing'
    up = cup([fmt(*iv) for iv, s_ in inc if s_])
    down = cup([fmt(*iv) for iv, s_ in inc if not s_])
    cu = cup([fmt(*iv) for iv, s_ in conc if s_])
    cd = cup([fmt(*iv) for iv, s_ in conc if not s_])
    ext = [f'local {"max" if inc[i][1] else "min"} at $x={L(c)}$' for i, c in enumerate(crit) if inc[i][1] != inc[i + 1][1]]
    infl_real = [p for i, p in enumerate(infl) if conc[i][1] != conc[i + 1][1]]
    infl_tex = ', '.join(f'$x={L(p)}$' for p in infl_real) or 'none'
    problem = (f'<p>Let $f(x)={L(f)}$. Find the intervals where $f$ is increasing and decreasing, its local extrema, '
               f'the intervals where it is concave up and concave down, and its inflection points.</p>')
    sol = (f'<p>$f\'(x)={L(sp.factor(fp))}$, which is zero at $x={", ".join(L(c) for c in crit)}$. Testing the sign of $f\'$ on each interval:</p>'
           f'<p>increasing on ${up}$; decreasing on ${down}$. So: {"; ".join(ext) or "no local extrema"}.</p>'
           f'<p>$f\'\'(x)={L(sp.factor(fpp))}$, which is zero at $x={", ".join(L(p) for p in infl)}$. Testing its sign:</p>'
           f'<p>concave up on ${cu}$; concave down on ${cd}$. Inflection points (where the concavity changes): '
           + (', '.join(f'$x={L(p)}$, where $f={L(f.subs(x, p))}$' for p in infl_real) or 'none') + '.</p>')
    answer = f'Increasing ${up}$, decreasing ${down}$; {"; ".join(ext)}; concave up ${cu}$, concave down ${cd}$; inflection at {infl_tex}'
    return {'problem': problem, 'answer': answer, 'solution': sol, 'data': {'f': f, 'inc': inc, 'conc': conc}}


def chk_cyl(d):
    R, H = d['R'], d['H']
    V = lambda r: math.pi * r * r * H * (1 - r / R)
    best = max((V(R * i / 100000), R * i / 100000) for i in range(100001))
    need(abs(best[0] - float(d['V'])) < 1e-6 * max(1, best[0]) and abs(best[1] - float(d['r'])) < 1e-3, 'maximum by sampling')


@template(course=C, chapter='optimization', id='m124-cylinder-in-cone',
          title='The largest cylinder inside a cone',
          based_on={'exam': 'm124finalAut2025', 'problem': 7}, check=chk_cyl)
def cylinder_in_cone(rng):
    R, H = rng.choice([3, 6, 8, 9, 12]), rng.choice([3, 6, 9, 10, 12])
    r = sp.Symbol('r', positive=True)
    h = H * (1 - r / R)
    V = sp.pi * r ** 2 * h
    rs = sp.Rational(2 * R, 3)
    hs, Vs = h.subs(r, rs), sp.simplify(V.subs(r, rs))
    problem = f'<p>Find the dimensions of the right circular cylinder of largest volume that fits inside a cone of height ${H}$ and base radius ${R}$, with the cylinder\'s base on the cone\'s base. Verify that it is a maximum.</p>'
    sol = (f'<p>Let the cylinder have radius $r$ and height $h$. Its top rim touches the cone, and by similar triangles $\\frac{{h}}{{{H}}}=\\frac{{{R}-r}}{{{R}}}$, so $h={L(h)}$.</p>'
           f'\\[V(r)=\\pi r^2h={L(sp.expand(V))},\\qquad 0\\le r\\le{R}.\\]'
           f'<p>$V\'(r)={L(sp.factor(sp.diff(V, r)))}$, which is $0$ at $r=0$ and $r={L(rs)}$. Since $V(0)=V({R})=0$ while $V({L(rs)})>0$ '
           f'(and $V\'$ changes from positive to negative there), $r={L(rs)}$ gives the maximum.</p>'
           f'<p>Radius $r={L(rs)}$, height $h={L(hs)}$, volume $V={L(Vs)}$.</p>')
    return {'problem': problem, 'answer': f'$r={L(rs)}$, $h={L(hs)}$ ($V={L(Vs)}$)', 'solution': sol, 'data': {'R': R, 'H': H, 'r': rs, 'V': Vs}}


def chk_param(d):
    X, Y, k = d['x'], d['y'], d['k']
    need(X.subs(t, k) == X.subs(t, -k) and Y.subs(t, k) == Y.subs(t, -k), 'the curve crosses itself')
    need((X.subs(t, k), Y.subs(t, k)) == tuple(d['P']), 'crossing point')
    xs, ys = sp.lambdify(t, X, 'mpmath'), sp.lambdify(t, Y, 'mpmath')
    for tv, m in zip((k, -k), d['slopes']):
        need(close(mpmath.diff(ys, tv) / mpmath.diff(xs, tv), float(m), 1e-10), 'tangent slope (numerical)')


@template(course=C, chapter='parametric_curves', id='m124-parametric-crossing',
          title='Where a parametric curve crosses itself, and its tangent lines there',
          based_on={'exam': 'm124finalWin2024', 'problem': 5}, check=chk_param)
def parametric_crossing(rng):
    k = rng.choice([1, 2, 3])
    b, c = rng.randint(-3, 3), rng.randint(-2, 3)
    X, Y = t ** 3 - k * k * t + b, t ** 2 + c
    P = (sp.Integer(b), sp.Integer(k * k + c))
    slopes = [sp.Rational(2 * tv, 3 * tv * tv - k * k) for tv in (k, -k)]
    problem = (f'<p>Consider the parametric curve $x={L(X)}$, $y={L(Y)}$.</p>'
               '<p>(a) Find the point where the curve crosses itself.<br>(b) Find the equations of both tangent lines at that point.</p>')
    sol = (f'<p><strong>(a)</strong> We need $t_1\\ne t_2$ giving the same $(x,y)$. Equal $y$ means $t_1^2=t_2^2$, so $t_2=-t_1$. '
           f'Then equal $x$ means $t_1^3-{k * k}t_1=-t_1^3+{k * k}t_1$, i.e. $2t_1(t_1^2-{k * k})=0$, so $t_1=\\pm{k}$. '
           f'At $t=\\pm{k}$: $x={b}$ and $y={k * k + c}$, so the crossing point is $({b},{k * k + c})$.</p>'
           f'<p><strong>(b)</strong> $\\dfrac{{dy}}{{dx}}=\\dfrac{{dy/dt}}{{dx/dt}}=\\dfrac{{2t}}{{3t^2-{k * k}}}$. At $t={k}$ the slope is ${L(slopes[0])}$; at $t=-{k}$ it is ${L(slopes[1])}$:</p>'
           f'\\[{line_tex(slopes[0], b, k * k + c)}\\qquad\\text{{and}}\\qquad {line_tex(slopes[1], b, k * k + c)}.\\]')
    return {'problem': problem, 'answer': f'$({b},{k * k + c})$; ${line_tex(slopes[0], b, k * k + c)}$ and ${line_tex(slopes[1], b, k * k + c)}$', 'solution': sol,
            'data': {'x': X, 'y': Y, 'k': k, 'P': P, 'slopes': slopes}}

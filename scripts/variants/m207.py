"""Math 207 (Differential Equations) practice-problem templates. See common.py for the contract.

Checks substitute each answer back into its equation (exactly with SymPy, and
numerically at several points), integrate the equation numerically, or take the
Laplace transform of the answer, so they never reuse the solution's own steps.
"""
import mpmath
import sympy as sp

from common import template, Reject, need, close, nz, rk4

C = 'Math 207'
t, s, x, y = sp.symbols('t s x y')


# ── helpers ──────────────────────────────────────────────────────────
def L(e):
    return sp.latex(e, ln_notation=True)


def zero(e, var=t, pts=(0.3, 0.7, 1.1, 1.9, 2.6)):
    """e is identically zero: exact simplification, or numerically at several points."""
    e = sp.sympify(e)
    if sp.simplify(e) == 0:
        return True
    return all(abs(complex(e.subs(var, p).evalf(30))) < 1e-15 for p in pts)


def ode2_tex(b, c, var='y', lead=1):
    """lead·y'' + b y' + c y as LaTeX."""
    out = (f'{L(lead)}' if lead != 1 else '') + f"{var}''"
    for coef, term in ((b, f"{var}'"), (c, var)):
        coef = sp.nsimplify(coef)
        if coef == 0:
            continue
        mag = '' if abs(coef) == 1 else L(abs(coef))
        out += (' - ' if coef < 0 else ' + ') + mag + term
    return out


def char_tex(b, c):
    """r^2 + b r + c with tidy signs."""
    out = 'r^2'
    if b:
        out += f'{"+" if b > 0 else "-"}{"" if abs(b) == 1 else abs(b)}r'
    if c:
        out += f'{"+" if c > 0 else "-"}{abs(c)}'
    return out


def resid2(expr, b, c, f, lead=1):
    return lead * sp.diff(expr, t, 2) + b * sp.diff(expr, t) + c * expr - f


def rfac(r, var='r'):
    """(r - a) with tidy signs."""
    r = sp.nsimplify(r)
    if r == 0:
        return var
    return f'({var}{" - " if r > 0 else " + "}{L(abs(r))})'


def explicit_ok(sol, ode_rhs, x0, y0, var):
    """sol(var) solves dy/dvar = ode_rhs(var, y) with sol(x0) = y0."""
    need(sp.simplify(sol.subs(var, x0) - y0) == 0, 'initial condition')
    res = sp.diff(sol, var) - ode_rhs.subs(y, sol)
    need(zero(res, var, pts=[x0 + d for d in (0.01, 0.05, 0.1, 0.15)]), 'does not satisfy the equation')


# ── first-order equations ────────────────────────────────────────────
G_POOL = [
    lambda r: r.choice([1, 2, 3]) * t * sp.exp(r.choice([1, 2, -1]) * t),
    lambda r: r.choice([2, 3, 4, 6]) * t ** r.choice([1, 2, 3]),
    lambda r: r.choice([1, 2, 3]) * sp.cos(r.choice([1, 2, 3]) * t),
    lambda r: r.choice([1, 2, 4]) * sp.exp(r.choice([2, 3, -2]) * t),
    lambda r: r.choice([1, 2]) * t * sp.cos(t),
]


def integral_work(g):
    """Antiderivative of g and a line of working (integration by parts spelled out when needed)."""
    G = sp.integrate(g, t)
    k, core = g.as_independent(t)
    if core.is_Mul and t in core.args:
        other = core / t
        V = sp.integrate(other, t)
        lead = '' if k == 1 else L(k)
        work = (f'By parts with $u=t$, $dv={L(other)}\\,dt$ (so $du=dt$, $v={L(V)}$): '
                f'$\\int {L(g)}\\,dt={lead}\\Big[{L(t * V)}-\\int {L(V)}\\,dt\\Big]={L(G)}+C$.')
    else:
        work = f'$\\int {L(g)}\\,dt={L(G)}+C$.'
    return G, work


def chk_separable(d):
    H, G, h, g = d['H'], d['G'], d['h'], d['g']
    need(sp.simplify(sp.diff(H, y) - h) == 0, 'antiderivative in y')
    need(zero(sp.diff(G, t) - g), 'antiderivative in t')


@template(course=C, chapter='first_order_odes', id='m207-separable-general',
          title='General solution of a separable equation',
          based_on={'exam': 'm207finalWin2013_Erickson', 'problem': 1}, check=chk_separable)
def separable_general(rng):
    g = rng.choice(G_POOL)(rng)
    a, b = rng.choice([1, 2, 3, 4, 6]), rng.randint(-3, 3)
    kind = rng.choice(['lin', 'lin', 'sq', 'exp'])
    if kind == 'lin':
        h = a * y + b
    elif kind == 'sq':
        h = 3 * y ** 2 + rng.choice([0, 1, 2])
    else:
        h = rng.choice([1, 2]) * sp.exp(rng.choice([1, 2]) * y)
    H = sp.integrate(h, y)
    G, work = integral_work(g)
    problem = f'<p>Find the general solution of</p>\\[\\frac{{dy}}{{dt}}=\\frac{{{L(g)}}}{{{L(h)}}}.\\]<p>An implicit solution is fine.</p>'
    sol = (f'<p>Separate the variables:</p>\\[\\left({L(h)}\\right)dy={L(g)}\\,dt.\\]'
           f'<p>Integrate the left side: $\\int\\left({L(h)}\\right)dy={L(H)}$. For the right side: {work}</p>'
           f'<p>So the general solution is</p>\\[{L(H)}={L(G)}+C.\\]'
           f'<p><strong>Check:</strong> differentiating implicitly, $\\left({L(sp.diff(H, y))}\\right)y\'={L(sp.diff(G, t))}$, which is the original equation.</p>')
    return {'problem': problem, 'answer': f'\\[{L(H)}={L(G)}+C\\]', 'solution': sol,
            'data': {'H': H, 'G': G, 'h': h, 'g': g}}


def classify_eq(f, r):
    lo, hi = sp.sign(f.subs(y, r - sp.Rational(1, 2))), sp.sign(f.subs(y, r + sp.Rational(1, 2)))
    if lo > 0 and hi < 0:
        return 'stable'
    if lo < 0 and hi > 0:
        return 'unstable'
    return 'semistable'


def chk_auto(d):
    f = d['f']
    need(set(sp.solve(f, y)) == set(d['kinds']), 'equilibria')
    for r, k in d['kinds'].items():
        need(classify_eq(f, r) == k, f'stability of {r}')
    # integrate numerically from y0 and see where the solution goes
    fn = sp.lambdify(y, f, 'math')
    # long horizon: next to a double root (semistable equilibrium) the approach is only like 1/t
    end = rk4(lambda _t, v: [fn(v[0])], 0.0, [float(d['y0'])], 400.0, 40000)[0]
    if d['limit'] in ('oo', '-oo'):
        need((end > 0) == (d['limit'] == 'oo') and abs(end) > max(abs(r) for r in d['kinds']) + 0.5, 'runs off to infinity')
    else:
        need(abs(end - d['limit']) < 1e-2, 'long-run limit')


@template(course=C, chapter='first_order_odes', id='m207-autonomous',
          title='Equilibria of an autonomous equation and their stability',
          based_on={'exam': 'm207mid1Win2014_Spicer', 'problem': 4}, check=chk_auto)
def autonomous(rng):
    n = rng.choice([2, 3, 3])
    roots = sorted(rng.sample(range(-4, 5), n))
    mult = [rng.choice([1, 1, 2]) for _ in roots]
    if sum(mult) > 4 or all(m == 2 for m in mult):
        raise Reject
    sgn = rng.choice([1, -1])
    f = sgn * sp.prod([(y - r) ** m for r, m in zip(roots, mult)])
    shown = sp.expand(f) if sum(mult) <= 2 else f
    kinds = {r: classify_eq(f, r) for r in roots}
    y0 = rng.choice([r + sp.Rational(1, 2) for r in roots] + [roots[0] - 1])
    up = sp.sign(f.subs(y, y0)) > 0
    above, below = [r for r in roots if r > y0], [r for r in roots if r < y0]
    limit = (min(above) if above else 'oo') if up else (max(below) if below else '-oo')
    pts = [roots[0] - 1] + [sp.Rational(roots[i] + roots[i + 1], 2) for i in range(n - 1)] + [roots[-1] + 1]
    ivs = [f'$y\\lt {roots[0]}$'] + [f'${roots[i]}\\lt y\\lt {roots[i + 1]}$' for i in range(n - 1)] + [f'$y>{roots[-1]}$']   # \\lt: a bare < before a letter would start an HTML tag
    rows = ''.join(f'<tr><td>{iv}</td><td>${L(p)}$</td><td>${"+" if f.subs(y, p) > 0 else "-"}$</td>'
                   f'<td>{"increasing ↑" if f.subs(y, p) > 0 else "decreasing ↓"}</td></tr>' for iv, p in zip(ivs, pts))
    expl = {'stable': 'solutions on both sides move toward it', 'unstable': 'solutions on both sides move away from it',
            'semistable': '$f$ has the same sign on both sides, so solutions approach from one side and leave on the other'}
    lim_tex = {'oo': '\\infty', '-oo': '-\\infty'}[limit] if isinstance(limit, str) else L(limit)
    problem = (f'<p>Consider the autonomous equation</p>\\[\\frac{{dy}}{{dt}}={L(shown)}.\\]'
               f'<p>(a) Find all equilibrium solutions and classify each as stable, unstable or semistable.<br>'
               f'(b) If $y(0)={L(y0)}$, what is $\\lim_{{t\\to\\infty}}y(t)$?</p>')
    sol = (f'<p><strong>(a)</strong> Equilibria are where $f(y)={L(f)}=0$: '
           f'{", ".join(f"$y={r}$" for r in roots)}. Test the sign of $f$ between them:</p>'
           f'<table class="variant-table"><tr><th>interval</th><th>test $y$</th><th>sign of $f$</th><th>$y(t)$ is</th></tr>{rows}</table>'
           + ''.join(f'<p>$y={r}$: <strong>{kinds[r]}</strong>, since {expl[kinds[r]]}.</p>' for r in roots)
           + f'<p><strong>(b)</strong> $f({L(y0)})$ is {"positive" if up else "negative"}, so $y$ {"increases" if up else "decreases"} from ${L(y0)}$ '
           + (f'toward the equilibrium $y={lim_tex}$, which it never crosses: $\\lim_{{t\\to\\infty}}y(t)={lim_tex}$.</p>'
              if not isinstance(limit, str) else f'with no equilibrium in the way, so $y(t)\\to{lim_tex}$.</p>'))
    answer = '<p>' + '; '.join(f'$y={r}$ {kinds[r]}' for r in roots) + f'. (b) $y(t)\\to{lim_tex}$.</p>'
    return {'problem': problem, 'answer': answer, 'solution': sol,
            'data': {'f': f, 'kinds': kinds, 'y0': y0, 'limit': limit}}


# ── initial value problems ───────────────────────────────────────────
def chk_ivp1(d):
    explicit_ok(d['sol'], d['rhs'], d['x0'], d['y0'], x)


@template(course=C, chapter='initial_value_problems', id='m207-separable-ivp',
          title='Explicit solution of a separable initial value problem',
          based_on={'exam': 'm207mid1Spr2022_Loveless', 'problem': 1}, check=chk_ivp1)
def separable_ivp(rng):
    k = rng.choice([1, 2, 3, 4])
    g = rng.choice([sp.sin(k * x), sp.cos(k * x), 2 * k * x, 3 * x ** 2, sp.exp(k * x)])
    G = sp.integrate(g, x)
    kind = rng.choice(['exp', 'square', 'growth', 'root'])
    x0 = 0
    if kind == 'exp':          # e^{y-c} dy = g dx
        c = rng.randint(-2, 2)
        y0 = c + rng.choice([0, 0, 1])
        rhs = g * sp.exp(-(y - c))
        Cc = sp.exp(y0 - c) - G.subs(x, x0)
        sol = c + sp.log(G + Cc)
        step = (f'\\[e^{{{L(y - c)}}}\\,dy={L(g)}\\,dx\\ \\Rightarrow\\ e^{{{L(y - c)}}}={L(G)}+C.\\]'
                f'<p>At $x=0$, $y={y0}$: $e^{{{y0 - c}}}={L(G.subs(x, 0))}+C$, so $C={L(Cc)}$. Take logarithms:</p>')
        problem_rhs = f'{L(g)}\\,e^{{{L(c - y)}}}'
    elif kind == 'square':     # y' = g y^2
        y0 = rng.choice([-1, 1, 2, -2, sp.Rational(1, 2)])
        rhs = g * y ** 2
        Cc = -1 / sp.sympify(y0) - G.subs(x, x0)
        sol = -1 / (G + Cc)
        step = (f'\\[\\frac{{dy}}{{y^2}}={L(g)}\\,dx\\ \\Rightarrow\\ -\\frac1y={L(G)}+C.\\]'
                f'<p>At $x=0$, $y={L(y0)}$: ${L(-1 / sp.sympify(y0))}={L(G.subs(x, 0))}+C$, so $C={L(Cc)}$. Solve for $y$:</p>')
        problem_rhs = f'{L(g)}\\,y^2'
    elif kind == 'growth':     # y' = g y
        y0 = nz(rng, -4, 5)
        rhs = g * y
        sol = y0 * sp.exp(G - G.subs(x, x0))
        step = (f'\\[\\frac{{dy}}{{y}}={L(g)}\\,dx\\ \\Rightarrow\\ \\ln|y|={L(G)}+C\\ \\Rightarrow\\ y=Ae^{{{L(G)}}}.\\]'
                f'<p>At $x=0$: ${y0}=Ae^{{{L(G.subs(x, 0))}}}$, so $A={L(y0 * sp.exp(-G.subs(x, 0)))}$:</p>')
        problem_rhs = f'{L(g)}\\,y'
    else:                      # y' = g / y
        y0 = rng.choice([-3, -2, 2, 3, 4])
        rhs = g / y
        Cc = sp.Rational(y0 ** 2, 2) - G.subs(x, x0)
        sol = sp.sign(y0) * sp.sqrt(2 * G + 2 * Cc)
        step = (f'\\[y\\,dy={L(g)}\\,dx\\ \\Rightarrow\\ \\frac{{y^2}}2={L(G)}+C.\\]'
                f'<p>At $x=0$, $y={y0}$: ${L(sp.Rational(y0 ** 2, 2))}={L(G.subs(x, 0))}+C$, so $C={L(Cc)}$. '
                f'Solve for $y$, taking the {"positive" if y0 > 0 else "negative"} root because $y(0)={y0}$:</p>')
        problem_rhs = f'\\frac{{{L(g)}}}{{y}}'
    if kind != 'root':
        sol = sp.simplify(sol)
    problem = f'<p>Find the explicit solution of the initial value problem</p>\\[\\frac{{dy}}{{dx}}={problem_rhs},\\qquad y(0)={L(y0)}.\\]'
    sol_tex = (f'<p>Separate the variables and integrate:</p>{step}\\[y={L(sol)}.\\]'
               f'<p><strong>Check:</strong> $y(0)={L(sp.simplify(sol.subs(x, 0)))}$.</p>')
    return {'problem': problem, 'answer': f'$y={L(sol)}$', 'solution': sol_tex,
            'data': {'sol': sol, 'rhs': rhs, 'x0': x0, 'y0': y0}}


def chk_linear_ivp(d):
    sol, a, c, m, y0 = d['sol'], d['a'], d['c'], d['m'], d['y0']
    need(sp.simplify(sol.subs(t, 1) - y0) == 0, 'initial condition')
    need(zero(sp.diff(sol, t) + a / t * sol - c * t ** m, pts=(0.5, 1.3, 2.2, 3.7)), 'equation')


@template(course=C, chapter='initial_value_problems', id='m207-linear-ivp',
          title='A linear first-order initial value problem (integrating factor)',
          based_on={'exam': 'm207mid1Spr2016_Loveless', 'problem': 1}, check=chk_linear_ivp)
def linear_ivp(rng):
    a = rng.choice([1, 2, 3, -1, 4])
    m = rng.choice([0, 1, 2, 3])
    c = rng.choice([1, 2, 3, 4, 5, 6])
    if m + a + 1 == 0:
        raise Reject
    y0 = rng.randint(-3, 4)
    k = m + a + 1
    Cc = y0 - sp.Rational(c, k)
    sol = sp.Rational(c, k) * t ** (m + 1) + Cc * t ** (-a)
    mu = t ** a
    lhs = f"y'+{'' if a == 1 else L(a)}\\frac{{y}}{{t}}" if a > 0 else "y'-\\frac{y}{t}"
    problem = f'<p>Solve the initial value problem</p>\\[{lhs}={L(c * t ** m)},\\qquad y(1)={y0},\\qquad t>0.\\]'
    sol_tex = (f'<p>The equation is linear with $p(t)={L(sp.Rational(a) / t)}$. Integrating factor:</p>'
               f'\\[\\mu(t)=e^{{\\int p\\,dt}}=e^{{{L(a)}\\ln t}}={L(mu)}.\\]'
               f'<p>Multiply through by $\\mu$; the left side becomes a product rule:</p>'
               f'\\[\\left({L(mu)}\\,y\\right)\'={L(sp.expand(c * t ** m * mu))}\\ \\Rightarrow\\ {L(mu)}\\,y={L(sp.Rational(c, k) * t ** k)}+C.\\]'
               f'<p>At $t=1$: ${y0}={L(sp.Rational(c, k))}+C$, so $C={L(Cc)}$. Divide by ${L(mu)}$:</p>'
               f'\\[y={L(sol)}.\\]')
    return {'problem': problem, 'answer': f'$y={L(sol)}$', 'solution': sol_tex,
            'data': {'sol': sol, 'a': a, 'c': c, 'm': m, 'y0': y0}}


# ── second-order equations ───────────────────────────────────────────
def solve_coeffs(Yform, coeffs, b, c, f):
    """Plug Yform into y''+by'+cy=f and solve for the coefficients by matching each kind of term.
    Returns (solution dict or None, list of equations)."""
    expr = sp.expand(resid2(Yform, b, c, f))
    # collect over the distinct functions t^j e^{at} cos/sin(bt)
    terms = sp.Add.make_args(sp.expand(sp.powsimp(expr)))
    groups = {}
    for term in terms:
        coeff, func = sp.S(1), sp.S(1)
        for fac in sp.Mul.make_args(term):
            if fac.free_symbols & {t}:
                func *= fac
            else:
                coeff *= fac
        groups[func] = groups.get(func, 0) + coeff
    eqs = [sp.Eq(sp.expand(v), 0) for v in groups.values() if sp.expand(v) != 0]
    sol = sp.solve(eqs, coeffs, dict=True) if eqs else [{}]
    ok = bool(sol) and all(k in sol[0] for k in coeffs) and all(not v.free_symbols for v in sol[0].values())
    return (sol[0] if ok else None), eqs


def chk_general2(d):
    b, c, f = d['b'], d['c'], d['f']
    c1, c2 = sp.symbols('c1 c2')
    need(zero(resid2(d['y'], b, c, f).subs({c1: sp.Rational(13, 10), c2: sp.Rational(-7, 10)})), 'general solution with c1, c2')
    need(zero(resid2(d['yh1'], b, c, 0)) and zero(resid2(d['yh2'], b, c, 0)), 'homogeneous solutions')
    W = sp.simplify(d['yh1'] * sp.diff(d['yh2'], t) - d['yh2'] * sp.diff(d['yh1'], t))
    need(W != 0, 'independent')


@template(course=C, chapter='second_order_odes', id='m207-undetermined-coefficients',
          title='General solution by undetermined coefficients',
          based_on={'exam': 'm207mid2Win2011_Grigg', 'problem': 2}, check=chk_general2)
def undetermined(rng):
    r1, r2 = rng.sample(range(-4, 5), 2)
    b, c = -(r1 + r2), r1 * r2
    kind = rng.choice(['exp', 'exp-res', 'texp', 'poly', 'trig'])
    A, B, Cc = sp.symbols('A B C')
    if kind == 'exp':
        al = rng.choice([a for a in range(-3, 4) if a not in (r1, r2)])
        K = nz(rng, -6, 6)
        f, form, cs, note = K * sp.exp(al * t), A * sp.exp(al * t), [A], f'Since ${al}$ is not a root, try'
    elif kind == 'exp-res':
        al = rng.choice([r1, r2])
        K = nz(rng, -6, 6)
        f, form, cs = K * sp.exp(al * t), A * t * sp.exp(al * t), [A]
        note = f'Since ${al}$ is a root of the characteristic equation, $Ae^{{{L(al * t)}}}$ would solve the homogeneous equation; multiply by $t$:'
    elif kind == 'texp':
        al = rng.choice([a for a in range(-2, 3) if a not in (r1, r2)] + [r1])
        K = nz(rng, -4, 4)
        mult = int(al in (r1, r2))
        f = K * t * sp.exp(al * t)
        form = t ** mult * (A * t + B) * sp.exp(al * t)
        cs = [A, B]
        note = (f'Since ${al}$ is a root, multiply the usual guess $(At+B)e^{{{L(al * t)}}}$ by $t$:' if mult else f'Since ${al}$ is not a root, try')
    elif kind == 'poly':
        if c == 0:
            raise Reject
        k2, k1, k0 = rng.randint(-3, 3), rng.randint(-4, 4), rng.randint(-5, 5)
        if k2 == 0 and k1 == 0:
            raise Reject
        f = k2 * t ** 2 + k1 * t + k0
        deg = 2 if k2 else 1
        form = (A * t ** 2 + B * t + Cc) if deg == 2 else (A * t + B)
        cs = [A, B, Cc][: deg + 1]
        note = 'The forcing is a polynomial and $0$ is not a root, so try a polynomial of the same degree:'
    else:
        w = rng.choice([1, 2, 3])
        K = nz(rng, -5, 5)
        fn = rng.choice([sp.cos, sp.sin])
        f = K * fn(w * t)
        form = A * sp.cos(w * t) + B * sp.sin(w * t)
        cs = [A, B]
        note = f'The roots are real, so ${w}i$ is not a root; try'
    co, eqs = solve_coeffs(form, cs, b, c, f)
    if co is None or any(abs(sp.fraction(v)[1]) > 150 for v in co.values()):
        raise Reject
    Yp = sp.expand(form.subs(co))
    c1, c2 = sp.symbols('c1 c2')
    yh1, yh2 = sp.exp(r1 * t), sp.exp(r2 * t)
    ysol = c1 * yh1 + c2 * yh2 + Yp
    eq_tex = ',\\quad '.join(L(e.lhs) + '=0' for e in eqs)
    plus = '' if L(Yp).startswith('-') else '+'
    general = f'c_1{L(yh1)}+c_2{L(yh2)}{plus}{L(Yp)}'
    problem = f'<p>Find the general solution of</p>\\[{ode2_tex(b, c)}={L(f)}.\\]'
    sol = (f'<p><strong>Homogeneous part.</strong> The characteristic equation is ${char_tex(b, c)}=0$, i.e. '
           f'${rfac(r1)}{rfac(r2)}=0$, so $r={r1},\\ {r2}$ and $y_h=c_1{L(yh1)}+c_2{L(yh2)}$.</p>'
           f'<p><strong>Particular solution.</strong> {note}</p>\\[Y={L(form)}.\\]'
           f'<p>Substitute into the equation and match the coefficients of each kind of term:</p>\\[{eq_tex},\\]'
           f'<p>which gives {", ".join(f"${L(k)}={L(v)}$" for k, v in co.items())}. So $Y={L(Yp)}$.</p>'
           f'<p><strong>General solution:</strong></p>\\[y={general}.\\]')
    return {'problem': problem, 'answer': f'$y={general}$', 'solution': sol,
            'data': {'y': ysol, 'yh1': yh1, 'yh2': yh2, 'b': b, 'c': c, 'f': f}}


def group_form(al, be, deg, s_mult, letters):
    """t^s e^{αt}[(poly) cos βt + (poly) sin βt] with fresh coefficient letters (consumed from `letters`)."""
    def poly():
        cs = [sp.Symbol(letters.pop(0)) for _ in range(deg + 1)]
        return sum(cf * t ** (deg - i) for i, cf in enumerate(cs)), cs
    pre = t ** s_mult * sp.exp(al * t)
    if be == 0:
        p, cs = poly()
        return pre * p, cs
    p1, c1 = poly()
    p2, c2 = poly()
    return pre * (p1 * sp.cos(be * t) + p2 * sp.sin(be * t)), c1 + c2


LETTERS = list('ABCDEFGHJKLMNPQRSTUVW')


def chk_form(d):
    b, c = d['b'], d['c']
    for g in d['groups']:
        form, cs = group_form(g['al'], g['be'], g['deg'], g['s'], LETTERS[:])
        co, _ = solve_coeffs(form, cs, b, c, g['f'])
        need(co is not None, f'form for {g["f"]} cannot work')
        if g['s'] > 0:
            form2, cs2 = group_form(g['al'], g['be'], g['deg'], g['s'] - 1, LETTERS[:])
            co2, _ = solve_coeffs(form2, cs2, b, c, g['f'])
            need(co2 is None, f'the extra factor of t is needed for {g["f"]}')


@template(course=C, chapter='second_order_odes', id='m207-particular-form',
          title='The form of a particular solution (no need to find the coefficients)',
          based_on={'exam': 'm207finalNA2018_1', 'problem': 3}, check=chk_form)
def particular_form(rng):
    kind = rng.choice(['real', 'repeated', 'complex', 'pure'])
    if kind == 'real':
        r1, r2 = rng.sample(range(-3, 4), 2)
        roots = [(r1, 0), (r2, 0)]
        b, c = -(r1 + r2), r1 * r2
    elif kind == 'repeated':
        r1 = rng.randint(-3, 3)
        roots = [(r1, 0), (r1, 0)]
        b, c = -2 * r1, r1 * r1
    elif kind == 'complex':
        a, w = rng.choice([-2, -1, 1, 2]), rng.randint(1, 3)
        roots = [(a, w), (a, -w)]
        b, c = -2 * a, a * a + w * w
    else:
        w = rng.randint(1, 4)
        roots = [(0, w), (0, -w)]
        b, c = 0, w * w
    # forcing terms built around the roots so that resonance comes up often
    cands = [(al, abs(be), rng.choice([0, 1])) for al, be in set(roots)]
    cands += [(0, 0, rng.choice([0, 1, 2])), (rng.choice([-1, 1, 2]), 0, rng.choice([0, 1])),
              (rng.choice([0, 1]), rng.choice([1, 2, 3]), rng.choice([0, 1]))]
    rng.shuffle(cands)
    want = rng.choice([2, 3, 3])
    picked = []
    for cnd in cands:
        if (cnd[0], cnd[1]) not in [(p[0], p[1]) for p in picked]:
            picked.append(cnd)
        if len(picked) == want:
            break
    if len(picked) < 2:
        raise Reject
    terms, groups = [], []
    letters = LETTERS[:]
    for al, be, deg in picked:
        k = nz(rng, -4, 5)
        trig = rng.choice([sp.cos, sp.sin]) if be else None
        f = k * t ** deg * sp.exp(al * t) * (trig(be * t) if be else 1)
        s_mult = (1 if (al, be) in roots else 0) if be else sum(1 for r in roots if r == (al, 0))
        form, _ = group_form(al, be, deg, s_mult, letters)
        terms.append(f)
        groups.append({'al': al, 'be': be, 'deg': deg, 's': s_mult, 'f': f, 'form': form})
    rhs = sum(terms)
    rt = ', '.join(L(r + i * sp.I) for r, i in sorted(set(roots), key=str))
    pieces = []
    for g in groups:
        z = L(g['al'] + g['be'] * sp.I)
        why = f'${z}$ is ' + {0: 'not a root', 1: 'a root, so multiply by $t$', 2: 'a double root, so multiply by $t^2$'}[g['s']]
        pieces.append(f'<li>For ${L(g["f"])}$: {why}. Guess ${L(g["form"])}$.</li>')
    Yall = ' + '.join(L(g['form']) for g in groups)
    problem = (f'<p>Write down the form of a particular solution of</p>\\[{ode2_tex(b, c)}={L(rhs)}.\\]'
               '<p>Do not solve for the coefficients.</p>')
    sol = (f'<p>The characteristic equation ${char_tex(b, c)}=0$ has roots $r={rt}$.</p>'
           f'<p>Treat each kind of forcing term separately: a term $t^k e^{{\\alpha t}}\\cos\\beta t$ (or $\\sin\\beta t$) gets degree-$k$ polynomials times both $\\cos\\beta t$ and $\\sin\\beta t$, '
           f'multiplied by $t^s$ where $s$ is the number of times $\\alpha+\\beta i$ is a root.</p><ul>{"".join(pieces)}</ul>'
           f'<p>Adding the pieces (every letter is a different unknown constant):</p>\\[Y={Yall}.\\]')
    return {'problem': problem, 'answer': f'\\[Y={Yall}\\]', 'solution': sol,
            'data': {'b': b, 'c': c, 'groups': [{k: v for k, v in g.items() if k != 'form'} for g in groups]}}


def chk_euler(d):
    a, b = d['a'], d['b']
    for f in d['basis']:
        need(zero(t ** 2 * sp.diff(f, t, 2) + a * t * sp.diff(f, t) + b * f, pts=(0.5, 1.3, 2.7)), 'solves the Euler equation')
    f1, f2 = d['basis']
    need(sp.simplify(f1 * sp.diff(f2, t) - f2 * sp.diff(f1, t)) != 0, 'independent')


def signed(coef, term, first=False):
    if coef == 0:
        return ''
    mag = '' if abs(coef) == 1 else str(abs(coef))
    return ('-' if coef < 0 else ('' if first else '+')) + mag + term


@template(course=C, chapter='second_order_odes', id='m207-euler-equation',
          title='An Euler equation: try y = tʳ',
          based_on={'exam': 'm207finalNA2023_4', 'problem': 4}, check=chk_euler)
def euler(rng):
    if rng.random() < 0.75:
        r1, r2 = rng.sample(range(-3, 5), 2)
    else:
        r1 = r2 = rng.choice([-2, -1, 1, 2, 3])
    a = 1 - (r1 + r2)        # r(r-1) + a r + b = r^2 + (a-1) r + b
    b = r1 * r2
    if a == 0 and b == 0:
        raise Reject
    basis = [t ** r1, t ** r2] if r1 != r2 else [t ** r1, t ** r1 * sp.log(t)]
    divided = rng.random() < 0.5
    if divided:
        eq = "y''" + (f'{"+" if a > 0 else "-"}\\frac{{{abs(a)}}}{{t}}y\'' if a else '') + (f'{"+" if b > 0 else "-"}\\frac{{{abs(b)}}}{{t^2}}y' if b else '') + '=0'
    else:
        eq = "t^2y''" + signed(a, "ty'") + signed(b, 'y') + '=0'
    r = sp.Symbol('r')
    ind = sp.expand(r * (r - 1) + a * r + b)
    gen = f'c_1{L(basis[0])}+c_2{L(basis[1])}'
    pre = (f"<p>Multiply through by $t^2$: $t^2y''{signed(a, chr(116) + 'y' + chr(39))}{signed(b, 'y')}=0$.</p>" if divided else '')
    problem = (f'<p>For $t>0$, consider</p>\\[{eq}.\\]'
               '<p>The coefficients are not constant, so $y=e^{rt}$ will not work. Look for solutions of the form $y=t^r$ and find the general solution.</p>')
    sol = (pre + f"<p>With $y=t^r$: $y'=rt^{{r-1}}$ and $y''=r(r-1)t^{{r-2}}$, so $t^2y''=r(r-1)t^r$ and $ty'=rt^r$. Substitute and divide by $t^r$:</p>"
           f'\\[r(r-1){signed(a, "r")}{signed(b, "")}={L(ind)}={rfac(r1)}{rfac(r2) if r1 != r2 else "^2"}=0.\\]'
           + (f'<p>The roots are $r={r1}$ and $r={r2}$, giving $y_1={L(basis[0])}$ and $y_2={L(basis[1])}$.</p>' if r1 != r2 else
              f'<p>$r={r1}$ is a double root. One solution is $y_1={L(basis[0])}$; for a repeated root of an Euler equation the second is $y_2={L(basis[1])}$.</p>')
           + f'<p>They are not multiples of each other, so the general solution is</p>\\[y={gen}.\\]')
    return {'problem': problem, 'answer': f'$y={gen}$', 'solution': sol, 'data': {'a': a, 'b': b, 'basis': basis}}


# ── springs ──────────────────────────────────────────────────────────
def chk_spring(d):
    m, g, k, u = d['m'], d['gamma'], d['k'], d['u']
    need(zero(resid2(u, g, k, 0, lead=m)), 'equation')
    need(sp.simplify(u.subs(t, 0) - d['u0']) == 0 and sp.simplify(sp.diff(u, t).subs(t, 0) - d['v0']) == 0, 'initial conditions')
    disc = g ** 2 - 4 * m * k
    need({'under': disc < 0, 'critical': disc == 0, 'over': disc > 0}[d['kind']], 'damping type')
    need(sp.simplify(d['W'] / d['stretch'] - k) == 0 and sp.simplify(d['W'] / 32 - m) == 0, 'k and m from the data')


@template(course=C, chapter='springs_and_damping', id='m207-damped-spring',
          title='A damped mass–spring system from physical data',
          based_on={'exam': 'm207mid2Win2011_Grigg', 'problem': 1}, check=chk_spring)
def damped_spring(rng):
    W = rng.choice([8, 16, 32, 64])
    m = sp.Rational(W, 32)
    kind = rng.choice(['under', 'under', 'critical', 'over'])
    if kind == 'under':
        p, q = rng.choice([1, 2, sp.Rational(1, 2), sp.Rational(3, 2)]), rng.choice([1, 2, 3, 4])
        gamma, k = 2 * m * p, m * (p ** 2 + q ** 2)
    elif kind == 'critical':
        p = rng.choice([1, 2, 3, 4])
        gamma, k = 2 * m * p, m * p ** 2
    else:
        r1, r2 = rng.sample([1, 2, 3, 4, 5], 2)
        gamma, k = m * (r1 + r2), m * r1 * r2
    if not (2 * k).is_integer or not (2 * gamma).is_integer:
        raise Reject
    stretch = sp.Rational(W) / k
    u0 = rng.choice([sp.Rational(1, 2), 1, sp.Rational(1, 4), sp.Rational(-1, 2)])
    v0 = rng.choice([0, 0, 1, -1, 2])
    C1, C2 = sp.symbols('C_1 C_2')
    r = sp.Symbol('r')
    roots = sp.solve(m * r ** 2 + gamma * r + k, r)
    if kind == 'under':
        re, im = sp.re(roots[0]), abs(sp.im(roots[0]))
        gen = sp.exp(re * t) * (C1 * sp.cos(im * t) + C2 * sp.sin(im * t))
        rt_tex = f'r={L(re)}\\pm {L(im)}i'
    elif kind == 'critical':
        re = roots[0]
        gen = (C1 + C2 * t) * sp.exp(re * t)
        rt_tex = f'r={L(re)}\\ \\text{{(double root)}}'
    else:
        gen = C1 * sp.exp(roots[0] * t) + C2 * sp.exp(roots[1] * t)
        rt_tex = f'r={L(roots[0])},\\ {L(roots[1])}'
    cs = sp.solve([gen.subs(t, 0) - u0, sp.diff(gen, t).subs(t, 0) - v0], [C1, C2], dict=True)[0]
    u = gen.subs(cs)
    word = {'under': 'underdamped', 'critical': 'critically damped', 'over': 'overdamped'}[kind]
    disc = gamma ** 2 - 4 * m * k
    dir0 = 'below' if u0 > 0 else 'above'
    vel = '' if v0 == 0 else f' with an initial velocity of ${abs(v0)}$ ft/s {"downward" if v0 > 0 else "upward"}'
    problem = (f'<p>A weight of ${W}$ lb stretches a spring ${L(stretch)}$ ft. The weight moves through a medium that resists with a force of ${L(gamma)}$ lb '
               f'for every ft/s of velocity. It is pulled ${L(abs(u0))}$ ft {dir0} equilibrium and released{vel}. Use $g=32$ ft/s² and take down as positive.</p>'
               '<p>(a) Write the initial value problem for the displacement $u(t)$ (in ft).<br>(b) Is the motion underdamped, critically damped or overdamped?<br>(c) Solve for $u(t)$.</p>')
    sol = (f'<p><strong>(a)</strong> Mass $m=\\frac{{{W}}}{{32}}={L(m)}$ slug. Spring constant $k=\\frac{{{W}}}{{{L(stretch)}}}={L(k)}$ lb/ft. Damping $\\gamma={L(gamma)}$ lb·s/ft:</p>'
           f'\\[{ode2_tex(gamma, k, "u", m)}=0,\\qquad u(0)={L(u0)},\\quad u\'(0)={L(v0)}.\\]'
           f'<p><strong>(b)</strong> $\\gamma^2-4mk={L(gamma ** 2)}-4\\left({L(m)}\\right)({L(k)})={L(disc)}$, which is {"negative" if disc < 0 else "zero" if disc == 0 else "positive"}: <strong>{word}</strong>.</p>'
           f'<p><strong>(c)</strong> The characteristic equation ${L(m * r ** 2 + gamma * r + k)}=0$ gives ${rt_tex}$, so $u={L(gen)}$. '
           f'From $u(0)={L(u0)}$ and $u\'(0)={L(v0)}$: $C_1={L(cs[C1])}$, $C_2={L(cs[C2])}$.</p>\\[u(t)={L(u)}.\\]')
    return {'problem': problem, 'answer': f'{word.capitalize()}; $u(t)={L(u)}$', 'solution': sol,
            'data': {'m': m, 'gamma': gamma, 'k': k, 'u': u, 'u0': u0, 'v0': v0, 'kind': kind, 'W': W, 'stretch': stretch}}


def chk_steady(d):
    need(zero(resid2(d['Y'], d['g'], d['k'], d['f'])), 'steady state solves the equation')
    need(not d['Y'].has(sp.exp), 'steady state is periodic')
    need(sp.simplify(d['R'] ** 2 - (d['A'] ** 2 + d['B'] ** 2)) == 0, 'amplitude')


@template(course=C, chapter='springs_and_damping', id='m207-forced-steady-state',
          title='Steady-state response of a forced, damped spring',
          based_on={'exam': 'm207mid2Win2011_Grigg', 'problem': 4}, check=chk_steady)
def steady(rng):
    g, k, w = rng.choice([1, 2, 3, 4]), rng.choice([1, 2, 3, 4, 5, 6, 9]), rng.choice([1, 2, 3])
    P, Q = rng.randint(-4, 4), rng.randint(-4, 4)
    if P == 0 and Q == 0:
        raise Reject
    f = P * sp.sin(w * t) + Q * sp.cos(w * t)
    A, B = sp.symbols('A B')
    eqA = sp.Eq((k - w ** 2) * A + g * w * B, Q)       # cos terms
    eqB = sp.Eq(-g * w * A + (k - w ** 2) * B, P)      # sin terms
    co = sp.solve([eqA, eqB], [A, B])
    Yp = co[A] * sp.cos(w * t) + co[B] * sp.sin(w * t)
    R = sp.sqrt(co[A] ** 2 + co[B] ** 2)
    problem = (f'<p>A spring–mass system with $m=1$ satisfies</p>\\[{ode2_tex(g, k)}={L(f)}.\\]'
               '<p>(a) Find the steady-state solution (the part that does not die out).<br>(b) What is its amplitude?</p>')
    sol = (f'<p><strong>(a)</strong> Damping makes the homogeneous solutions decay, so the steady state is the particular solution $Y=A\\cos {w}t+B\\sin {w}t$. '
           f'Then $Y\'=-{w}A\\sin {w}t+{w}B\\cos {w}t$ and $Y\'\'=-{w * w}Y$. Substituting and matching the $\\cos {w}t$ and $\\sin {w}t$ terms:</p>'
           f'\\[\\begin{{aligned}}\\cos {w}t:&\\quad {L(eqA.lhs)}={L(Q)}\\\\ \\sin {w}t:&\\quad {L(eqB.lhs)}={L(P)}\\end{{aligned}}\\]'
           f'<p>Solving: $A={L(co[A])}$, $B={L(co[B])}$.</p>\\[y_{{ss}}(t)={L(Yp)}.\\]'
           f'<p><strong>(b)</strong> Amplitude $R=\\sqrt{{A^2+B^2}}={L(R)}$.</p>')
    return {'problem': problem, 'answer': f'$y_{{ss}}={L(Yp)}$, amplitude ${L(R)}$', 'solution': sol,
            'data': {'Y': Yp, 'g': g, 'k': k, 'f': f, 'R': R, 'A': co[A], 'B': co[B]}}


# ── Laplace transforms ───────────────────────────────────────────────
def inv(F):
    """Inverse Laplace transform for t > 0 (drops the Heaviside(t) factor)."""
    return sp.expand(sp.inverse_laplace_transform(F, s, t).subs(sp.Heaviside(t), 1))


def chk_laplace_ivp(d):
    yv = d['y']
    need(zero(resid2(yv, d['b'], d['c'], d['f'])), 'equation')
    need(sp.simplify(yv.subs(t, 0) - d['y0']) == 0 and sp.simplify(sp.diff(yv, t).subs(t, 0) - d['v0']) == 0, 'initial conditions')
    need(sp.simplify(sp.laplace_transform(yv, t, s, noconds=True) - d['Ys']) == 0, 'Y(s) matches')


def sfac(r):
    return 's' if r == 0 else f'(s{"-" if r > 0 else "+"}{abs(r)})'


@template(course=C, chapter='laplace_transforms', id='m207-laplace-ivp',
          title='Solve an initial value problem with Laplace transforms',
          based_on={'exam': 'm207finalSpr2013_Riley', 'problem': 9}, check=chk_laplace_ivp)
def laplace_ivp(rng):
    r1, r2 = rng.sample(range(-3, 4), 2)
    b, c = -(r1 + r2), r1 * r2
    al = rng.choice([a for a in range(-3, 4) if a not in (r1, r2)])
    K = nz(rng, -6, 6)
    f = K * sp.exp(al * t)
    y0, v0 = rng.randint(-2, 2), rng.randint(-3, 3)
    F = K / (s - al)
    Ys = sp.factor(((s + b) * y0 + v0 + F) / ((s - r1) * (s - r2)))
    parts = sp.apart(Ys, s)
    if any(sp.fraction(sp.Add.make_args(parts)[i].as_coeff_Mul()[0])[1] > 60 for i in range(len(sp.Add.make_args(parts)))):
        raise Reject
    yv = inv(parts)
    lhs = 's^2Y' + signed(-y0, 's') + signed(-v0, '')
    if b:
        lhs += f'{"+" if b > 0 else "-"}{abs(b) if abs(b) != 1 else ""}\\left(sY{signed(-y0, "")}\\right)'
    if c:
        lhs += f'{"+" if c > 0 else "-"}{abs(c) if abs(c) != 1 else ""}Y'
    problem = f'<p>Use the Laplace transform to solve</p>\\[{ode2_tex(b, c)}={L(f)},\\qquad y(0)={y0},\\quad y\'(0)={v0}.\\]'
    sol = (f'<p>Transform both sides, using $\\mathcal L\\{{y\'\'\\}}=s^2Y-sy(0)-y\'(0)$ and $\\mathcal L\\{{y\'\\}}=sY-y(0)$:</p>'
           f'\\[{lhs}={L(F)}.\\]'
           f'<p>Collect the $Y$ terms; note $s^2{signed(b, "s")}{signed(c, "")}={sfac(r1)}{sfac(r2)}$. Solving for $Y$:</p>'
           f'\\[Y(s)={L(Ys)}.\\]<p>Partial fractions:</p>\\[Y(s)={L(parts)}.\\]'
           f'<p>Invert each term with $\\mathcal L^{{-1}}\\left\\{{\\frac{{1}}{{s-a}}\\right\\}}=e^{{at}}$:</p>\\[y(t)={L(yv)}.\\]')
    return {'problem': problem, 'answer': f'$y(t)={L(yv)}$', 'solution': sol,
            'data': {'y': yv, 'b': b, 'c': c, 'f': f, 'y0': y0, 'v0': v0, 'Ys': Ys}}


def chk_step(d):
    b, c, K, a = d['b'], d['c'], d['K'], d['a']
    p1 = sp.lambdify(t, d['piece1'], 'math')
    p2 = sp.lambdify(t, d['piece2'], 'math')
    on, off = (K, 0) if d['on_first'] else (0, K)
    # integrate each stretch separately (the forcing jumps at t = a)
    for tt in (0.4 * a, 0.9 * a):
        yv = rk4(lambda _t, w: [w[1], on - b * w[1] - c * w[0]], 0.0, [0.0, 0.0], tt)
        need(close(yv[0], p1(tt), 1e-7), f'solution at t={tt}')
    ya = rk4(lambda _t, w: [w[1], on - b * w[1] - c * w[0]], 0.0, [0.0, 0.0], float(a))
    for tt in (1.3 * a, 2 * a):
        yv = rk4(lambda _t, w: [w[1], off - b * w[1] - c * w[0]], float(a), ya, tt)
        need(close(yv[0], p2(tt), 1e-7), f'solution at t={tt}')


@template(course=C, chapter='laplace_transforms', id='m207-laplace-step',
          title='A switched-off (or switched-on) forcing term with step functions',
          based_on={'exam': 'm207finalWin2013_Erickson', 'problem': 9}, check=chk_step)
def laplace_step(rng):
    r1, r2 = rng.sample([-3, -2, -1, 1, 2, 3], 2)
    b, c = -(r1 + r2), r1 * r2
    K = rng.choice([1, 2, 3, 4, 6])
    a = rng.choice([1, 2, 3])
    on_first = rng.random() < 0.6
    H = 1 / (s * (s - r1) * (s - r2))
    Hp = sp.apart(H, s)
    h = inv(Hp)
    shifted = sp.expand(h.subs(t, t - a))
    if on_first:
        piece1, piece2 = sp.expand(K * h), sp.expand(K * (h - shifted))
        g_tex = f'\\begin{{cases}}{K}, & 0\\le t<{a}\\\\ 0, & t\\ge {a}\\end{{cases}}'
        g_step, Gs = f'{K}\\big(1-u_{{{a}}}(t)\\big)', f'\\frac{{{K}\\left(1-e^{{-{a}s}}\\right)}}{{s}}'
        Ys = f'{K}\\big(1-e^{{-{a}s}}\\big)H(s)'
        yform = f'{K}\\big[h(t)-u_{{{a}}}(t)\\,h(t-{a})\\big]'
    else:
        piece1, piece2 = sp.Integer(0), sp.expand(K * shifted)
        g_tex = f'\\begin{{cases}}0, & 0\\le t<{a}\\\\ {K}, & t\\ge {a}\\end{{cases}}'
        g_step, Gs = f'{K}u_{{{a}}}(t)', f'\\frac{{{K}e^{{-{a}s}}}}{{s}}'
        Ys = f'{K}e^{{-{a}s}}H(s)'
        yform = f'{K}u_{{{a}}}(t)\\,h(t-{a})'
    cases = f'\\begin{{cases}}{L(piece1)}, & 0\\le t<{a}\\\\ {L(piece2)}, & t\\ge {a}\\end{{cases}}'
    problem = f'<p>Solve the initial value problem</p>\\[{ode2_tex(b, c)}={g_tex},\\qquad y(0)=0,\\quad y\'(0)=0.\\]'
    sol = (f'<p>Write the forcing with a unit step function: $g(t)={g_step}$, so $\\mathcal L\\{{g\\}}={Gs}$.</p>'
           f'<p>With zero initial conditions, transforming gives $\\left(s^2{signed(b, "s")}{signed(c, "")}\\right)Y=\\mathcal L\\{{g\\}}$, so</p>'
           f'\\[Y(s)={Ys},\\qquad H(s)=\\frac{{1}}{{s{sfac(r1)}{sfac(r2)}}}.\\]'
           f'<p>Partial fractions and inversion of $H$:</p>\\[H(s)={L(Hp)}\\ \\Rightarrow\\ h(t)={L(h)}.\\]'
           f'<p>A factor $e^{{-{a}s}}$ shifts: $\\mathcal L^{{-1}}\\{{e^{{-{a}s}}H(s)\\}}=u_{{{a}}}(t)\\,h(t-{a})$. So $y(t)={yform}$, i.e.</p>'
           f'\\[y(t)={cases}\\]')
    return {'problem': problem, 'answer': f'\\[y(t)={cases}\\]', 'solution': sol,
            'data': {'b': b, 'c': c, 'K': K, 'a': a, 'on_first': on_first, 'piece1': piece1, 'piece2': piece2}}


def chk_inverse(d):
    need(sp.simplify(sp.laplace_transform(d['f'], t, s, noconds=True) - d['F']) == 0, 'transform of the answer')


@template(course=C, chapter='laplace_transforms', id='m207-inverse-laplace',
          title='Inverse Laplace transform: partial fractions and completing the square',
          based_on={'exam': 'm207finalSpr2015_Loveless', 'problem': 7}, check=chk_inverse)
def inverse_laplace(rng):
    a = rng.choice([-3, -2, -1, 1, 2, 3])
    A1 = rng.choice([1, 2, 3, 4])
    h, w = rng.choice([1, 2, 3, -1, -2]), rng.choice([1, 2, 3])
    B1 = rng.choice([1, 2, 3, 6])
    plain = rng.random() < 0.5
    num2 = sp.Integer(B1) if plain else s + rng.choice([0, 2 * h, h + 1])
    F1 = A1 / (s ** 2 * (s - a))
    q = s ** 2 + 2 * h * s + h * h + w * w
    F2 = num2 / q
    F = F1 + F2
    p1 = sp.apart(F1, s)
    f1 = inv(p1)
    sh = f'(s{"+" if h > 0 else "-"}{abs(h)})'
    if plain:
        f2 = sp.Rational(B1, w) * sp.exp(-h * t) * sp.sin(w * t)
        how2 = f'\\frac{{{B1}}}{{{sh}^2+{w * w}}}={L(sp.Rational(B1, w))}\\cdot\\frac{{{w}}}{{{sh}^2+{w}^2}}\\ \\to\\ {L(f2)}'
    else:
        shift = sp.expand(num2 - (s + h))        # numerator = (s+h) + shift
        f2 = sp.exp(-h * t) * (sp.cos(w * t) + sp.Rational(shift, w) * sp.sin(w * t))
        how2 = (f'\\frac{{{L(num2)}}}{{{sh}^2+{w * w}}}=\\frac{{{sh[1:-1]}}}{{{sh}^2+{w}^2}}'
                + (f'{"+" if shift > 0 else "-"}{L(sp.Rational(abs(shift), w))}\\cdot\\frac{{{w}}}{{{sh}^2+{w}^2}}' if shift else '')
                + f'\\ \\to\\ {L(f2)}')
    f = sp.expand(f1 + f2)
    problem = f'<p>Find</p>\\[\\mathcal L^{{-1}}\\left\\{{{L(F1)}+{L(F2)}\\right\\}}.\\]'
    sol = (f'<p><strong>First term.</strong> Partial fractions:</p>\\[{L(F1)}={L(p1)},\\]'
           f'<p>and with $\\mathcal L^{{-1}}\\{{1/s\\}}=1$, $\\mathcal L^{{-1}}\\{{1/s^2\\}}=t$ and $\\mathcal L^{{-1}}\\{{1/(s-a)\\}}=e^{{at}}$ this gives ${L(f1)}$.</p>'
           f'<p><strong>Second term.</strong> Complete the square: ${L(sp.expand(q))}={sh}^2+{w * w}$. '
           f'Using $\\mathcal L\\{{e^{{ct}}\\cos wt\\}}=\\frac{{s-c}}{{(s-c)^2+w^2}}$ and $\\mathcal L\\{{e^{{ct}}\\sin wt\\}}=\\frac{{w}}{{(s-c)^2+w^2}}$ with $c={-h}$, $w={w}$:</p>\\[{how2}.\\]'
           f'<p>Altogether:</p>\\[f(t)={L(f)}.\\]')
    return {'problem': problem, 'answer': f'$f(t)={L(f)}$', 'solution': sol, 'data': {'f': f, 'F': F}}


# ── modeling ─────────────────────────────────────────────────────────
def chk_mix(d):
    yv, rin, cin, rout, V0, dV = d['y'], d['rin'], d['cin'], d['rout'], d['V0'], d['dV']
    need(zero(sp.diff(yv, t) - (rin * cin - rout * yv / (V0 + dV * t)), pts=(0.5, 3, 7, 12)), 'equation')
    need(sp.simplify(yv.subs(t, 0) - d['y0']) == 0, 'initial amount')
    need(V0 + dV * d['T'] == d['cap'], 'time to fill')
    need(abs(float(yv.subs(t, d['T'])) - d['yT']) < 0.005, 'amount when full (rounded)')


@template(course=C, chapter='modeling_applications', id='m207-mixing-tank',
          title='A mixing tank that is filling up',
          based_on={'exam': 'm207mid1Spr2022_Loveless', 'problem': 5}, check=chk_mix)
def mixing(rng):
    n = rng.choice([1, 2])
    dV = rng.choice([2, 5, 10])
    rout = n * dV
    rin = rout + dV
    cin = rng.choice([1, 2, 3, 5])
    V0 = rng.choice([50, 100, 200])
    cap = V0 * rng.choice([2, 3])
    y0 = rng.choice([0, 10, 20, 50])
    T = sp.Rational(cap - V0, dV)
    Vt = V0 + dV * t
    K = sp.Rational(rin * cin, dV * (n + 1))
    Cc = (y0 - K * V0) * V0 ** n
    yv = K * Vt + Cc / Vt ** n
    yT = round(float(yv.subs(t, T)), 2)
    frac = f'\\frac{{{L(abs(Cc))}}}{{({V0}+{dV}t)^{{{n}}}}}' if n > 1 else f'\\frac{{{L(abs(Cc))}}}{{{V0}+{dV}t}}'
    ytex = f'{L(K)}({V0}+{dV}t){"+" if Cc >= 0 else "-"}{frac}'
    pw = lambda base: f'({base})^{{{n}}}' if n > 1 else f'({base})'
    problem = (f'<p>A tank holds ${V0}$ L of water containing ${y0}$ g of salt. Brine with ${cin}$ g/L of salt flows in at ${rin}$ L/min, '
               f'and the well-mixed solution drains out at ${rout}$ L/min. The tank holds ${cap}$ L.</p>'
               '<p>(a) Write an initial value problem for the amount of salt $y(t)$ (g) after $t$ minutes.<br>(b) Solve it.<br>(c) How much salt is in the tank when it is full?</p>')
    sol = (f'<p><strong>(a)</strong> The volume grows by ${rin}-{rout}={dV}$ L/min, so $V(t)={V0}+{dV}t$. Salt enters at ${rin}\\cdot{cin}={rin * cin}$ g/min '
           f'and leaves at ${rout}\\cdot\\dfrac{{y}}{{{V0}+{dV}t}}$ g/min:</p>\\[\\frac{{dy}}{{dt}}={rin * cin}-\\frac{{{rout}y}}{{{V0}+{dV}t}},\\qquad y(0)={y0}.\\]'
           f'<p><strong>(b)</strong> This is linear with $p(t)=\\frac{{{rout}}}{{{V0}+{dV}t}}$, so $\\mu=e^{{\\int p\\,dt}}=e^{{{n if n > 1 else ""}\\ln({V0}+{dV}t)}}={pw(f"{V0}+{dV}t")}$:</p>'
           f'\\[\\Big({pw(f"{V0}+{dV}t")}\\,y\\Big)\'={rin * cin}{pw(f"{V0}+{dV}t")}\\ \\Rightarrow\\ {pw(f"{V0}+{dV}t")}\\,y=\\frac{{{rin * cin}}}{{{dV * (n + 1)}}}({V0}+{dV}t)^{{{n + 1}}}+C.\\]'
           f'<p>At $t=0$: ${V0}{"^" + str(n) if n > 1 else ""}\\cdot{y0}={L(K)}\\cdot{V0}^{{{n + 1}}}+C$, so $C={L(Cc)}$. Divide by $\\mu$:</p>'
           f'\\[y(t)={ytex}.\\]'
           f'<p><strong>(c)</strong> The tank is full when ${V0}+{dV}t={cap}$, at $t={L(T)}$ min. Then</p>'
           f'\\[y({L(T)})={L(K)}\\cdot{cap}{"+" if Cc >= 0 else "-"}\\frac{{{L(abs(Cc))}}}{{{cap}{"^" + str(n) if n > 1 else ""}}}\\approx {yT:.2f}\\ \\text{{g}}.\\]')
    return {'problem': problem, 'answer': f'$y(t)={ytex}$; about ${yT:.2f}$ g when full', 'solution': sol,
            'data': {'y': yv, 'rin': rin, 'cin': cin, 'rout': rout, 'V0': V0, 'dV': dV, 'y0': y0, 'T': T, 'cap': cap, 'yT': yT}}


def chk_cool(d):
    T, a, b, c, k = d['T'], d['a'], d['b'], d['c'], d['k']
    need(zero(sp.diff(T, t) + a * T - (b + c * sp.exp(-k * t)), pts=(0.2, 1, 3, 6)), 'equation')
    need(sp.simplify(T.subs(t, 0) - d['T0']) == 0, 'initial temperature')
    need(sp.limit(T, t, sp.oo) == d['Tinf'], 'long-run temperature')


@template(course=C, chapter='modeling_applications', id='m207-linear-forcing',
          title='A linear model with exponential forcing (integrating factor)',
          based_on={'exam': 'm207mid1Spr2022_Loveless', 'problem': 3}, check=chk_cool)
def linear_forcing(rng):
    a = rng.choice([sp.Rational(1, 4), sp.Rational(1, 2), sp.Rational(1, 5), sp.Rational(1, 10), sp.Integer(2)])
    k = rng.choice([kk for kk in (sp.Integer(1), sp.Integer(2), sp.Rational(1, 2), sp.Integer(3)) if kk != a])
    Tinf = rng.choice([20, 30, 40, 60])
    b = a * Tinf
    c = rng.choice([30, 40, 60, 80, -40])
    T0 = rng.choice([100, 200, 400, 0, 10])
    D = c / (a - k)          # particular part D e^{-kt}: (a - k) D = c
    Cc = T0 - Tinf - D
    T = Tinf + D * sp.exp(-k * t) + Cc * sp.exp(-a * t)
    problem = (f'<p>The temperature $T(t)$ (°C) of an object satisfies</p>\\[T\'+{L(a)}T={L(b)}{"+" if c > 0 else "-"}{abs(c)}e^{{{L(-k * t)}}},\\qquad T(0)={T0}.\\]'
               '<p>(a) Solve for $T(t)$.<br>(b) What temperature does the object approach in the long run?</p>')
    sol = (f'<p><strong>(a)</strong> Integrating factor $\\mu=e^{{{L(a * t)}}}$:</p>'
           f'\\[\\big(Te^{{{L(a * t)}}}\\big)\'={L(b)}e^{{{L(a * t)}}}{"+" if c > 0 else "-"}{abs(c)}e^{{{L((a - k) * t)}}}\\ \\Rightarrow\\ '
           f'Te^{{{L(a * t)}}}={L(Tinf)}e^{{{L(a * t)}}}{"+" if D > 0 else "-"}{L(abs(D))}e^{{{L((a - k) * t)}}}+C.\\]'
           f'<p>Divide by $e^{{{L(a * t)}}}$: $T={L(Tinf)}{"+" if D > 0 else "-"}{L(abs(D))}e^{{{L(-k * t)}}}+Ce^{{{L(-a * t)}}}$. '
           f'At $t=0$: ${T0}={L(Tinf + D)}+C$, so $C={L(Cc)}$:</p>\\[T(t)={L(T)}.\\]'
           f'<p><strong>(b)</strong> Both exponentials decay, so $T(t)\\to {Tinf}$ °C.</p>')
    return {'problem': problem, 'answer': f'$T(t)={L(T)}$; $T\\to{Tinf}$ °C', 'solution': sol,
            'data': {'T': T, 'a': a, 'b': b, 'c': c, 'k': k, 'T0': T0, 'Tinf': Tinf}}

"""Math 126 (Calculus III) practice-problem templates. See common.py for the contract.

Checks recompute each answer another way: a different formula (curvature from
|r'×r''|, a_N from |a|² - a_T²), numerical differentiation or root-finding,
dense sampling of a region or constraint curve, numerical integration, or
SymPy's series expansion.
"""
import math
import mpmath
import sympy as sp

from common import template, Reject, need, close, nz, quad, quad2

C = 'Math 126'
x, y, z, t, n = sp.symbols('x y z t n', real=True)


def L(e):
    return sp.latex(e, ln_notation=True)


def vtex(F):
    return '\\langle ' + ',\\ '.join(L(c) for c in F) + '\\rangle'


def plane_tex(nv, d, names='xyz'):
    out = ''
    for c, v in zip(nv, names):
        if c == 0:
            continue
        mag = '' if abs(c) == 1 else L(abs(c))
        out += ('-' if c < 0 else ('+' if out else '')) + mag + v
    return f'{out}={L(d)}'


def shift(v, a):
    """(v - a) with tidy signs; just v when a = 0."""
    if a == 0:
        return v
    return f'({v}{"-" if a > 0 else "+"}{L(abs(a))})'


# ── vectors and geometry ─────────────────────────────────────────────
def chk_plane3(d):
    P, Q, R, nv, dd = d['P'], d['Q'], d['R'], d['n'], d['d']
    for pt in (P, Q, R):
        need(sum(a * b for a, b in zip(nv, pt)) == dd, 'point on plane')
    need(any(nv), 'nonzero normal')
    a, b, c = (math.dist(P, Q), math.dist(Q, R), math.dist(R, P))
    s_ = (a + b + c) / 2
    need(close(math.sqrt(max(s_ * (s_ - a) * (s_ - b) * (s_ - c), 0)), float(d['area']), 1e-9), 'area (Heron)')


@template(course=C, chapter='vectors_and_geometry_in_3d', id='m126-plane-three-points',
          title="The plane through three points, and the triangle's area",
          based_on={'exam': 'm126mid1Win2016', 'problem': 1}, check=chk_plane3)
def plane_three(rng):
    P, Q, R = ([rng.randint(-3, 4) for _ in range(3)] for _ in range(3))
    PQ = [b - a for a, b in zip(P, Q)]
    PR = [b - a for a, b in zip(P, R)]
    nv = list(sp.Matrix(PQ).cross(sp.Matrix(PR)))
    if not any(nv):
        raise Reject
    g = math.gcd(*[int(abs(v)) for v in nv])
    nr = [v // g for v in nv]
    dd = sum(a * b for a, b in zip(nr, P))
    area = sp.sqrt(sum(v * v for v in nv)) / 2
    pt_form = '+'.join(f'{nr[i]}{shift("xyz"[i], P[i])}' for i in range(3) if nr[i]).replace('+-', '-')
    problem = (f'<p>Let $P({P[0]},{P[1]},{P[2]})$, $Q({Q[0]},{Q[1]},{Q[2]})$ and $R({R[0]},{R[1]},{R[2]})$.</p>'
               '<p>(a) Find an equation of the plane through $P$, $Q$ and $R$.<br>(b) Find the area of triangle $PQR$.</p>')
    sol = (f'<p><strong>(a)</strong> $\\overrightarrow{{PQ}}={vtex(PQ)}$ and $\\overrightarrow{{PR}}={vtex(PR)}$. A normal vector is</p>'
           f'\\[\\vec n=\\overrightarrow{{PQ}}\\times\\overrightarrow{{PR}}={vtex(nv)}' + (f'\\parallel{vtex(nr)}' if g != 1 else '') + '.\\]'
           f'<p>Using the point $P$: ${pt_form}=0$, i.e.</p>\\[{plane_tex(nr, dd)}.\\]'
           f'<p><strong>(b)</strong> The area is half the length of the cross product: $\\frac12\\left|{vtex(nv)}\\right|=\\frac12\\sqrt{{{sum(v * v for v in nv)}}}={L(area)}$.</p>')
    return {'problem': problem, 'answer': f'(a) ${plane_tex(nr, dd)}$ &nbsp; (b) ${L(area)}$', 'solution': sol,
            'data': {'P': P, 'Q': Q, 'R': R, 'n': nr, 'd': dd, 'area': area}}


def chk_line(d):
    for nv, dd in d['planes']:
        need(sum(a * b for a, b in zip(nv, d['point'])) == dd, 'point on both planes')
        need(sum(a * b for a, b in zip(nv, d['dir'])) == 0, 'direction perpendicular to both normals')
    need(any(d['dir']), 'nonzero direction')


@template(course=C, chapter='vectors_and_geometry_in_3d', id='m126-line-of-intersection',
          title='Parametric equations for the line where two planes meet',
          based_on={'exam': 'm126finalSpr2007', 'problem': 4}, check=chk_line)
def line_intersection(rng):
    P0 = [rng.randint(-2, 3) for _ in range(3)]
    n1 = [nz(rng, -3, 3), rng.randint(-2, 2), nz(rng, -2, 2)]
    n2 = [rng.randint(-2, 2), nz(rng, -3, 3), nz(rng, -2, 2)]
    dv = list(sp.Matrix(n1).cross(sp.Matrix(n2)))
    if not any(dv):
        raise Reject
    d1, d2 = sum(a * b for a, b in zip(n1, P0)), sum(a * b for a, b in zip(n2, P0))
    k = next(i for i in (2, 1, 0) if dv[i] != 0)       # setting this coordinate to 0 leaves a solvable 2x2 system
    others = [i for i in range(3) if i != k]
    u, w = sp.symbols('u w')
    sol = sp.solve([n1[others[0]] * u + n1[others[1]] * w - d1, n2[others[0]] * u + n2[others[1]] * w - d2], [u, w])
    pt = [sp.Integer(0)] * 3
    pt[others[0]], pt[others[1]] = sol[u], sol[w]
    g = math.gcd(*[int(abs(v)) for v in dv])
    dr = [v // g for v in dv]
    names = 'xyz'
    par = ',\\quad '.join(f'{names[i]}={L(pt[i] + dr[i] * t)}' for i in range(3))
    problem = (f'<p>Find parametric equations for the line of intersection of the planes</p>'
               f'\\[{plane_tex(n1, d1)}\\qquad\\text{{and}}\\qquad {plane_tex(n2, d2)}.\\]')
    sol_tex = (f'<p>The line lies in both planes, so it is perpendicular to both normals $\\vec n_1={vtex(n1)}$ and $\\vec n_2={vtex(n2)}$. A direction vector is</p>'
               f'\\[\\vec n_1\\times\\vec n_2={vtex(dv)}' + (f'\\parallel{vtex(dr)}' if g != 1 else '') + '.\\]'
               f'<p>For a point on the line, set ${names[k]}=0$ and solve the two plane equations: '
               f'${names[others[0]]}={L(sol[u])}$, ${names[others[1]]}={L(sol[w])}$. So $({L(pt[0])},{L(pt[1])},{L(pt[2])})$ is on the line, and</p>'
               f'\\[{par}.\\]<p>(Any point on the line and any nonzero multiple of the direction give an equally correct answer.)</p>')
    return {'problem': problem, 'answer': f'${par}$ (or any equivalent parametrization)', 'solution': sol_tex,
            'data': {'planes': [(n1, d1), (n2, d2)], 'point': pt, 'dir': dr}}


# ── curves and motion ────────────────────────────────────────────────
def chk_curv(d):
    xt, yt, t0 = d['x'], d['y'], d['t0']
    r1 = sp.Matrix([sp.diff(xt, t), sp.diff(yt, t), 0]).subs(t, t0)
    r2 = sp.Matrix([sp.diff(xt, t, 2), sp.diff(yt, t, 2), 0]).subs(t, t0)
    k = r1.cross(r2).norm() / r1.norm() ** 3
    need(close(float(k), float(d['k']), 1e-12), 'curvature from |r′×r″|/|r′|³')


@template(course=C, chapter='curves_in_3d_and_motion_in_space', id='m126-curvature',
          title='Curvature of a parametric curve',
          based_on={'exam': 'm126mid2Spr2007_ConroyH', 'problem': 4}, check=chk_curv)
def curvature(rng):
    a, b, c, e = nz(rng, -2, 2), rng.randint(-3, 3), nz(rng, -2, 2), rng.randint(-3, 3)
    xt = a * t ** 2 + b * t
    yt = c * t ** rng.choice([2, 3]) + e * t
    t0 = rng.randint(-2, 2)
    x1, y1 = sp.diff(xt, t), sp.diff(yt, t)
    x2, y2 = sp.diff(xt, t, 2), sp.diff(yt, t, 2)
    X1, Y1, X2, Y2 = (q.subs(t, t0) for q in (x1, y1, x2, y2))
    num = abs(X1 * Y2 - Y1 * X2)
    den = X1 ** 2 + Y1 ** 2
    if den == 0 or num == 0:
        raise Reject
    k = sp.nsimplify(num / den ** sp.Rational(3, 2))
    problem = f'<p>Find the curvature of the curve $x={L(xt)}$, $y={L(yt)}$ at $t={t0}$.</p>'
    sol = (f'<p>For a plane curve, $\\kappa=\\dfrac{{|x\'y\'\'-y\'x\'\'|}}{{\\left(x\'^2+y\'^2\\right)^{{3/2}}}}$.</p>'
           f'<p>$x\'={L(x1)}$, $y\'={L(y1)}$, $x\'\'={L(x2)}$, $y\'\'={L(y2)}$. At $t={t0}$: $x\'={X1}$, $y\'={Y1}$, $x\'\'={X2}$, $y\'\'={Y2}$.</p>'
           f'\\[\\kappa=\\frac{{|({X1})({Y2})-({Y1})({X2})|}}{{\\left({X1 ** 2}+{Y1 ** 2}\\right)^{{3/2}}}}=\\frac{{{num}}}{{{den}^{{3/2}}}}={L(k)}.\\]')
    return {'problem': problem, 'answer': f'$\\kappa={L(k)}$', 'solution': sol, 'data': {'x': xt, 'y': yt, 't0': t0, 'k': k}}


def chk_acc(d):
    r, t0 = d['r'], d['t0']
    v = [float(sp.diff(c, t).subs(t, t0)) for c in r]
    a = [float(sp.diff(c, t, 2).subs(t, t0)) for c in r]
    need(close(sum(p * q for p, q in zip(v, a)) / math.sqrt(sum(p * p for p in v)), float(d['aT']), 1e-12), 'a_T')
    need(close(math.sqrt(max(sum(q * q for q in a) - float(d['aT']) ** 2, 0)), float(d['aN']), 1e-9), 'a_N from |a|² = a_T² + a_N²')


@template(course=C, chapter='curves_in_3d_and_motion_in_space', id='m126-acceleration-components',
          title='Tangential and normal components of acceleration',
          based_on={'exam': 'm126finalSpr2007', 'problem': 6}, check=chk_acc)
def acc_components(rng):
    p = nz(rng, -2, 3)
    if rng.random() < 0.5:
        r = [p * t, sp.Integer(rng.choice([1, 2, -1])) / t, rng.choice([1, 2]) * t ** 2]
        t0 = rng.choice([1, 2])
    else:
        r = [rng.choice([1, 2]) * t ** 2, p * t, rng.choice([1, 3]) * t ** 3]
        t0 = rng.choice([1, 2, -1])
    v = [sp.diff(c, t) for c in r]
    a = [sp.diff(c, t, 2) for c in r]
    v0 = [c.subs(t, t0) for c in v]
    a0 = [c.subs(t, t0) for c in a]
    speed = sp.sqrt(sum(q * q for q in v0))
    dot = sum(p_ * q for p_, q in zip(v0, a0))
    cr = list(sp.Matrix(v0).cross(sp.Matrix(a0)))
    crn = sp.sqrt(sum(q * q for q in cr))
    aT, aN = sp.radsimp(dot / speed), sp.radsimp(crn / speed)
    problem = f'<p>A particle moves along $\\vec r(t)={vtex(r)}$. Find the tangential and normal components of its acceleration at $t={t0}$.</p>'
    sol = (f'<p>$\\vec v={vtex(v)}$ and $\\vec a={vtex(a)}$. At $t={t0}$: $\\vec v={vtex(v0)}$, $\\vec a={vtex(a0)}$, $|\\vec v|={L(speed)}$.</p>'
           f'\\[a_T=\\frac{{\\vec v\\cdot\\vec a}}{{|\\vec v|}}=\\frac{{{L(dot)}}}{{{L(speed)}}}={L(aT)}.\\]'
           f'<p>$\\vec v\\times\\vec a={vtex(cr)}$, so</p>\\[a_N=\\frac{{|\\vec v\\times\\vec a|}}{{|\\vec v|}}=\\frac{{{L(crn)}}}{{{L(speed)}}}={L(aN)}.\\]'
           f'<p><strong>Check:</strong> $a_T^2+a_N^2=|\\vec a|^2={L(sum(q * q for q in a0))}$.</p>')
    return {'problem': problem, 'answer': f'$a_T={L(aT)}$, $a_N={L(aN)}$', 'solution': sol, 'data': {'r': r, 't0': t0, 'aT': aT, 'aN': aN}}


ARC = [(1, 2), (2, 1), (1, 8), (8, 1), (2, 4), (4, 2), (2, 9), (9, 2), (3, 6), (6, 3)]


def chk_arc(d):
    speed = sp.lambdify(t, sp.sqrt(sum(sp.diff(c, t) ** 2 for c in d['r'])), 'mpmath')
    need(close(quad(speed, d['a'], d['b']), float(d['L']), 1e-10), 'arc length')


@template(course=C, chapter='curves_in_3d_and_motion_in_space', id='m126-arc-length',
          title='Arc length of a space curve',
          based_on={'exam': 'm126mid2Win2006_Conroy', 'problem': 5}, check=chk_arc)
def arc_length(rng):
    p, q = rng.choice(ARC)
    s_ = sp.sqrt(2 * p * q)
    r = [p * t, sp.Rational(2, 3) * s_ * t ** sp.Rational(3, 2), sp.Rational(q, 2) * t ** 2]
    a = rng.choice([0, 0, 1])
    b = a + rng.choice([1, 2, 3])
    Lval = p * (b - a) + sp.Rational(q, 2) * (b ** 2 - a ** 2)
    problem = f'<p>Find the length of the curve $\\vec r(t)={vtex(r)}$ for ${a}\\le t\\le {b}$.</p>'
    sol = (f'<p>$\\vec r\\,{{}}\'(t)={vtex([sp.diff(c, t) for c in r])}$, so</p>'
           f'\\[|\\vec r\\,{{}}\'(t)|=\\sqrt{{{p * p}+{2 * p * q}t+{L(q * q * t ** 2)}}}=\\sqrt{{\\left({L(p + q * t)}\\right)^2}}={L(p + q * t)}\\quad(t\\ge0).\\]'
           f'\\[L=\\int_{{{a}}}^{{{b}}}\\left({L(p + q * t)}\\right)dt=\\left[{L(p * t + sp.Rational(q, 2) * t ** 2)}\\right]_{{{a}}}^{{{b}}}={L(Lval)}.\\]')
    return {'problem': problem, 'answer': f'$L={L(Lval)}$', 'solution': sol, 'data': {'r': r, 'a': a, 'b': b, 'L': Lval}}


# ── partial derivatives, tangent planes ──────────────────────────────
def chk_implicit(d):
    f = sp.lambdify((x, y, z), d['F'], 'mpmath')
    P = d['P']
    zof = lambda X, Y: mpmath.findroot(lambda Z: f(X, Y, Z), P[2])
    zx = mpmath.diff(lambda h: zof(P[0] + h, P[1]), 0)
    zy = mpmath.diff(lambda h: zof(P[0], P[1] + h), 0)
    need(close(zx, float(d['zx']), 1e-8) and close(zy, float(d['zy']), 1e-8), 'implicit partials (numerical)')


@template(course=C, chapter='partial_derivatives_and_optimization', id='m126-implicit-partials',
          title='Partial derivatives of z defined implicitly',
          based_on={'exam': 'm126mid2Win2019_Taggart', 'problem': 2}, check=chk_implicit)
def implicit_partials(rng):
    P = [rng.randint(-2, 2), rng.randint(-2, 2), rng.choice([-1, 1, 2])]
    terms = [x ** 2 * z, y * z ** 3, x * y * z, x * z ** 2, y ** 2 * z, z ** 3, x ** 2 * y, x * sp.exp(z - P[2])]
    F0 = sum(nz(rng, -3, 3) * m for m in rng.sample(terms, 3))
    c = F0.subs({x: P[0], y: P[1], z: P[2]})
    F = F0 - c
    Fx, Fy, Fz = (sp.diff(F, v) for v in (x, y, z))
    at = {x: P[0], y: P[1], z: P[2]}
    fx, fy, fzv = Fx.subs(at), Fy.subs(at), Fz.subs(at)
    if fzv == 0 or (fx == 0 and fy == 0):
        raise Reject
    zx, zy = sp.nsimplify(-fx / fzv), sp.nsimplify(-fy / fzv)
    problem = (f'<p>The equation ${L(F0)}={L(c)}$ defines $z$ as a function of $x$ and $y$ near the point $({P[0]},{P[1]},{P[2]})$. '
               f'Find $\\dfrac{{\\partial z}}{{\\partial x}}$ and $\\dfrac{{\\partial z}}{{\\partial y}}$ at that point.</p>')
    sol = (f'<p>Let $F(x,y,z)={L(F)}$. Implicit differentiation gives $z_x=-\\dfrac{{F_x}}{{F_z}}$ and $z_y=-\\dfrac{{F_y}}{{F_z}}$.</p>'
           f'<p>$F_x={L(Fx)}$, $F_y={L(Fy)}$, $F_z={L(Fz)}$. At $({P[0]},{P[1]},{P[2]})$: $F_x={L(fx)}$, $F_y={L(fy)}$, $F_z={L(fzv)}$.</p>'
           f'\\[\\frac{{\\partial z}}{{\\partial x}}=-\\frac{{{L(fx)}}}{{{L(fzv)}}}={L(zx)},\\qquad \\frac{{\\partial z}}{{\\partial y}}=-\\frac{{{L(fy)}}}{{{L(fzv)}}}={L(zy)}.\\]')
    return {'problem': problem, 'answer': f'$z_x={L(zx)}$, $z_y={L(zy)}$', 'solution': sol, 'data': {'F': F, 'P': P, 'zx': zx, 'zy': zy}}


LIN_F = [
    (lambda r: sp.sqrt(x ** 2 + y ** 2), [(3, 4), (4, 3), (6, 8), (5, 12), (8, 6), (12, 5)]),
    (lambda r: x ** 2 * y ** 3, [(1, 1), (2, 1), (1, 2), (-1, 1)]),
    (lambda r: x * sp.exp(r.choice([1, 2, 3]) * y), [(1, 0), (2, 0), (3, 0)]),
    (lambda r: sp.log(x ** 2 + r.choice([1, 2, 3]) * y), [(1, 0), (2, 0)]),
    (lambda r: sp.sqrt(r.choice([1, 2]) * x + y ** 2), [(8, 1), (0, 3), (2, 2)]),
]
STEPS = [sp.Rational(1, 10), sp.Rational(-1, 10), sp.Rational(1, 20), sp.Rational(-1, 20), sp.Rational(1, 100)]


def chk_lin(d):
    f = sp.lambdify((x, y), d['f'], 'mpmath')
    a, b = d['pt']
    fx = mpmath.diff(lambda h: f(a + h, b), 0)
    fy = mpmath.diff(lambda h: f(a, b + h), 0)
    need(close(f(a, b), float(d['f0']), 1e-12), 'f at the point')
    need(close(f(a, b) + fx * d['dx'] + fy * d['dy'], float(d['est']), 1e-10), 'linear estimate (numerical partials)')


@template(course=C, chapter='tangent_planes_and_linear_approximation', id='m126-linear-approximation',
          title='Tangent plane and a linear estimate',
          based_on={'exam': 'm126finalWin2008', 'problem': 5}, check=chk_lin)
def linear_approx(rng):
    mk, pts = rng.choice(LIN_F)
    f = mk(rng)
    a, b = rng.choice(pts)
    f0 = sp.simplify(f.subs({x: a, y: b}))
    if not (f0.is_real and f0.is_finite) or f0 == 0:
        raise Reject
    dx, dy = rng.choice(STEPS), rng.choice(STEPS)
    fx, fy = sp.diff(f, x), sp.diff(f, y)
    fxv, fyv = sp.simplify(fx.subs({x: a, y: b})), sp.simplify(fy.subs({x: a, y: b}))
    plane = sp.expand(f0 + fxv * (x - a) + fyv * (y - b))
    est = sp.nsimplify(f0 + fxv * dx + fyv * dy)
    X, Yv = a + dx, b + dy
    approx = '' if est.is_Integer else f'\\approx {float(est):.4f}'
    problem = (f'<p>Let $f(x,y)={L(f)}$.</p><p>(a) Find the tangent plane to $z=f(x,y)$ at $({a},{b})$.<br>'
               f'(b) Use it to estimate $f({L(X)},{L(Yv)})$.</p>')
    sol = (f'<p><strong>(a)</strong> $f({a},{b})={L(f0)}$, $f_x={L(fx)}$ and $f_y={L(fy)}$, so $f_x({a},{b})={L(fxv)}$ and $f_y({a},{b})={L(fyv)}$.</p>'
           f'\\[z={L(f0)}+\\left({L(fxv)}\\right){shift("x", a)}+\\left({L(fyv)}\\right){shift("y", b)}\\quad\\Longleftrightarrow\\quad z={L(plane)}.\\]'
           f'<p><strong>(b)</strong> With $\\Delta x={L(dx)}$ and $\\Delta y={L(dy)}$:</p>'
           f'\\[f({L(X)},{L(Yv)})\\approx {L(f0)}+\\left({L(fxv)}\\right)\\left({L(dx)}\\right)+\\left({L(fyv)}\\right)\\left({L(dy)}\\right)={L(est)}{approx}.\\]')
    return {'problem': problem, 'answer': f'$z={L(plane)}$; $f({L(X)},{L(Yv)})\\approx{L(est)}$', 'solution': sol,
            'data': {'f': f, 'pt': (a, b), 'dx': float(dx), 'dy': float(dy), 'est': est, 'f0': f0}}


# ── critical points, global extrema, Lagrange ────────────────────────
def classify2(f, pt):
    H = sp.hessian(f, (x, y)).subs({x: pt[0], y: pt[1]})
    ev = [float(sp.re(e)) for e in H.eigenvals()]
    if all(e > 1e-12 for e in ev):
        return 'local minimum'
    if all(e < -1e-12 for e in ev):
        return 'local maximum'
    if min(ev) < -1e-12 and max(ev) > 1e-12:
        return 'saddle point'
    return 'inconclusive'


def chk_crit(d):
    f = d['f']
    pts = {tuple(p) for p in sp.nonlinsolve([sp.diff(f, x), sp.diff(f, y)], [x, y]) if all(sp.sympify(c).is_real for c in p)}
    need(pts == set(d['kinds']), 'critical points')
    for p, k in d['kinds'].items():
        need(classify2(f, p) == k, f'classification of {p} (Hessian eigenvalues)')


@template(course=C, chapter='critical_points_and_local_extrema', id='m126-classify-critical-points',
          title='Find and classify critical points (second derivative test)',
          based_on={'exam': 'm126mid2Win2019_Taggart', 'problem': 3}, check=chk_crit)
def crit_points(rng):
    fam = rng.choice(['A', 'B', 'C'])
    if fam == 'A':
        f = x ** 3 + y ** 3 - 3 * rng.choice([1, 2, 3]) * x * y
    elif fam == 'B':
        a, b = rng.choice([1, 2, 3]), rng.randint(-2, 2)
        f = x ** 3 - 3 * a * a * x + rng.choice([1, 2]) * (y ** 2 - 2 * b * y)
    else:
        m = rng.choice([1, 4, 9])
        f = 3 * m * x - x ** 3 - 3 * x * y ** 2
    f = sp.expand(rng.choice([1, -1, 2]) * f)
    fx, fy = sp.diff(f, x), sp.diff(f, y)
    pts = sorted({(s_[x], s_[y]) for s_ in sp.solve([fx, fy], [x, y], dict=True) if s_[x].is_real and s_[y].is_real})
    fxx, fyy, fxy = sp.diff(f, x, 2), sp.diff(f, y, 2), sp.diff(f, x, y)
    rows, kinds = [], {}
    for p in pts:
        at = {x: p[0], y: p[1]}
        A, B_, Cc = fxx.subs(at), fyy.subs(at), fxy.subs(at)
        D = A * B_ - Cc ** 2
        if D == 0:
            raise Reject
        kind = 'saddle point' if D < 0 else ('local minimum' if A > 0 else 'local maximum')
        kinds[p] = kind
        rows.append(f'<tr><td>$({L(p[0])},{L(p[1])})$</td><td>${L(A)}$</td><td>${L(B_)}$</td><td>${L(Cc)}$</td><td>${L(D)}$</td><td>{kind}</td></tr>')
    problem = f'<p>Find all critical points of $f(x,y)={L(f)}$ and classify each as a local maximum, local minimum or saddle point.</p>'
    sol = (f'<p>$f_x={L(fx)}$ and $f_y={L(fy)}$. Solving $f_x=f_y=0$ gives the critical points '
           f'{", ".join(f"$({L(p[0])},{L(p[1])})$" for p in pts)}.</p>'
           f'<p>Second derivatives: $f_{{xx}}={L(fxx)}$, $f_{{yy}}={L(fyy)}$, $f_{{xy}}={L(fxy)}$, and $D=f_{{xx}}f_{{yy}}-f_{{xy}}^2$:</p>'
           f'<table class="variant-table"><tr><th>point</th><th>$f_{{xx}}$</th><th>$f_{{yy}}$</th><th>$f_{{xy}}$</th><th>$D$</th><th>type</th></tr>{"".join(rows)}</table>'
           '<p>($D<0$: saddle point; $D>0$ and $f_{xx}>0$: local minimum; $D>0$ and $f_{xx}<0$: local maximum.)</p>')
    return {'problem': problem, 'answer': '<p>' + '; '.join(f'$({L(p[0])},{L(p[1])})$ {kinds[p]}' for p in pts) + '</p>', 'solution': sol,
            'data': {'f': f, 'kinds': kinds}}


def chk_global(d):
    f = sp.lambdify((x, y), d['f'], 'math')
    a, b, tri = d['a'], d['b'], d['tri']
    N = 240
    vals = []
    for i in range(N + 1):
        X = a * i / N
        top = b * (1 - X / a) if tri else b
        vals += [f(X, top * j / N) for j in range(N + 1)]
    need(max(vals) <= float(d['max']) + 1e-9 and min(vals) >= float(d['min']) - 1e-9, 'no sampled value beats the claimed extremes')
    for key in ('max', 'min'):
        X, Y = (float(c) for c in d[key + '_at'])
        need(-1e-12 <= X <= a + 1e-12 and -1e-12 <= Y <= (b * (1 - X / a) if tri else b) + 1e-12, 'extreme point in the region')
        need(close(f(X, Y), float(d[key]), 1e-12), 'value at the extreme point')


@template(course=C, chapter='global_extrema_on_regions', id='m126-global-extrema',
          title='Absolute maximum and minimum on a closed region',
          based_on={'exam': 'm126finalWin2025', 'problem': 4}, check=chk_global)
def global_extrema(rng):
    tri = rng.random() < 0.5
    a, b = rng.choice([1, 2, 3]), rng.choice([1, 2, 3])
    f = nz(rng, -2, 2) * x ** 2 + nz(rng, -2, 2) * y ** 2 + rng.randint(-2, 2) * x * y + rng.randint(-4, 4) * x + rng.randint(-4, 4) * y
    inside = lambda X, Y: 0 < X < a and 0 < Y < (b * (1 - X / a) if tri else b)
    sol = sp.solve([sp.diff(f, x), sp.diff(f, y)], [x, y], dict=True)
    interior = [(s_[x], s_[y]) for s_ in sol if x in s_ and y in s_ and inside(s_[x], s_[y])]
    cands = [(p, 'interior critical point') for p in interior]
    if tri:
        corners = [(0, 0), (a, 0), (0, b)]
        edges = [((0, 0), (a, 0)), ((0, 0), (0, b)), ((a, 0), (0, b))]
    else:
        corners = [(0, 0), (a, 0), (a, b), (0, b)]
        edges = [((0, 0), (a, 0)), ((a, 0), (a, b)), ((0, b), (a, b)), ((0, 0), (0, b))]
    edge_lines = []
    for P, Q in edges:
        g = sp.expand(f.subs({x: P[0] + t * (Q[0] - P[0]), y: P[1] + t * (Q[1] - P[1])}))
        crit = [r for r in sp.solve(sp.diff(g, t), t) if r.is_real and 0 < r < 1]
        cands += [((P[0] + r * (Q[0] - P[0]), P[1] + r * (Q[1] - P[1])), 'edge') for r in crit]
        edge_lines.append(f'<li>From $({P[0]},{P[1]})$ to $({Q[0]},{Q[1]})$: $f={L(g)}$ for $0\\le t\\le1$'
                          + (f'; critical at {", ".join(f"$t={L(r)}$" for r in crit)}' if crit else '; no critical point inside') + '.</li>')
    cands += [(p, 'corner') for p in corners]
    vals = [(sp.nsimplify(f.subs({x: p[0], y: p[1]})), p, w) for p, w in cands]
    mx = max(vals, key=lambda q: q[0])
    mn = min(vals, key=lambda q: q[0])
    if mx[0] == mn[0]:
        raise Reject
    region = f'the triangle with vertices $(0,0)$, $({a},0)$ and $(0,{b})$' if tri else f'the rectangle $0\\le x\\le{a}$, $0\\le y\\le{b}$'
    table = ''.join(f'<tr><td>$({L(p[0])},{L(p[1])})$</td><td>{w}</td><td>${L(v)}$</td></tr>' for v, p, w in vals)
    pt = lambda q: f'$({L(q[1][0])},{L(q[1][1])})$'
    problem = f'<p>Find the absolute maximum and minimum values of $f(x,y)={L(f)}$ on {region}.</p>'
    sol_tex = (f'<p><strong>Interior.</strong> $f_x={L(sp.diff(f, x))}$ and $f_y={L(sp.diff(f, y))}$. '
               + (f'Setting both to zero gives {", ".join(f"$({L(p[0])},{L(p[1])})$" for p in interior)}, inside the region.' if interior else
                  'Setting both to zero gives no critical point strictly inside the region.') + '</p>'
               f'<p><strong>Boundary.</strong> Parametrize each edge and find the critical points of the one-variable function:</p><ul>{"".join(edge_lines)}</ul>'
               f'<p><strong>Compare every candidate</strong>, including the corners:</p>'
               f'<table class="variant-table"><tr><th>point</th><th>from</th><th>$f$</th></tr>{table}</table>'
               f'<p>Absolute maximum ${L(mx[0])}$ at {pt(mx)}; absolute minimum ${L(mn[0])}$ at {pt(mn)}.</p>')
    return {'problem': problem, 'answer': f'max ${L(mx[0])}$ at {pt(mx)}; min ${L(mn[0])}$ at {pt(mn)}', 'solution': sol_tex,
            'data': {'f': f, 'a': a, 'b': b, 'tri': tri, 'max': mx[0], 'min': mn[0], 'max_at': mx[1], 'min_at': mn[1]}}


def chk_lagrange(d):
    f = sp.lambdify((x, y), d['f'], 'math')
    X, Yf = (sp.lambdify(t, c, 'math') for c in d['curve'])
    N = 20000
    vals = [f(X(2 * math.pi * i / N), Yf(2 * math.pi * i / N)) for i in range(N)]
    need(abs(max(vals) - float(d['max'])) < 1e-6 and abs(min(vals) - float(d['min'])) < 1e-6, 'extremes along the constraint curve')
    g = sp.lambdify((x, y), d['g'], 'math')
    for p in d['max_at'] + d['min_at']:
        need(abs(g(float(p[0]), float(p[1]))) < 1e-12, 'point on the constraint')


@template(course=C, chapter='lagrange_multipliers', id='m126-lagrange',
          title='Extreme values on a curve with Lagrange multipliers',
          based_on={'exam': 'm126finalSpr2006', 'problem': 9}, check=chk_lagrange)
def lagrange(rng):
    lam = sp.Symbol('lambda')
    fam = rng.choice(['linear', 'quad', 'xy'])
    if fam == 'linear':
        p, q = rng.choice([(3, 4), (4, 3), (5, 12), (12, 5), (6, 8), (8, 6), (1, 1), (1, 2)])
        p, q = rng.choice([1, -1]) * p, rng.choice([1, -1]) * q
        R = rng.choice([1, 2, 5])
        f, g, curve, ctex = p * x + q * y, x ** 2 + y ** 2 - R ** 2, (R * sp.cos(t), R * sp.sin(t)), f'x^2+y^2={R * R}'
    elif fam == 'quad':
        a, b, R = rng.choice([1, 2, 3]), rng.choice([4, 5, 6]), rng.choice([1, 2, 3])
        f = a * x ** 2 + b * y ** 2 + rng.choice([0, 2, -2]) * x
        g, curve, ctex = x ** 2 + y ** 2 - R ** 2, (R * sp.cos(t), R * sp.sin(t)), f'x^2+y^2={R * R}'
    else:
        A, B = rng.choice([1, 2, 3]), rng.choice([2, 3, 4])
        if A == B:
            raise Reject
        f, g = x * y, x ** 2 / sp.Integer(A * A) + y ** 2 / sp.Integer(B * B) - 1
        curve, ctex = (A * sp.cos(t), B * sp.sin(t)), f'\\frac{{x^2}}{{{A * A}}}+\\frac{{y^2}}{{{B * B}}}=1'
    eqs = [sp.diff(f, x) - lam * sp.diff(g, x), sp.diff(f, y) - lam * sp.diff(g, y), g]
    sols = [s_ for s_ in sp.solve(eqs, [x, y, lam], dict=True) if s_[x].is_real and s_[y].is_real]
    pts = [(s_[x], s_[y]) for s_ in sols]
    vals = [(sp.nsimplify(sp.simplify(f.subs({x: p[0], y: p[1]}))), p) for p in pts]
    mx, mn = max(v for v, _ in vals), min(v for v, _ in vals)
    mx_at = [p for v, p in vals if v == mx]
    mn_at = [p for v, p in vals if v == mn]
    fmt = lambda ps: ', '.join(f'$({L(p[0])},{L(p[1])})$' for p in ps)
    problem = f'<p>Use Lagrange multipliers to find the maximum and minimum values of $f(x,y)={L(f)}$ on the curve ${ctex}$.</p>'
    sol = (f'<p>Write the constraint as $g(x,y)={L(sp.expand(g))}=0$ and solve $\\nabla f=\\lambda\\nabla g$ together with $g=0$:</p>'
           f'\\[{L(sp.diff(f, x))}=\\lambda\\left({L(sp.diff(g, x))}\\right),\\qquad {L(sp.diff(f, y))}=\\lambda\\left({L(sp.diff(g, y))}\\right),\\qquad {L(sp.expand(g))}=0.\\]'
           f'<p>The solutions are {fmt(pts)}. Evaluate $f$ at each:</p>'
           f'<table class="variant-table"><tr><th>point</th><th>$f$</th></tr>{"".join(f"<tr><td>$({L(p[0])},{L(p[1])})$</td><td>${L(v)}$</td></tr>" for v, p in vals)}</table>'
           f'<p>The curve is closed and bounded, so both extremes exist: maximum ${L(mx)}$ at {fmt(mx_at)}; minimum ${L(mn)}$ at {fmt(mn_at)}.</p>')
    return {'problem': problem, 'answer': f'max ${L(mx)}$, min ${L(mn)}$', 'solution': sol,
            'data': {'f': f, 'g': g, 'curve': curve, 'max': mx, 'min': mn, 'max_at': mx_at, 'min_at': mn_at}}


# ── double integrals ─────────────────────────────────────────────────
def chk_dbl(d):
    f = sp.lambdify((x, y), d['f'], 'mpmath')
    lo, hi = sp.lambdify(x, d['lo'], 'mpmath'), sp.lambdify(x, d['hi'], 'mpmath')
    need(close(quad2(f, d['x0'], d['x1'], lo, hi), sp.N(d['I'], 25), 1e-9), 'iterated integral (numerical)')


@template(course=C, chapter='double_integrals', id='m126-double-integral-region',
          title='Mass of a plate over a region between two curves',
          based_on={'exam': 'm126finalWin2008', 'problem': 6}, check=chk_dbl)
def double_region(rng):
    if rng.random() < 0.5:
        k = rng.choice([1, 2, 3, 4])
        lo, hi, x0, x1 = x ** 2, k * x, 0, k
        rdesc = f'the region between $y=x^2$ and $y={L(k * x)}$'
        meet = f'The curves meet where $x^2={L(k * x)}$: $x=0$ and $x={k}$. Between them $y={L(k * x)}$ is on top.'
    else:
        a, b = rng.choice([1, 2, 3]), rng.choice([1, 2, 3])
        lo, hi, x0, x1 = sp.Integer(0), b - sp.Rational(b, a) * x, 0, a
        rdesc = f'the triangle with vertices $(0,0)$, $({a},0)$ and $(0,{b})$'
        meet = f'The slanted side is $y={L(hi)}$, so the triangle is $0\\le x\\le{a}$, $0\\le y\\le{L(hi)}$.'
    f = rng.choice([x * y, x + y, 1 + x, x ** 2, 2 * y, x * y ** 2])
    inner = sp.expand(sp.integrate(f, (y, lo, hi)))
    I = sp.integrate(inner, (x, x0, x1))
    problem = f'<p>A thin plate occupies {rdesc} and has density $\\delta(x,y)={L(f)}$. Find its mass.</p>'
    sol = (f'<p>{meet}</p>\\[m=\\int_{{{x0}}}^{{{x1}}}\\int_{{{L(lo)}}}^{{{L(hi)}}}{L(f)}\\,dy\\,dx.\\]'
           f'<p>Inner integral (in $y$): ${L(inner)}$.</p>\\[m=\\int_{{{x0}}}^{{{x1}}}\\left({L(inner)}\\right)dx={L(I)}.\\]')
    return {'problem': problem, 'answer': f'$m={L(I)}$', 'solution': sol, 'data': {'f': f, 'lo': lo, 'hi': hi, 'x0': x0, 'x1': x1, 'I': I}}


# ── Taylor ───────────────────────────────────────────────────────────
def chk_taylor(d):
    ser = sp.series(d['f'], x, d['a'], d['n'] + 1).removeO()
    need(sp.simplify(sp.expand(ser) - sp.expand(d['T'])) == 0, 'matches SymPy series')


@template(course=C, chapter='taylor_polynomials', id='m126-taylor-polynomial',
          title='A Taylor polynomial about a point',
          based_on={'exam': 'm126finalSpr2007', 'problem': 1}, check=chk_taylor)
def taylor_poly(rng):
    fam = rng.choice(['exp', 'log', 'sqrt', 'sin', 'cos', 'mix', 'inv'])
    if fam == 'exp':
        f, a = sp.exp(rng.choice([1, 2, -1, 3]) * x), rng.choice([0, 0, 1])
    elif fam == 'log':
        f, a = sp.log(x), rng.choice([1, 2])
    elif fam == 'sqrt':
        f, a = sp.sqrt(x), rng.choice([1, 4, 9])
    elif fam == 'sin':
        f, a = sp.sin(rng.choice([1, 2]) * x), rng.choice([0, sp.pi / 2, sp.pi])
    elif fam == 'cos':
        f, a = sp.cos(rng.choice([1, 2, 3]) * x), rng.choice([0, sp.pi / 2, sp.pi])
    elif fam == 'mix':
        f, a = x ** 3 + rng.choice([1, 2]) * x + 4 * sp.cos(sp.pi * x), rng.choice([1, -1, 0])
    else:
        f, a = 1 / x, rng.choice([1, 2, -1])
    nn = rng.choice([2, 3])
    ders = [sp.simplify(sp.diff(f, x, k)) for k in range(nn + 1)]
    vals = [sp.simplify(dk.subs(x, a)) for dk in ders]
    if all(v == 0 for v in vals[1:]):
        raise Reject
    T = sum(v / sp.factorial(k) * (x - a) ** k for k, v in enumerate(vals))
    xa = shift('x', a) if not isinstance(a, sp.Basic) or a.is_Integer else f'\\left(x-{L(a)}\\right)'
    pieces = []
    for k, v in enumerate(vals):
        if v == 0:
            continue
        pieces.append(L(v) if k == 0 else (f'\\left({L(v)}\\right){xa}' if k == 1 else f'\\frac{{{L(v)}}}{{{k}!}}{xa}^{{{k}}}'))
    problem = f'<p>Find the Taylor polynomial $T_{{{nn}}}(x)$ of $f(x)={L(f)}$ about $x={L(a)}$.</p>'
    sol = ('<p>$T_n(x)=\\sum_{k=0}^n\\frac{f^{(k)}(a)}{k!}(x-a)^k$. Derivatives:</p><ul>'
           + ''.join(f'<li>$f{"" if k == 0 else "^{(" + str(k) + ")}"}(x)={L(ders[k])}$, so $f{"" if k == 0 else "^{(" + str(k) + ")}"}({L(a)})={L(vals[k])}$</li>' for k in range(nn + 1))
           + f'</ul>\\[T_{{{nn}}}(x)={" + ".join(pieces)}={L(T)}.\\]')
    ordered = ''
    for k, v in enumerate(vals):                     # write T_n in increasing powers of (x - a), as on paper
        c_ = sp.nsimplify(v / sp.factorial(k))
        if c_ == 0:
            continue
        mag = L(abs(c_)) if (abs(c_) != 1 or k == 0) else ''
        pw = '' if k == 0 else (xa if k == 1 else f'{xa}^{{{k}}}')
        neg = sp.sign(c_) < 0 if c_.is_number and c_.is_real else False
        ordered += ('-' if neg else ('+' if ordered else '')) + (f'{mag}{pw}' if mag else pw)
    sol = sol.replace(f'={L(T)}.\\]', f'={ordered}.\\]')
    return {'problem': problem, 'answer': f'$T_{{{nn}}}(x)={ordered}$', 'solution': sol, 'data': {'f': f, 'a': a, 'n': nn, 'T': T}}


def chk_tineq(d):
    k, c, nn, M, bound = d['k'], d['c'], d['n'], d['M'], d['bound']
    need(close(float(bound), float(M) * c ** (nn + 1) / math.factorial(nn + 1), 1e-12), 'bound formula')
    f = sp.exp(k * x)
    T = sp.series(f, x, 0, nn + 1).removeO()
    sgn = -1 if d['side'] == 'neg' else 1
    worst = max(abs(float((f - T).subs(x, sgn * c * s_))) for s_ in (0.25, 0.5, 0.75, 1))
    need(worst <= float(bound) + 1e-15, 'actual error within the bound')
    need(float(M) >= max(abs(k) ** (nn + 1) * math.exp(k * sgn * c * s_) for s_ in (0, 0.5, 1)) - 1e-12, 'M bounds the derivative')


@template(course=C, chapter='taylor_polynomials', id='m126-taylor-inequality',
          title="Bounding the error with Taylor's inequality",
          based_on={'exam': 'm126finalWin2008', 'problem': 2}, check=chk_tineq)
def taylor_inequality(rng):
    k = rng.choice([1, 2, 3, -1, -2])
    c = rng.choice([sp.Rational(1, 2), sp.Rational(1, 4), sp.Rational(1, 10), sp.Integer(1)])
    nn = rng.choice([2, 3, 4])
    side = 'neg' if k > 0 else 'pos'      # the side where kx <= 0, so e^{kx} <= 1 and M = |k|^{n+1}
    M = abs(k) ** (nn + 1)
    bound = M * c ** (nn + 1) / sp.factorial(nn + 1)
    interval = f'[-{L(c)},\\,0]' if side == 'neg' else f'[0,\\,{L(c)}]'
    problem = (f'<p>Let $T_{{{nn}}}(x)$ be the degree-${nn}$ Taylor polynomial of $f(x)=e^{{{L(k * x)}}}$ about $x=0$. '
               f'Use Taylor\'s inequality to bound $|f(x)-T_{{{nn}}}(x)|$ for $x$ in ${interval}$.</p>')
    sol = (f'<p>Taylor\'s inequality: if $|f^{{({nn + 1})}}(x)|\\le M$ on the interval, then $|f(x)-T_{{{nn}}}(x)|\\le\\dfrac{{M}}{{({nn + 1})!}}|x|^{{{nn + 1}}}$.</p>'
           f'<p>$f^{{({nn + 1})}}(x)={L(sp.Integer(k) ** (nn + 1))}e^{{{L(k * x)}}}$. On ${interval}$ we have ${L(k * x)}\\le0$, so $e^{{{L(k * x)}}}\\le1$ and '
           f'$|f^{{({nn + 1})}}(x)|\\le{M}$; take $M={M}$. Also $|x|\\le{L(c)}$:</p>'
           f'\\[|f(x)-T_{{{nn}}}(x)|\\le\\frac{{{M}}}{{{nn + 1}!}}\\left({L(c)}\\right)^{{{nn + 1}}}={L(bound)}\\approx{float(bound):.3g}.\\]')
    return {'problem': problem, 'answer': f'$|f(x)-T_{{{nn}}}(x)|\\le{L(bound)}$', 'solution': sol,
            'data': {'k': k, 'c': float(c), 'n': nn, 'M': M, 'bound': bound, 'side': side}}


def chk_series(d):
    f, gen, start, R, deg = d['f'], d['gen'], d['start'], d['R'], d['deg']
    ser = sp.series(f, x, 0, deg).removeO()
    want = sp.expand(sum(gen.subs(n, k) for k in range(start, 60) if sp.degree(gen.subs(n, k), x) < deg))
    need(sp.expand(ser - want) == 0, 'general term matches the series')
    if R != sp.oo:
        term = sp.Poly(gen.subs(n, 400), x)
        need(close(abs(float(term.coeffs()[0])) ** (-1.0 / term.degree()), float(R), 2e-2), 'radius of convergence (root test)')


@template(course=C, chapter='taylor_series', id='m126-maclaurin-series',
          title='A Maclaurin series from a known series, and its radius of convergence',
          based_on={'exam': 'm126finalSpr2008', 'problem': 2}, check=chk_series)
def maclaurin(rng):
    fam = rng.choice(['exp', 'xexp', 'cos', 'sin', 'geom', 'log', 'xgeom'])
    k, m, j = rng.choice([1, 2, 3]), rng.choice([1, 2, 3]), rng.choice([1, 2])
    c = sp.sympify(rng.choice([1, 2, 3, -1, -2, sp.Rational(1, 2)]))
    if fam == 'exp':
        f, gen, start, R = sp.exp(k * x ** m), sp.Integer(k) ** n * x ** (m * n) / sp.factorial(n), 0, sp.oo
        known, sub = 'e^u=\\sum_{n\\ge0}\\frac{u^n}{n!}', f'$u={L(k * x ** m)}$'
    elif fam == 'xexp':
        f, gen, start, R = x ** j * sp.exp(k * x), sp.Integer(k) ** n * x ** (n + j) / sp.factorial(n), 0, sp.oo
        known, sub = 'e^u=\\sum_{n\\ge0}\\frac{u^n}{n!}', f'$u={L(k * x)}$, then multiply by ${L(x ** j)}$'
    elif fam == 'cos':
        f, gen, start, R = sp.cos(k * x ** m), (-1) ** n * sp.Integer(k) ** (2 * n) * x ** (2 * m * n) / sp.factorial(2 * n), 0, sp.oo
        known, sub = '\\cos u=\\sum_{n\\ge0}\\frac{(-1)^nu^{2n}}{(2n)!}', f'$u={L(k * x ** m)}$'
    elif fam == 'sin':
        f, gen, start, R = sp.sin(k * x ** m), (-1) ** n * sp.Integer(k) ** (2 * n + 1) * x ** (m * (2 * n + 1)) / sp.factorial(2 * n + 1), 0, sp.oo
        known, sub = '\\sin u=\\sum_{n\\ge0}\\frac{(-1)^nu^{2n+1}}{(2n+1)!}', f'$u={L(k * x ** m)}$'
    elif fam == 'geom':
        f, gen, start = 1 / (1 - c * x ** m), c ** n * x ** (m * n), 0
        R = (1 / abs(c)) ** sp.Rational(1, m)
        known, sub = '\\frac{1}{1-u}=\\sum_{n\\ge0}u^n\\ \\ (|u|<1)', f'$u={L(c * x ** m)}$'
    elif fam == 'log':
        f, gen, start = sp.log(1 + c * x), (-1) ** (n + 1) * c ** n * x ** n / n, 1
        R, m = 1 / abs(c), 1
        known, sub = '\\ln(1+u)=\\sum_{n\\ge1}\\frac{(-1)^{n+1}u^n}{n}\\ \\ (|u|<1)', f'$u={L(c * x)}$'
    else:
        f, gen, start = x ** j / (1 + c * x ** m), (-1) ** n * c ** n * x ** (m * n + j), 0
        R = (1 / abs(c)) ** sp.Rational(1, m)
        known, sub = '\\frac{1}{1+u}=\\sum_{n\\ge0}(-1)^nu^n\\ \\ (|u|<1)', f'$u={L(c * x ** m)}$, then multiply by ${L(x ** j)}$'
    first = [sp.simplify(gen.subs(n, q)) for q in range(start, start + 4)]
    deg = sp.degree(first[-1], x) + 1
    Rtex = '\\infty' if R == sp.oo else L(R)
    terms = ''.join(('' if i == 0 or L(q).startswith('-') else '+') + L(q) for i, q in enumerate(first))
    problem = f'<p>Find the Maclaurin series of $f(x)={L(f)}$: write its first four nonzero terms, the series in sigma notation, and its radius of convergence.</p>'
    sol = (f'<p>Start from ${known}$ and substitute {sub}:</p>'
           f'\\[{L(f)}={terms}+\\cdots=\\sum_{{n={start}}}^{{\\infty}}{L(gen)}.\\]'
           + ('<p>The series for $e^u$, $\\sin u$ and $\\cos u$ converge for every $u$, so the radius of convergence is $R=\\infty$.</p>' if R == sp.oo else
              f'<p>The known series converges for $|u|<1$, i.e. $|{L(c * x ** m)}|<1$, which means $|x|<{Rtex}$. So $R={Rtex}$.</p>'))
    return {'problem': problem, 'answer': f'$\\sum_{{n={start}}}^{{\\infty}}{L(gen)}$, $R={Rtex}$', 'solution': sol,
            'data': {'f': f, 'gen': gen, 'start': start, 'R': R, 'deg': deg}}

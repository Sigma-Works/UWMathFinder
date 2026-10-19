"""Math 224 (Advanced Multivariable Calculus) practice-problem templates. See common.py for the contract.

Each check recomputes the answer another way, numerically: integrals in polar,
cylindrical or spherical coordinates are redone in Cartesian coordinates;
Green's, Stokes' and divergence-theorem answers are redone as the line or
surface integral they replace; potentials are differentiated back.
"""
import mpmath
import sympy as sp
from sympy.vector import CoordSys3D, curl as v_curl, divergence as v_div, gradient as v_grad

from common import template, Reject, need, close, nz

C = 'Math 224'
x, y, z, t, r, th, u, v = sp.symbols('x y z t r theta u v', real=True)
rho, ph = sp.symbols('rho phi', positive=True)
pi = sp.pi
N3 = CoordSys3D('N')


def L(e):
    return sp.latex(e, ln_notation=True)


def vtex(F):
    return '\\langle ' + ',\\ '.join(L(c) for c in F) + '\\rangle'


def fnum(e, *vars_):
    return sp.lambdify(vars_, e, 'mpmath')


def as_vec(F):
    sub = {x: N3.x, y: N3.y, z: N3.z}
    return F[0].subs(sub) * N3.i + F[1].subs(sub) * N3.j + F[2].subs(sub) * N3.k


def from_vec(V):
    back = {N3.x: x, N3.y: y, N3.z: z}
    return [sp.expand(sp.sympify(V.dot(e)).subs(back)) for e in (N3.i, N3.j, N3.k)]


def disk_quad(f, R, cx=0):
    """∬ f(x, y) over the disk of radius R centred at (cx, 0), in Cartesian coordinates."""
    R, cx = (mpmath.mpf(str(sp.N(q, 40))) for q in (R, cx))
    def half(X):
        return mpmath.sqrt(max(R ** 2 - (X - cx) ** 2, 0))
    # split at the axes through the origin, where integrands like sqrt(x^2 + y^2) have a kink
    def ys(X):
        h = half(X)
        return [-h, 0, h] if h > 0 else [0, 0]
    xs = sorted({cx - R, cx + R} | ({0} if cx - R < 0 < cx + R else set()))
    return mpmath.quad(lambda X: mpmath.quad(lambda Y: f(X, Y), ys(X)), xs)


def seg_integral(F, A, B):
    """∫ F·dr along the segment from A to B, by direct parametrisation."""
    Fn = [fnum(c, x, y, z) for c in F]
    d = [b - a for a, b in zip(A, B)]
    return mpmath.quad(lambda s: sum(Fn[i](*[a + s * di for a, di in zip(A, d)]) * d[i] for i in range(3)), [0, 1])


def lin_eq(coeffs, names='xyz'):
    out = ''
    for c, n in zip(coeffs, names):
        if c == 0:
            continue
        mag = '' if abs(c) == 1 else str(abs(c))
        out += ('-' if c < 0 else ('+' if out else '')) + mag + n
    return out or '0'


# ── double integrals ─────────────────────────────────────────────────
def chk_polar(d):
    gap = fnum(d['top'] - d['bottom'], x, y)
    need(close(disk_quad(gap, d['R'], d['cx']), sp.N(d['V'], 30), 1e-8), 'volume')


@template(course=C, chapter='double_integrals', id='m224-polar-volume',
          title='Volume between two paraboloids in polar coordinates',
          based_on={'exam': 'm126finalSpr2025', 'problem': 5}, check=chk_polar)
def polar_volume(rng):
    if rng.random() < 0.5:     # centred: z = c - a r^2 above z = b r^2
        a, b, R = rng.choice([1, 2, 3]), rng.choice([1, 2, 3]), rng.choice([1, 2, 3])
        c = (a + b) * R ** 2
        top, bottom, cx = c - a * (x ** 2 + y ** 2), b * (x ** 2 + y ** 2), 0
        hgt = c - (a + b) * r ** 2
        inner = sp.integrate(hgt * r, (r, 0, R))
        V = 2 * pi * inner
        sol = (f'<p>The surfaces meet where ${L(top)}={L(bottom)}$, i.e. $x^2+y^2={R * R}$: a circle of radius ${R}$. '
               f'Over the disk $r\\le {R}$ the top surface is $z={L(top)}$, so the height is ${L(sp.expand(top - bottom))}={L(hgt)}$ in polar form.</p>'
               f'\\[V=\\int_0^{{2\\pi}}\\int_0^{{{R}}}\\left({L(hgt)}\\right)r\\,dr\\,d\\theta.\\]'
               f'<p>Inner integral: $\\left[{L(sp.integrate(hgt * r, r))}\\right]_0^{{{R}}}={L(inner)}$. Then $V=2\\pi\\cdot{L(inner)}={L(V)}$.</p>')
        Rr = R
    else:                      # shifted, as in the original: z = p(x²+y²) over z = (p+1)(x²+y²) - 2kx
        p, k = rng.choice([1, 2, 3]), rng.choice([1, 2, 3])
        top, bottom, cx = p * (x ** 2 + y ** 2), (p + 1) * (x ** 2 + y ** 2) - 2 * k * x, k
        hgt = 2 * k * r * sp.cos(th) - r ** 2
        inner = sp.simplify(sp.integrate(hgt * r, (r, 0, 2 * k * sp.cos(th))))
        V = sp.integrate(inner, (th, -pi / 2, pi / 2))
        sol = (f'<p>The surfaces meet where ${L(top)}={L(bottom)}$, i.e. $x^2+y^2={2 * k}x$. In polar coordinates that is $r^2={2 * k}r\\cos\\theta$, '
               f'the circle $r={2 * k}\\cos\\theta$ for $-\\frac\\pi2\\le\\theta\\le\\frac\\pi2$. Inside it, $z={L(top)}$ is on top and the height is '
               f'${L(sp.expand(top - bottom))}={L(hgt)}$.</p>'
               f'\\[V=\\int_{{-\\pi/2}}^{{\\pi/2}}\\int_0^{{{2 * k}\\cos\\theta}}\\left({L(hgt)}\\right)r\\,dr\\,d\\theta.\\]'
               f'<p>Inner integral: ${L(inner)}$. Integrating over $\\theta$ (using $\\int_{{-\\pi/2}}^{{\\pi/2}}\\cos^4\\theta\\,d\\theta=\\frac{{3\\pi}}{{8}}$): $V={L(V)}$.</p>')
        Rr = k
    problem = f'<p>Use polar coordinates to find the volume of the solid between the paraboloids $z={L(top)}$ and $z={L(bottom)}$.</p>'
    return {'problem': problem, 'answer': f'$V={L(V)}$', 'solution': sol,
            'data': {'top': top, 'bottom': bottom, 'R': Rr, 'cx': cx, 'V': V}}


REV_F = [(sp.exp, 'e^{%s}'), (sp.cos, '\\cos\\left(%s\\right)'), (sp.sin, '\\sin\\left(%s\\right)'), (lambda w: sp.sqrt(1 + w), '\\sqrt{1+%s}')]


def chk_reverse(d):
    f = fnum(d['f'], x)
    k, p, a = d['k'], d['p'], d['a']
    val = mpmath.quad(lambda Y: mpmath.quad(f, [(Y / k) ** (1 / mpmath.mpf(p)), a]), [0, k * a ** p])
    need(close(val, sp.N(d['I'], 30), 1e-8), 'value of the integral')


@template(course=C, chapter='double_integrals', id='m224-reverse-order',
          title='Reverse the order of integration, then evaluate',
          based_on={'exam': 'm126finalWin2025', 'problem': 5}, check=chk_reverse)
def reverse_order(rng):
    p, k, a = rng.choice([1, 2]), rng.choice([1, 2, 3]), rng.choice([1, 2])
    g, gt = rng.choice(REV_F)
    w = x ** (p + 1)
    f = g(w)
    lo = sp.root(y / k, p) if p > 1 else y / k
    I = sp.simplify(sp.integrate(k * x ** p * f, (x, 0, a)))
    W = sp.Symbol('w')
    Gw = sp.integrate(g(W), W)
    problem = (f'<p>Evaluate by reversing the order of integration:</p>'
               f'\\[\\int_0^{{{L(k * a ** p)}}}\\int_{{{L(lo)}}}^{{{a}}} {gt % L(w)}\\,dx\\,dy.\\]')
    sol = (f'<p>The inner integral cannot be done in elementary terms, so describe the region the other way. It is $0\\le y\\le {L(k * a ** p)}$, ${L(lo)}\\le x\\le {a}$: '
           f'the region under the curve $y={L(k * x ** p)}$ for $0\\le x\\le {a}$. So</p>'
           f'\\[\\int_0^{{{a}}}\\int_0^{{{L(k * x ** p)}}} {gt % L(w)}\\,dy\\,dx=\\int_0^{{{a}}} {L(k * x ** p)}\\,{gt % L(w)}\\,dx.\\]'
           f'<p>Substitute $w={L(w)}$, $dw={L(sp.diff(w, x))}\\,dx$, so $w$ runs from $0$ to ${L(a ** (p + 1))}$:</p>'
           f'\\[{L(sp.Rational(k, p + 1))}\\int_0^{{{L(a ** (p + 1))}}} {gt % "w"}\\,dw={L(sp.Rational(k, p + 1))}\\left[{L(Gw)}\\right]_0^{{{L(a ** (p + 1))}}}={L(I)}.\\]')
    return {'problem': problem, 'answer': f'${L(I)}$', 'solution': sol, 'data': {'f': f, 'k': k, 'p': p, 'a': a, 'I': I}}


# ── surface area ─────────────────────────────────────────────────────
def chk_area(d):
    g = fnum(sp.sqrt(1 + sp.diff(d['zf'], x) ** 2 + sp.diff(d['zf'], y) ** 2), x, y)
    if d['kind'] == 'disk':
        val = disk_quad(g, d['R'])
    else:
        X0, Y0 = d['X0'], d['Y0']
        val = mpmath.quad(lambda X: mpmath.quad(lambda Y: g(X, Y), [0, Y0 * (1 - X / X0)]), [0, X0])
    need(close(val, sp.N(d['A'], 30), 1e-8), 'surface area')


@template(course=C, chapter='surface_area', id='m224-surface-area',
          title='Surface area of a graph', based_on={'style': 'Stewart §15.5'}, check=chk_area)
def surface_area(rng):
    if rng.random() < 0.5:
        a, R2 = rng.choice([(1, sp.Integer(2)), (1, sp.Integer(6)), (1, sp.Integer(12)), (2, sp.Rational(1, 2)), (2, sp.Rational(3, 2)), (3, sp.Rational(2, 9))])
        h = rng.choice([4, 9, 16])
        if a * R2 > h:
            raise Reject
        R = sp.sqrt(R2)
        zf = h - a * (x ** 2 + y ** 2)
        inside = 1 + 4 * a ** 2 * r ** 2
        A = sp.simplify(sp.integrate(sp.integrate(sp.sqrt(inside) * r, (r, 0, R)), (th, 0, 2 * pi)))
        problem = f'<p>Find the area of the part of the paraboloid $z={L(zf)}$ that lies above the plane $z={L(h - a * R2)}$.</p>'
        sol = (f'<p>The paraboloid is above $z={L(h - a * R2)}$ when ${L(a * (x ** 2 + y ** 2))}\\le{L(a * R2)}$, i.e. over the disk $x^2+y^2\\le{L(R2)}$ (radius ${L(R)}$).</p>'
               f'<p>With $z_x={L(sp.diff(zf, x))}$ and $z_y={L(sp.diff(zf, y))}$, $dS=\\sqrt{{1+z_x^2+z_y^2}}\\,dA=\\sqrt{{1+{4 * a * a}(x^2+y^2)}}\\,dA$. In polar coordinates:</p>'
               f'\\[A=\\int_0^{{2\\pi}}\\int_0^{{{L(R)}}}\\sqrt{{{L(inside)}}}\\,r\\,dr\\,d\\theta=2\\pi\\left[\\frac{{\\left({L(inside)}\\right)^{{3/2}}}}{{{12 * a * a}}}\\right]_0^{{{L(R)}}}={L(A)}.\\]')
        data = {'zf': zf, 'kind': 'disk', 'R': R, 'A': A}
    else:
        a, b, c = rng.choice([(1, 2, 2), (2, 1, 2), (2, 2, 1), (2, 3, 6), (3, 6, 2), (6, 2, 3), (4, 4, 7), (1, 4, 8), (8, 4, 1)])
        dd = rng.choice([a * b * c, 2 * a * b * c, 12])
        X0, Y0 = sp.Rational(dd, a), sp.Rational(dd, b)
        zf = (dd - a * x - b * y) / sp.Integer(c)
        n = sp.sqrt(a * a + b * b + c * c)
        A = n / c * X0 * Y0 / 2
        problem = f'<p>Find the area of the part of the plane ${a}x+{b}y+{c}z={dd}$ that lies in the first octant.</p>'
        sol = (f'<p>Solve for $z={L(zf)}$, so $z_x={L(sp.Rational(-a, c))}$, $z_y={L(sp.Rational(-b, c))}$ and '
               f'$\\sqrt{{1+z_x^2+z_y^2}}=\\frac{{\\sqrt{{{a * a}+{b * b}+{c * c}}}}}{{{c}}}={L(n / c)}$, a constant.</p>'
               f'<p>The piece lies over the triangle in the $xy$-plane with vertices $(0,0)$, $({L(X0)},0)$, $(0,{L(Y0)})$, of area $\\frac12({L(X0)})({L(Y0)})={L(X0 * Y0 / 2)}$. So</p>'
               f'\\[A={L(n / c)}\\cdot{L(X0 * Y0 / 2)}={L(A)}.\\]')
        data = {'zf': zf, 'kind': 'tri', 'X0': X0, 'Y0': Y0, 'A': A}
    return {'problem': problem, 'answer': f'${L(data["A"])}$', 'solution': sol, 'data': data}


# ── triple integrals ─────────────────────────────────────────────────
def chk_cyl(d):
    inner = sp.integrate(d['dens'], (z, 0, d['top']))      # z-integral in Cartesian coordinates, then the disk numerically
    need(close(disk_quad(fnum(inner, x, y), d['R']), sp.N(d['M'], 30), 1e-8), 'mass')


@template(course=C, chapter='triple_integrals', id='m224-triple-cylindrical',
          title='Mass of a solid in cylindrical coordinates',
          based_on={'exam': 'm324finalSpr1997_LeeA', 'problem': 5}, check=chk_cyl)
def triple_cyl(rng):
    R = rng.choice([1, 2, 3])
    h = R * R + rng.choice([0, 1, 3, 5])
    top = h - (x ** 2 + y ** 2)
    dens, dens_c, dname = rng.choice([(z, z, '$\\delta=z$'), (x ** 2 + y ** 2, r ** 2, '$\\delta=x^2+y^2$'), (sp.Integer(1), sp.Integer(1), 'constant, $\\delta=1$'),
                                      (sp.sqrt(x ** 2 + y ** 2), r, 'equal to the distance to the $z$-axis')])
    topc = h - r ** 2
    zint = sp.integrate(dens_c, (z, 0, topc))
    rint = sp.integrate(zint * r, (r, 0, R))
    M = sp.simplify(2 * pi * rint)
    integrand = '' if dens_c == 1 else L(dens_c) + '\\,'
    problem = (f'<p>A solid lies inside the cylinder $x^2+y^2={R * R}$, above the plane $z=0$ and below the paraboloid $z={L(top)}$. '
               f'Its density is {dname}. Find its mass.</p>')
    sol = (f'<p>In cylindrical coordinates the solid is $0\\le\\theta\\le2\\pi$, $0\\le r\\le{R}$, $0\\le z\\le{L(topc)}$, and $dV=r\\,dz\\,dr\\,d\\theta$:</p>'
           f'\\[M=\\int_0^{{2\\pi}}\\int_0^{{{R}}}\\int_0^{{{L(topc)}}}{integrand}r\\,dz\\,dr\\,d\\theta.\\]'
           f'<p>The $z$-integral gives $\\left({L(sp.expand(zint))}\\right)r$; the $r$-integral gives ${L(rint)}$; the $\\theta$-integral multiplies by $2\\pi$:</p>'
           f'\\[M={L(M)}.\\]')
    return {'problem': problem, 'answer': f'$M={L(M)}$', 'solution': sol, 'data': {'dens': dens, 'top': top, 'R': R, 'M': M}}


def chk_sph(d):
    a, phi0 = d['a'], mpmath.mpf(d['phi0'])
    rmax = a * mpmath.sin(phi0)
    cot = mpmath.cos(phi0) / mpmath.sin(phi0)
    lo, hi = sp.symbols('lo hi')
    zf = fnum(sp.integrate(d['dens'], (z, lo, hi)), x, y, lo, hi)
    f = lambda X, Y: zf(X, Y, mpmath.sqrt(X * X + Y * Y) * cot, mpmath.sqrt(a * a - X * X - Y * Y))
    need(close(disk_quad(f, rmax), sp.N(d['V'], 30), 1e-7), 'value in Cartesian coordinates')


@template(course=C, chapter='triple_integrals', id='m224-triple-spherical',
          title='An "ice-cream cone" in spherical coordinates', based_on={'style': 'Stewart §15.8'}, check=chk_sph)
def triple_sph(rng):
    a = rng.choice([1, 2, 3])
    phi0 = rng.choice([pi / 6, pi / 4, pi / 3])
    kind = rng.choice(['volume', 'z', 'rho2'])
    cone = {pi / 6: 'z=\\sqrt{3(x^2+y^2)}', pi / 4: 'z=\\sqrt{x^2+y^2}', pi / 3: 'z=\\sqrt{(x^2+y^2)/3}'}[phi0]
    if kind == 'volume':
        integrand, dens, what, itex = sp.Integer(1), sp.Integer(1), 'its volume', ''
    elif kind == 'z':
        integrand, dens, what, itex = rho * sp.cos(ph), z, '$\\iiint_E z\\,dV$', ', and $z=\\rho\\cos\\phi$'
    else:
        integrand, dens, what, itex = rho ** 2, x ** 2 + y ** 2 + z ** 2, '$\\iiint_E (x^2+y^2+z^2)\\,dV$', ', and $x^2+y^2+z^2=\\rho^2$'
    f = integrand * rho ** 2 * sp.sin(ph)
    i_rho = sp.integrate(f, (rho, 0, a))
    i_phi = sp.simplify(sp.integrate(i_rho, (ph, 0, phi0)))
    V = sp.simplify(2 * pi * i_phi)
    problem = f'<p>$E$ is the solid above the cone ${cone}$ and inside the sphere $x^2+y^2+z^2={a * a}$. Use spherical coordinates to find {what}.</p>'
    sol = (f'<p>The sphere is $\\rho={a}$ and the cone is $\\phi={L(phi0)}$, so $E$ is $0\\le\\rho\\le{a}$, $0\\le\\phi\\le{L(phi0)}$, $0\\le\\theta\\le2\\pi$, '
           f'with $dV=\\rho^2\\sin\\phi\\,d\\rho\\,d\\phi\\,d\\theta${itex}:</p>'
           f'\\[\\int_0^{{2\\pi}}\\int_0^{{{L(phi0)}}}\\int_0^{{{a}}}{L(f)}\\,d\\rho\\,d\\phi\\,d\\theta.\\]'
           f'<p>$\\rho$-integral: ${L(i_rho)}$. $\\phi$-integral: ${L(i_phi)}$. Times $2\\pi$:</p>\\[{L(V)}.\\]')
    return {'problem': problem, 'answer': f'${L(V)}$', 'solution': sol, 'data': {'a': a, 'phi0': float(phi0), 'dens': dens, 'V': V}}


# ── change of variables ──────────────────────────────────────────────
def chk_cov(d):
    (a, b), (c, e) = d['U'], d['V']
    p1, p2, q1, q2 = d['p1'], d['p2'], d['q1'], d['q2']
    f = fnum(d['f'], x, y)

    def ybounds(X):
        lo, hi = -mpmath.inf, mpmath.inf
        for (cx, cy, l, h) in ((a, b, p1, p2), (c, e, q1, q2)):
            if cy == 0:
                if not (l <= cx * X <= h):
                    return None
                continue
            y1, y2 = (l - cx * X) / mpmath.mpf(cy), (h - cx * X) / mpmath.mpf(cy)
            lo, hi = max(lo, min(y1, y2)), min(hi, max(y1, y2))
        return (lo, hi) if hi > lo else None

    Mi = sp.Matrix([[a, b], [c, e]]).inv()
    brk = sorted({float(Mi[0, 0] * U + Mi[0, 1] * W) for U in (p1, p2) for W in (q1, q2)})

    def inner(X):
        bd = ybounds(X)
        return mpmath.quad(lambda Y: f(X, Y), list(bd)) if bd else 0
    need(close(mpmath.quad(inner, brk), sp.N(d['I'], 30), 1e-7), 'value over the parallelogram in x, y')


@template(course=C, chapter='change_of_variables', id='m224-change-of-variables',
          title='A double integral over a parallelogram by a change of variables', based_on={'style': 'Stewart §15.9'}, check=chk_cov)
def change_vars(rng):
    a, b = rng.choice([(1, 1), (1, 2), (2, 1), (1, -1)])
    c, e = rng.choice([(1, -1), (1, -2), (2, -1), (1, 3), (3, -1)])
    det = a * e - b * c
    if det == 0:
        raise Reject
    p1, p2 = sorted(rng.sample(range(0, 5), 2))
    q1, q2 = sorted(rng.sample(range(-2, 4), 2))
    U, V = a * x + b * y, c * x + e * y
    kind = rng.choice(['uv2', 'u_exp', 'poly'])
    g = {'uv2': u * v ** 2, 'u_exp': u * sp.exp(v), 'poly': u ** 2 + v}[kind]
    f = g.subs({u: U, v: V})
    I = sp.simplify(sp.Rational(1, abs(det)) * sp.integrate(sp.integrate(g, (v, q1, q2)), (u, p1, p2)))
    gx = {'uv2': f'({L(U)})({L(V)})^2', 'u_exp': f'({L(U)})\\,e^{{{L(V)}}}', 'poly': f'({L(U)})^2+({L(V)})'}[kind]
    problem = (f'<p>$R$ is the parallelogram bounded by the lines ${L(U)}={p1}$, ${L(U)}={p2}$, ${L(V)}={q1}$ and ${L(V)}={q2}$. Use a change of variables to evaluate</p>'
               f'\\[\\iint_R {gx}\\,dA.\\]')
    sol = (f'<p>Let $u={L(U)}$ and $v={L(V)}$. Then $R$ becomes the rectangle ${p1}\\le u\\le{p2}$, ${q1}\\le v\\le{q2}$ and the integrand is ${L(g)}$.</p>'
           f'<p>Jacobian: $\\frac{{\\partial(u,v)}}{{\\partial(x,y)}}=\\begin{{vmatrix}}{a}&{b}\\\\{c}&{e}\\end{{vmatrix}}={det}$, so '
           f'$\\left|\\frac{{\\partial(x,y)}}{{\\partial(u,v)}}\\right|=\\frac{{1}}{{{abs(det)}}}$ and $dA=\\frac{{1}}{{{abs(det)}}}\\,du\\,dv$.</p>'
           f'\\[\\iint_R {gx}\\,dA=\\frac{{1}}{{{abs(det)}}}\\int_{{{p1}}}^{{{p2}}}\\int_{{{q1}}}^{{{q2}}}{L(g)}\\,dv\\,du=\\frac{{1}}{{{abs(det)}}}\\int_{{{p1}}}^{{{p2}}}{L(sp.integrate(g, (v, q1, q2)))}\\,du={L(I)}.\\]')
    return {'problem': problem, 'answer': f'${L(I)}$', 'solution': sol,
            'data': {'U': (a, b), 'V': (c, e), 'p1': p1, 'p2': p2, 'q1': q1, 'q2': q2, 'f': f, 'I': I}}


# ── gradient ─────────────────────────────────────────────────────────
def chk_flow(d):
    rt, P, FP, n = d['r'], d['P'], d['FP'], d['plane']
    need([c.subs(t, 0) for c in rt] == list(P), 'flow line passes through P')
    need([sp.diff(c, t).subs(t, 0) for c in rt] == list(FP), 'F(P) is the velocity of the flow line')
    a, b, c, dd = n
    need(a * P[0] + b * P[1] + c * P[2] == dd and [a, b, c] == list(FP), 'tangent plane through P with normal F(P)')


@template(course=C, chapter='chain_rule_and_gradient', id='m224-flow-line-gradient',
          title='A gradient field from one of its flow lines; tangent plane to a level surface',
          based_on={'exam': 'm324test2Spr1997_LeeA', 'problem': 4}, check=chk_flow)
def flow_line(rng):
    P = [rng.randint(-2, 2) for _ in range(3)]
    rt = [P[i] + nz(rng, -3, 3) * t + rng.randint(-2, 2) * t ** rng.choice([2, 3]) for i in range(3)]
    FP = [sp.diff(c, t).subs(t, 0) for c in rt]
    dd = sum(a * p for a, p in zip(FP, P))
    lhs = lin_eq(FP)
    point = lambda i: f'({"xyz"[i]}{"-" if P[i] >= 0 else "+"}{abs(P[i])})' if P[i] else "xyz"[i]
    expanded = ''.join(f'{"+" if (FP[i] > 0 and i) else ""}{"-" if FP[i] < 0 else ""}{"" if abs(FP[i]) == 1 else abs(FP[i])}{point(i)}' for i in range(3) if FP[i])
    problem = (f'<p>$\\vec F=\\nabla f$ for some function $f(x,y,z)$. The flow line of $\\vec F$ that passes through $P({P[0]},{P[1]},{P[2]})$ at time $t=0$ is</p>'
               f'\\[\\vec r(t)={vtex(rt)}.\\]'
               f'<p>(a) Find $\\vec F({P[0]},{P[1]},{P[2]})$.<br>(b) Find an equation of the tangent plane at $P$ to the level surface of $f$ through $P$.</p>')
    sol = (f'<p><strong>(a)</strong> A flow line is a curve whose velocity at each point equals the field there: $\\vec r\\,{{}}\'(t)=\\vec F(\\vec r(t))$. '
           f'Here $\\vec r(0)=P$ and $\\vec r\\,{{}}\'(t)={vtex([sp.diff(c, t) for c in rt])}$, so</p>\\[\\vec F(P)=\\vec r\\,{{}}\'(0)={vtex(FP)}.\\]'
           f'<p><strong>(b)</strong> $\\nabla f(P)=\\vec F(P)$ is perpendicular to the level surface of $f$ through $P$, so it is a normal vector of the tangent plane:</p>'
           f'\\[{expanded}=0\\quad\\Longleftrightarrow\\quad {lhs}={dd}.\\]')
    return {'problem': problem, 'answer': f'$\\vec F(P)={vtex(FP)}$; tangent plane ${lhs}={dd}$', 'solution': sol,
            'data': {'r': rt, 'P': P, 'FP': FP, 'plane': [*FP, dd]}}


def chk_dir(d):
    f = fnum(d['f'], x, y, z)
    P, uvec = d['P'], d['u']
    D = mpmath.diff(lambda h: f(*[p + h * c for p, c in zip(P, uvec)]), 0)
    need(close(D, sp.N(d['D'], 30), 1e-9), 'directional derivative')
    gm = [mpmath.diff(lambda h, i=i: f(*[p + (h if j == i else 0) for j, p in enumerate(P)]), 0) for i in range(3)]
    need(close(mpmath.sqrt(sum(g * g for g in gm)), sp.N(d['maxrate'], 30), 1e-9), 'maximum rate')


@template(course=C, chapter='chain_rule_and_gradient', id='m224-directional-derivative',
          title='Directional derivative and the direction of fastest increase', based_on={'style': 'Stewart §14.6'}, check=chk_dir)
def directional(rng):
    a, b, c = nz(rng, -3, 3), nz(rng, -3, 3), nz(rng, -2, 2)
    f = rng.choice([a * x ** 2 * y + b * y * z ** 2 + c * x * z, a * x * y * z + b * x ** 2 + c * z ** 3, a * x * sp.exp(y * z) + b * y ** 2])
    P = [rng.randint(-2, 2), rng.randint(-2, 2), rng.randint(-1, 2)]
    vdir = rng.choice([[1, 2, 2], [2, -1, 2], [2, 3, 6], [1, -4, 8], [3, 0, 4], [0, 3, -4], [6, 2, -3]])
    vdir = [rng.choice([1, -1]) * w for w in vdir]
    norm = sp.sqrt(sum(w * w for w in vdir))
    grad = [sp.diff(f, w) for w in (x, y, z)]
    gP = [g.subs({x: P[0], y: P[1], z: P[2]}) for g in grad]
    if all(g == 0 for g in gP):
        raise Reject
    D = sp.nsimplify(sum(g * w for g, w in zip(gP, vdir)) / norm)
    maxrate = sp.sqrt(sum(g * g for g in gP))
    problem = (f'<p>Let $f(x,y,z)={L(f)}$ and $P=({P[0]},{P[1]},{P[2]})$.</p>'
               f'<p>(a) Find the directional derivative of $f$ at $P$ in the direction of $\\vec v={vtex(vdir)}$.<br>'
               f'(b) In which direction does $f$ increase fastest at $P$, and what is that maximum rate?</p>')
    sol = (f'<p>Gradient: $\\nabla f={vtex(grad)}$, so $\\nabla f(P)={vtex(gP)}$.</p>'
           f'<p><strong>(a)</strong> $|\\vec v|={L(norm)}$, so the unit vector is $\\vec u=\\frac{{1}}{{{L(norm)}}}{vtex(vdir)}$ and</p>'
           f'\\[D_{{\\vec u}}f(P)=\\nabla f(P)\\cdot\\vec u=\\frac{{{L(sum(g * w for g, w in zip(gP, vdir)))}}}{{{L(norm)}}}={L(D)}.\\]'
           f'<p><strong>(b)</strong> $f$ increases fastest in the direction of $\\nabla f(P)={vtex(gP)}$, at the rate $|\\nabla f(P)|={L(maxrate)}$.</p>')
    return {'problem': problem, 'answer': f'(a) ${L(D)}$ &nbsp; (b) direction ${vtex(gP)}$, rate ${L(maxrate)}$', 'solution': sol,
            'data': {'f': f, 'P': P, 'u': [float(w / norm) for w in vdir], 'D': D, 'maxrate': maxrate}}


# ── line integrals ───────────────────────────────────────────────────
def chk_segment(d):
    need(close(seg_integral(d['F'], d['A'], d['B']), sp.N(d['W'], 30), 1e-10), 'work along the segment')


@template(course=C, chapter='vector_fields_and_line_integrals', id='m224-line-integral-segment',
          title='Line integral of a vector field along a segment',
          based_on={'exam': 'm324test3Spr1997_Lee', 'problem': 1}, check=chk_segment)
def line_segment(rng):
    pool = [x, y, z, x * y, y * z, x * z, z ** 2, x ** 2, y ** 2, sp.Integer(1)]
    F = [nz(rng, -2, 2) * rng.choice(pool) for _ in range(3)]
    A = [rng.randint(0, 3), rng.randint(0, 3), rng.randint(0, 2)]
    B = [rng.randint(0, 3), rng.randint(0, 3), rng.randint(0, 3)]
    if A == B:
        raise Reject
    d = [b - a for a, b in zip(A, B)]
    rt = [a + di * t for a, di in zip(A, d)]
    on = [sp.expand(Fi.subs({x: rt[0], y: rt[1], z: rt[2]})) for Fi in F]
    integrand = sp.expand(sum(Fi * di for Fi, di in zip(on, d)))
    W = sp.integrate(integrand, (t, 0, 1))
    problem = (f'<p>Let $\\vec F={vtex(F)}$ and let $C$ be the line segment from $A({A[0]},{A[1]},{A[2]})$ to $B({B[0]},{B[1]},{B[2]})$. Compute $\\displaystyle\\int_C\\vec F\\cdot d\\vec r$.</p>')
    sol = (f'<p>Parametrize: $\\vec r(t)=A+t(B-A)={vtex(rt)}$ for $0\\le t\\le1$, so $\\vec r\\,{{}}\'(t)={vtex(d)}$.</p>'
           f'<p>On $C$, $\\vec F(\\vec r(t))={vtex(on)}$, and $\\vec F(\\vec r(t))\\cdot\\vec r\\,{{}}\'(t)={L(integrand)}$.</p>'
           f'\\[\\int_C\\vec F\\cdot d\\vec r=\\int_0^1\\left({L(integrand)}\\right)dt={L(W)}.\\]')
    return {'problem': problem, 'answer': f'${L(W)}$', 'solution': sol, 'data': {'F': F, 'A': A, 'B': B, 'W': W}}


FTLI_F = [lambda r_: sp.exp(r_.choice([1, 2, -1]) * x * y), lambda r_: x ** 2 * y + r_.choice([1, 2, 3]) * y ** 2, lambda r_: sp.sin(x * y) + x,
          lambda r_: x * sp.exp(y) + r_.choice([1, 2]) * y, lambda r_: x ** 2 * y ** 2 + r_.choice([1, 3]) * x]
FTLI_C = [(sp.sin(x), 0, pi, 'y=\\sin x', '(0,0)', '(\\pi,0)'), (x ** 2, 0, 2, 'y=x^2', '(0,0)', '(2,4)'),
          (sp.sqrt(x), 0, 4, 'y=\\sqrt x', '(0,0)', '(4,2)'), (x ** 3 - x, -1, 2, 'y=x^3-x', '(-1,0)', '(2,6)'), (sp.cos(x), 0, pi, 'y=\\cos x', '(0,1)', '(\\pi,-1)')]


def chk_ftli(d):
    F = [sp.diff(d['f'], x), sp.diff(d['f'], y)]
    g = d['g']
    Fx, Fy, gp, gn = fnum(F[0], x, y), fnum(F[1], x, y), fnum(sp.diff(g, x), x), fnum(g, x)
    lo = mpmath.mpf(float(d['x0'])) + (mpmath.mpf('1e-30') if g == sp.sqrt(x) else 0)
    val = mpmath.quad(lambda X: Fx(X, gn(X)) + Fy(X, gn(X)) * gp(X), [lo, float(d['x1'])])
    need(close(val, sp.N(d['W'], 30), 1e-8), 'line integral along the curve')


@template(course=C, chapter='vector_fields_and_line_integrals', id='m224-fundamental-theorem',
          title='The fundamental theorem for line integrals',
          based_on={'exam': 'm324test3Spr1997_Lee', 'problem': 3}, check=chk_ftli)
def ftli(rng):
    f = rng.choice(FTLI_F)(rng)
    g, x0, x1, ctex, Ptex, Qtex = rng.choice(FTLI_C)
    P = (x0, g.subs(x, x0))
    Q = (x1, g.subs(x, x1))
    fP, fQ = f.subs({x: P[0], y: P[1]}), f.subs({x: Q[0], y: Q[1]})
    W = sp.simplify(fQ - fP)
    form = rng.choice(['grad', 'field'])
    F = [sp.diff(f, x), sp.diff(f, y)]
    given = f'$\\vec G=\\operatorname{{grad}}\\left({L(f)}\\right)$' if form == 'grad' else f'$\\vec G={vtex(F)}$'
    problem = f'<p>$C$ is the part of the curve ${ctex}$ from ${Ptex}$ to ${Qtex}$, and {given}. Evaluate $\\displaystyle\\int_C\\vec G\\cdot d\\vec r$.</p>'
    find = ('' if form == 'grad' else
            f'<p>First look for a potential: integrating $f_x={L(F[0])}$ in $x$ gives ${L(f - f.subs(x, 0))}$ plus a function of $y$, and matching $f_y={L(F[1])}$ gives $f={L(f)}$. So $\\vec G=\\nabla f$.</p>')
    sol = (find + f'<p>Since $\\vec G=\\nabla f$ with $f(x,y)={L(f)}$, the integral depends only on the endpoints (the fundamental theorem for line integrals):</p>'
           f'\\[\\int_C\\nabla f\\cdot d\\vec r=f{Qtex}-f{Ptex}={L(fQ)}-\\left({L(fP)}\\right)={L(W)}.\\]')
    return {'problem': problem, 'answer': f'${L(W)}$', 'solution': sol, 'data': {'f': f, 'g': g, 'x0': x0, 'x1': x1, 'W': W}}


# ── Green's theorem ──────────────────────────────────────────────────
def chk_green(d):
    P, Q = d['P'], d['Q']
    if d['kind'] == 'circle':
        R = d['R']
        Pn, Qn = fnum(P, x, y), fnum(Q, x, y)
        val = mpmath.quad(lambda T: Pn(R * mpmath.cos(T), R * mpmath.sin(T)) * (-R * mpmath.sin(T)) +
                          Qn(R * mpmath.cos(T), R * mpmath.sin(T)) * (R * mpmath.cos(T)), [0, 2 * mpmath.pi])
    else:
        vs = d['verts']
        F = [P, Q, sp.Integer(0)]
        val = sum(seg_integral(F, list(vs[i]) + [0], list(vs[(i + 1) % len(vs)]) + [0]) for i in range(len(vs)))
    need(close(val, sp.N(d['W'], 30), 1e-9), 'circulation computed directly')


@template(course=C, chapter='greens_theorem', id='m224-greens-theorem',
          title="Circulation around a closed curve with Green's theorem", based_on={'style': 'Stewart §16.4'}, check=chk_green)
def greens(rng):
    kind = rng.choice(['rect', 'tri', 'circle'])
    pool = [x * y, y ** 2, x ** 2 * y, x * y ** 2, y ** 3, x ** 2, y, x] + ([] if kind == 'circle' else [sp.exp(x)])   # e^x over a disk has no closed form
    P = nz(rng, -3, 3) * rng.choice(pool) + rng.choice([0, nz(rng, -2, 2) * rng.choice(pool)])
    Q = nz(rng, -3, 3) * rng.choice(pool) + rng.choice([0, nz(rng, -2, 2) * rng.choice(pool)])
    curlz = sp.expand(sp.diff(Q, x) - sp.diff(P, y))
    if curlz == 0:
        raise Reject
    if kind == 'rect':
        a, b = rng.choice([1, 2, 3]), rng.choice([1, 2])
        W = sp.integrate(sp.integrate(curlz, (y, 0, b)), (x, 0, a))
        cdesc = f'the boundary of the rectangle $0\\le x\\le{a}$, $0\\le y\\le{b}$'
        setup = f'\\int_0^{{{a}}}\\int_0^{{{b}}}\\left({L(curlz)}\\right)dy\\,dx'
        data = {'verts': [(0, 0), (a, 0), (a, b), (0, b)]}
    elif kind == 'tri':
        a = rng.choice([1, 2, 3])
        W = sp.integrate(sp.integrate(curlz, (y, 0, a - x)), (x, 0, a))
        cdesc = f'the triangle with vertices $(0,0)$, $({a},0)$ and $(0,{a})$'
        setup = f'\\int_0^{{{a}}}\\int_0^{{{a}-x}}\\left({L(curlz)}\\right)dy\\,dx'
        data = {'verts': [(0, 0), (a, 0), (0, a)]}
    else:
        R = rng.choice([1, 2, 3])
        cz = sp.expand(curlz.subs({x: r * sp.cos(th), y: r * sp.sin(th)}))
        W = sp.simplify(sp.integrate(sp.integrate(cz * r, (r, 0, R)), (th, 0, 2 * pi)))
        cdesc = f'the circle $x^2+y^2={R * R}$'
        setup = f'\\int_0^{{2\\pi}}\\int_0^{{{R}}}\\left({L(cz)}\\right)r\\,dr\\,d\\theta'
        data = {'R': R}
    if W == 0 and rng.random() < 0.7:
        raise Reject
    problem = (f'<p>Let $\\vec F={vtex([P, Q])}$ and let $C$ be {cdesc}, oriented counterclockwise. Use Green\'s theorem to compute $\\displaystyle\\oint_C\\vec F\\cdot d\\vec r$.</p>')
    sol = (f'<p>Green\'s theorem: $\\oint_C P\\,dx+Q\\,dy=\\iint_D\\left(\\frac{{\\partial Q}}{{\\partial x}}-\\frac{{\\partial P}}{{\\partial y}}\\right)dA$, where $D$ is the region inside $C$.</p>'
           f'<p>$\\frac{{\\partial Q}}{{\\partial x}}={L(sp.diff(Q, x))}$ and $\\frac{{\\partial P}}{{\\partial y}}={L(sp.diff(P, y))}$, so the integrand is ${L(curlz)}$.</p>'
           f'\\[\\oint_C\\vec F\\cdot d\\vec r={setup}={L(W)}.\\]')
    return {'problem': problem, 'answer': f'${L(W)}$', 'solution': sol, 'data': {'P': P, 'Q': Q, 'kind': kind, 'W': W, **data}}


# ── curl and divergence ──────────────────────────────────────────────
def chk_divcurl(d):
    sub = {x: N3.x, y: N3.y, z: N3.z}
    back = {N3.x: x, N3.y: y, N3.z: z}
    fv = d['f'].subs(sub)
    need(from_vec(v_grad(fv)) == [sp.expand(c) for c in d['grad']], 'gradient')
    G = as_vec(d['G'])
    need(sp.expand(v_div(G).subs(back)) == sp.expand(d['div']), 'divergence')
    need(from_vec(v_curl(G)) == [sp.expand(c) for c in d['curl']], 'curl')
    need(sp.expand(v_div(v_grad(fv)).subs(back)) == sp.expand(d['lap']), 'Laplacian')


@template(course=C, chapter='curl_and_divergence', id='m224-div-curl',
          title='Gradient, divergence and curl',
          based_on={'exam': 'm324test2Spr1997_LeeA', 'problem': 2}, check=chk_divcurl)
def div_curl(rng):
    mon = [x * z, y * z, x * y, x ** 2, y ** 2, z ** 2, x ** 2 * y, y * z ** 2, x * y * z, sp.exp(x) * z, x * sp.exp(z)]
    f = nz(rng, -3, 3) * rng.choice(mon) + nz(rng, -3, 3) * rng.choice(mon)
    G = [nz(rng, -2, 3) * rng.choice(mon) for _ in range(3)]
    grad = [sp.diff(f, w) for w in (x, y, z)]
    div = sum(sp.diff(Gi, w) for Gi, w in zip(G, (x, y, z)))
    curl = [sp.diff(G[2], y) - sp.diff(G[1], z), sp.diff(G[0], z) - sp.diff(G[2], x), sp.diff(G[1], x) - sp.diff(G[0], y)]
    lap = sum(sp.diff(f, w, 2) for w in (x, y, z))
    P, Q, R = G
    problem = (f'<p>Let $f(x,y,z)={L(f)}$ and $\\vec G={vtex(G)}$. Compute:</p>'
               '<p>(a) $\\nabla f$ &nbsp; (b) $\\nabla\\cdot\\vec G$ &nbsp; (c) $\\nabla\\times\\vec G$ &nbsp; (d) $\\nabla\\cdot(\\nabla f)$</p>')
    sol = (f'<p><strong>(a)</strong> $\\nabla f=\\langle f_x,f_y,f_z\\rangle={vtex(grad)}$.</p>'
           f'<p><strong>(b)</strong> $\\nabla\\cdot\\vec G=\\frac{{\\partial}}{{\\partial x}}\\left({L(P)}\\right)+\\frac{{\\partial}}{{\\partial y}}\\left({L(Q)}\\right)+\\frac{{\\partial}}{{\\partial z}}\\left({L(R)}\\right)={L(div)}$.</p>'
           f'<p><strong>(c)</strong></p>\\[\\nabla\\times\\vec G=\\left\\langle \\frac{{\\partial R}}{{\\partial y}}-\\frac{{\\partial Q}}{{\\partial z}},\\ \\frac{{\\partial P}}{{\\partial z}}-\\frac{{\\partial R}}{{\\partial x}},\\ \\frac{{\\partial Q}}{{\\partial x}}-\\frac{{\\partial P}}{{\\partial y}}\\right\\rangle={vtex(curl)}.\\]'
           f'<p><strong>(d)</strong> $\\nabla\\cdot(\\nabla f)=f_{{xx}}+f_{{yy}}+f_{{zz}}={L(lap)}$.</p>')
    return {'problem': problem, 'answer': f'(a) ${vtex(grad)}$ (b) ${L(div)}$ (c) ${vtex(curl)}$ (d) ${L(lap)}$', 'solution': sol,
            'data': {'f': f, 'G': G, 'grad': grad, 'div': div, 'curl': curl, 'lap': lap}}


def chk_potential(d):
    G = d['G']
    cz = from_vec(v_curl(as_vec(G)))
    need(all(c == 0 for c in cz) == d['conservative'], 'curl test')
    if d['conservative']:
        need([sp.simplify(sp.diff(d['f'], w) - Gi) for w, Gi in zip((x, y, z), G)] == [0, 0, 0], 'potential')


@template(course=C, chapter='curl_and_divergence', id='m224-curl-test-potential',
          title='Curl test, and a potential function if there is one',
          based_on={'exam': 'm324test3Spr1997_Lee', 'problem': 5}, check=chk_potential)
def potential(rng):
    mon = [x * y, y * z, x * z, x ** 2 * y, x * y * z, y ** 2 * z, sp.exp(x) * y, z * sp.sin(y), x ** 3, z ** 2]
    f = sum(nz(rng, -3, 3) * m for m in rng.sample(mon, 3))
    G = [sp.expand(sp.diff(f, w)) for w in (x, y, z)]
    conservative = rng.random() < 0.65
    if not conservative:
        i = rng.randrange(3)
        G[i] = sp.expand(G[i] + nz(rng, -2, 2) * rng.choice([w for w in (x, y, z) if w != (x, y, z)[i]]))
    curl = [sp.expand(c) for c in (sp.diff(G[2], y) - sp.diff(G[1], z), sp.diff(G[0], z) - sp.diff(G[2], x), sp.diff(G[1], x) - sp.diff(G[0], y))]
    if conservative != all(c == 0 for c in curl):
        raise Reject
    problem = f'<p>Is $\\vec G={vtex(G)}$ conservative? If it is, find a potential function $f$ with $\\nabla f=\\vec G$.</p>'
    sol = f'<p>Curl test (the domain is all of $\\mathbb R^3$, so curl $=\\vec 0$ means conservative):</p>\\[\\nabla\\times\\vec G={vtex(curl)}.\\]'
    if not conservative:
        sol += '<p>The curl is not zero, so $\\vec G$ is <strong>not conservative</strong>: no potential exists.</p>'
        return {'problem': problem, 'answer': '<p>Not conservative (its curl is not $\\vec 0$).</p>', 'solution': sol, 'data': {'G': G, 'conservative': False}}
    g1 = sp.integrate(G[0], x)
    rest_y = sp.expand(G[1] - sp.diff(g1, y))
    g2 = sp.integrate(rest_y, y)
    rest_z = sp.expand(G[2] - sp.diff(g1 + g2, z))
    g3 = sp.integrate(rest_z, z)
    fpot = sp.expand(g1 + g2 + g3)
    sol += (f'<p>The curl is $\\vec 0$, so $\\vec G$ <strong>is conservative</strong>. Build $f$ one variable at a time:</p><ul>'
            f'<li>$f=\\int\\left({L(G[0])}\\right)dx={L(g1)}+g(y,z)$.</li>'
            f'<li>$f_y={L(sp.diff(g1, y))}+g_y$ must equal ${L(G[1])}$, so $g_y={L(rest_y)}$ and $g={L(g2)}+h(z)$.</li>'
            f'<li>$f_z={L(sp.diff(g1 + g2, z))}+h\'(z)$ must equal ${L(G[2])}$, so $h\'(z)={L(rest_z)}$ and $h={L(g3)}$ (plus a constant).</li></ul>'
            f'\\[f(x,y,z)={L(fpot)}+K.\\]')
    return {'problem': problem, 'answer': f'<p>Conservative; $f={L(fpot)}+K$.</p>', 'solution': sol,
            'data': {'G': G, 'conservative': True, 'f': fpot}}


# ── surface integrals ────────────────────────────────────────────────
def chk_flux_plane(d):
    F = sp.Matrix(d['F'])
    a, b, c, A, B = d['a'], d['b'], d['c'], d['A'], d['B']
    # the same piece as a graph z = a x + b y + c over 0 <= x <= A, 0 <= y <= (B/A) x, upward normal <-a, -b, 1>
    integrand = fnum((F.T * sp.Matrix([-a, -b, 1]))[0].subs(z, a * x + b * y + c), x, y)
    val = mpmath.quad(lambda X: mpmath.quad(lambda Y: integrand(X, Y), [0, B * X / mpmath.mpf(A)]), [0, A])
    need(close(val, sp.N(d['flux'], 30), 1e-9), 'flux')
    need(d['normal'][2] > 0, 'normal has positive z-component')


@template(course=C, chapter='surface_integrals', id='m224-flux-plane',
          title='Flux through a parametrized piece of a plane',
          based_on={'exam': 'm324test4Spr1997_LeeA', 'problem': 4}, check=chk_flux_plane)
def flux_plane(rng):
    a, b, c = nz(rng, -3, 3), nz(rng, -3, 3), rng.randint(-2, 2)
    A, B = rng.choice([1, 2, 3]), rng.choice([1, 2, 3])
    pool = [x, y, z, sp.Integer(1), x * y, sp.Integer(2)]
    F = [nz(rng, -3, 4) * rng.choice(pool) for _ in range(3)]
    sigma = [u, v, a * u + b * v + c]
    su, sv = [sp.diff(q, u) for q in sigma], [sp.diff(q, v) for q in sigma]
    n = list(sp.Matrix(su).cross(sp.Matrix(sv)))
    Fs = [sp.expand(Fi.subs({x: sigma[0], y: sigma[1], z: sigma[2]})) for Fi in F]
    dot = sp.expand(sum(p * q for p, q in zip(Fs, n)))
    inner = sp.expand(sp.integrate(dot, (v, 0, sp.Rational(B, A) * u)))
    flux = sp.integrate(inner, (u, 0, A))
    problem = (f'<p>$\\sigma$ is the plane $\\vec r(u,v)={vtex(sigma)}$, with the normal whose $z$-component is positive. $T^*$ is the triangle in the $uv$-plane with vertices $(0,0)$, $({A},0)$ and $({A},{B})$, '
               f'and $T$ is the matching piece of the plane. Find the flux of $\\vec F={vtex(F)}$ across $T$.</p>')
    sol = (f'<p>$\\vec r_u={vtex(su)}$ and $\\vec r_v={vtex(sv)}$, so $\\vec r_u\\times\\vec r_v={vtex(n)}$, which has positive $z$-component, as required.</p>'
           f'<p>On the surface, $\\vec F(\\vec r(u,v))={vtex(Fs)}$, and $\\vec F\\cdot(\\vec r_u\\times\\vec r_v)={L(dot)}$.</p>'
           f'<p>$T^*$ is $0\\le u\\le{A}$, $0\\le v\\le{L(sp.Rational(B, A) * u)}$:</p>'
           f'\\[\\iint_T\\vec F\\cdot d\\vec S=\\int_0^{{{A}}}\\int_0^{{{L(sp.Rational(B, A) * u)}}}\\left({L(dot)}\\right)dv\\,du=\\int_0^{{{A}}}\\left({L(inner)}\\right)du={L(flux)}.\\]')
    return {'problem': problem, 'answer': f'${L(flux)}$', 'solution': sol,
            'data': {'F': F, 'a': a, 'b': b, 'c': c, 'A': A, 'B': B, 'flux': flux, 'normal': n}}


def chk_flux_para(d):
    F, h = sp.Matrix(d['F']), d['h']
    integrand = fnum((F.T * sp.Matrix([2 * x, 2 * y, 1]))[0].subs(z, h - x ** 2 - y ** 2), x, y)
    need(close(disk_quad(integrand, mpmath.sqrt(h)), sp.N(d['flux'], 30), 1e-8), 'flux in Cartesian coordinates')


@template(course=C, chapter='surface_integrals', id='m224-flux-paraboloid',
          title='Flux through a paraboloid', based_on={'style': 'Stewart §16.7'}, check=chk_flux_para)
def flux_paraboloid(rng):
    h = rng.choice([1, 4, 9])
    R = sp.sqrt(h)
    k = rng.choice([1, 2, 3])
    F = [k * c for c in rng.choice([[x, y, z], [0, 0, z], [x, y, 1], [y, -x, z], [x * z, y * z, 0], [0, 0, x ** 2 + y ** 2]])]
    F = [sp.sympify(c) for c in F]
    zf = h - x ** 2 - y ** 2
    dot = sp.expand((sp.Matrix(F).T * sp.Matrix([2 * x, 2 * y, 1]))[0].subs(z, zf))
    dotp = sp.simplify(dot.subs({x: r * sp.cos(th), y: r * sp.sin(th)}))
    flux = sp.simplify(sp.integrate(sp.integrate(sp.expand(dotp * r), (r, 0, R)), (th, 0, 2 * pi)))
    problem = f'<p>$S$ is the part of the paraboloid $z={h}-x^2-y^2$ above the $xy$-plane, oriented upward. Find the flux of $\\vec F={vtex(F)}$ through $S$.</p>'
    sol = (f'<p>For a graph $z=g(x,y)$ oriented upward, $d\\vec S=\\langle -g_x,-g_y,1\\rangle\\,dA=\\langle 2x,2y,1\\rangle\\,dA$. '
           f'$S$ lies over the disk $x^2+y^2\\le{h}$.</p>'
           f'<p>On $S$: $\\vec F\\cdot\\langle 2x,2y,1\\rangle={L(dot)}$, which in polar coordinates is ${L(dotp)}$.</p>'
           f'\\[\\iint_S\\vec F\\cdot d\\vec S=\\int_0^{{2\\pi}}\\int_0^{{{L(R)}}}\\left({L(dotp)}\\right)r\\,dr\\,d\\theta={L(flux)}.\\]')
    return {'problem': problem, 'answer': f'${L(flux)}$', 'solution': sol, 'data': {'F': F, 'h': h, 'flux': flux}}


# ── Stokes and divergence theorems ───────────────────────────────────
def chk_divthm(d):
    Fn = [fnum(c, x, y, z) for c in d['F']]
    if d['kind'] == 'box':
        dims = d['dims']
        tot = 0
        for i in range(3):
            o = [j for j in range(3) if j != i]
            for val, sgn in ((dims[i], 1), (0, -1)):
                def g(p, q, i=i, o=o, val=val):
                    pt = [0, 0, 0]
                    pt[i], pt[o[0]], pt[o[1]] = val, p, q
                    return Fn[i](*pt)
                tot += sgn * mpmath.quad(g, [0, dims[o[0]]], [0, dims[o[1]]])
    else:
        R, H = d['dims']
        top = disk_quad(lambda X, Y: Fn[2](X, Y, H), R)
        bot = -disk_quad(lambda X, Y: Fn[2](X, Y, 0), R)
        side = mpmath.quad(lambda T, Z: (Fn[0](R * mpmath.cos(T), R * mpmath.sin(T), Z) * mpmath.cos(T) +
                                         Fn[1](R * mpmath.cos(T), R * mpmath.sin(T), Z) * mpmath.sin(T)) * R, [0, 2 * mpmath.pi], [0, H])
        tot = top + bot + side
    need(close(tot, sp.N(d['flux'], 30), 1e-8), 'flux computed face by face')


@template(course=C, chapter='stokes_and_divergence_theorems', id='m224-divergence-theorem',
          title='Outward flux with the divergence theorem',
          based_on={'exam': 'm324finalSpr1997_LeeA', 'problem': 3}, check=chk_divthm)
def divergence_thm(rng):
    pool = [x, y, z, x * y, y * z, x * z, x ** 2, y ** 2, z ** 2, x ** 3, z ** 3, sp.Integer(1)]
    F = [nz(rng, -3, 3) * rng.choice(pool) for _ in range(3)]
    div = sp.expand(sum(sp.diff(Fi, w) for Fi, w in zip(F, (x, y, z))))
    if div == 0:
        raise Reject
    if rng.random() < 0.5:
        a, b, c = rng.choice([1, 2, 3]), rng.choice([1, 2]), rng.choice([1, 2, 3])
        flux = sp.integrate(div, (x, 0, a), (y, 0, b), (z, 0, c))
        region = f'the box $0\\le x\\le{a}$, $0\\le y\\le{b}$, $0\\le z\\le{c}$'
        setup = f'\\int_0^{{{a}}}\\int_0^{{{b}}}\\int_0^{{{c}}}\\left({L(div)}\\right)dz\\,dy\\,dx'
        data = {'kind': 'box', 'dims': (a, b, c)}
    else:
        R, H = rng.choice([1, 2, 3]), rng.choice([1, 2, 3])
        dc = sp.expand(div.subs({x: r * sp.cos(th), y: r * sp.sin(th)}))
        flux = sp.simplify(sp.integrate(sp.integrate(sp.integrate(dc * r, (z, 0, H)), (r, 0, R)), (th, 0, 2 * pi)))
        region = f'the solid cylinder $x^2+y^2\\le{R * R}$, $0\\le z\\le{H}$'
        setup = f'\\int_0^{{2\\pi}}\\int_0^{{{R}}}\\int_0^{{{H}}}\\left({L(dc)}\\right)r\\,dz\\,dr\\,d\\theta'
        data = {'kind': 'cyl', 'dims': (R, H)}
    problem = f'<p>$E$ is {region}, and $S$ is its boundary with the outward orientation. Use the divergence theorem to find the flux of $\\vec F={vtex(F)}$ out of $S$.</p>'
    sol = (f'<p>The divergence theorem turns the flux through the closed surface into a triple integral: $\\iint_S\\vec F\\cdot d\\vec S=\\iiint_E\\nabla\\cdot\\vec F\\,dV$.</p>'
           f'<p>$\\nabla\\cdot\\vec F={L(div)}$.</p>\\[\\iiint_E\\nabla\\cdot\\vec F\\,dV={setup}={L(flux)}.\\]')
    return {'problem': problem, 'answer': f'${L(flux)}$', 'solution': sol, 'data': {'F': F, 'flux': flux, **data}}


def chk_stokes(d):
    F, A, B, Cc = d['F'], d['A'], d['B'], d['C']
    val = seg_integral(F, A, B) + seg_integral(F, B, Cc) + seg_integral(F, Cc, A)
    need(close(val, sp.N(d['W'], 30), 1e-10), 'circulation computed directly')


@template(course=C, chapter='stokes_and_divergence_theorems', id='m224-stokes-theorem',
          title="Circulation around a triangle with Stokes' theorem",
          based_on={'exam': 'm324finalSpr1997_LeeA', 'problem': 2}, check=chk_stokes)
def stokes(rng):
    a, b, c = rng.choice([1, 2, 3]), rng.choice([1, 2, 3]), rng.choice([1, 2, 3])
    k = [rng.randint(-3, 3) for _ in range(3)]
    if k == [0, 0, 0]:
        raise Reject
    # F = (1/2) k × r + ∇φ has constant curl k; the gradient part adds nothing around a closed curve
    phi = nz(rng, -2, 2) * rng.choice([x * y * z, x ** 2 * z, y ** 2, sp.exp(x) * y, z ** 3])
    rot = list(sp.Matrix(k).cross(sp.Matrix([x, y, z])) / 2)
    F = [sp.expand(rot[i] + sp.diff(phi, w)) for i, w in enumerate((x, y, z))]
    curl = [sp.expand(cc) for cc in (sp.diff(F[2], y) - sp.diff(F[1], z), sp.diff(F[0], z) - sp.diff(F[2], x), sp.diff(F[1], x) - sp.diff(F[0], y))]
    A, B, Cc = [a, 0, 0], [0, b, 0], [0, 0, c]
    nvec = list((sp.Matrix(B) - sp.Matrix(A)).cross(sp.Matrix(Cc) - sp.Matrix(A)))
    W = sp.Rational(1, 2) * sum(ki * ni for ki, ni in zip(curl, nvec))
    problem = (f'<p>$C$ is the triangle with vertices $A({a},0,0)$, $B(0,{b},0)$, $C(0,0,{c})$, traversed $A\\to B\\to C\\to A$. '
               f'Use Stokes\' theorem to find $\\displaystyle\\oint_C\\vec F\\cdot d\\vec r$ for</p>\\[\\vec F={vtex(F)}.\\]')
    sol = (f'<p>Stokes\' theorem: $\\oint_C\\vec F\\cdot d\\vec r=\\iint_T(\\nabla\\times\\vec F)\\cdot d\\vec S$, where $T$ is the flat triangle bounded by $C$, oriented by the right-hand rule.</p>'
           f'<p>Curl: $\\nabla\\times\\vec F={vtex(curl)}$, a constant vector.</p>'
           f'<p>For a flat triangle, $\\iint_T d\\vec S$ is the vector area $\\frac12\\overrightarrow{{AB}}\\times\\overrightarrow{{AC}}$. Here $\\overrightarrow{{AB}}={vtex([-a, b, 0])}$ and '
           f'$\\overrightarrow{{AC}}={vtex([-a, 0, c])}$, so $\\overrightarrow{{AB}}\\times\\overrightarrow{{AC}}={vtex(nvec)}$, which points away from the origin: by the right-hand rule that matches going $A\\to B\\to C$.</p>'
           f'\\[\\oint_C\\vec F\\cdot d\\vec r={vtex(curl)}\\cdot\\frac12{vtex(nvec)}={L(W)}.\\]')
    return {'problem': problem, 'answer': f'${L(W)}$', 'solution': sol, 'data': {'F': F, 'A': A, 'B': B, 'C': Cc, 'W': W}}

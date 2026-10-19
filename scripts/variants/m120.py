"""Math 120 (Precalculus) practice-problem templates. See common.py for the contract.

UW Math 120 problems are mostly word problems with a fixed story; these keep the
story and change the numbers. Checks redo each answer independently (the
geometry another way, numerical sampling, or substitution back into the data).
"""
import math
import sympy as sp

from common import template, Reject, need, close, nz

C = 'Math 120'
x, t = sp.symbols('x t', real=True)


def L(e):
    return sp.latex(e, ln_notation=True)


def r2(v):
    return f'{float(v):,.2f}'


# ── angles ───────────────────────────────────────────────────────────
def chk_two_angles(d):
    a, b, D, h = (d[k] for k in ('a', 'b', 'D', 'h'))
    d1 = h / math.tan(math.radians(a))
    need(close(math.tan(math.radians(b)) * (d1 + D), h, 1e-10), 'the far angle sees the same height')


@template(course=C, chapter='angles', id='m120-height-two-angles',
          title='Height of a building from two angles of elevation',
          based_on={'exam': 'm120finalAut2006', 'problem': 5}, check=chk_two_angles)
def height_two_angles(rng):
    a = rng.choice([38, 42, 45, 50, 55, 60, 64, 70, 73])
    b = rng.choice([q for q in (25, 30, 34, 36, 40, 44) if q < a - 3])
    D = rng.choice([50, 80, 100, 120, 150, 200])
    ta, tb = math.tan(math.radians(a)), math.tan(math.radians(b))
    d1 = D * tb / (ta - tb)
    h = d1 * ta
    thing = rng.choice(['building', 'tower', 'tree', 'cliff'])
    problem = (f'<p>From a point on level ground, the angle of elevation to the top of a {thing} is ${a}^\\circ$. '
               f'After walking ${D}$ ft directly away from it, the angle of elevation is ${b}^\\circ$. How tall is the {thing}?</p>')
    sol = (f'<p>Let $h$ be the height and $d$ the first distance. Two right triangles give</p>'
           f'\\[h=d\\tan{a}^\\circ\\qquad\\text{{and}}\\qquad h=(d+{D})\\tan{b}^\\circ.\\]'
           f'<p>Set them equal: $d(\\tan{a}^\\circ-\\tan{b}^\\circ)={D}\\tan{b}^\\circ$, so</p>'
           f'\\[d=\\frac{{{D}\\tan{b}^\\circ}}{{\\tan{a}^\\circ-\\tan{b}^\\circ}}\\approx{d1:.2f}\\ \\text{{ft}},\\qquad h=d\\tan{a}^\\circ\\approx{h:.1f}\\ \\text{{ft}}.\\]')
    return {'problem': problem, 'answer': f'$h\\approx{h:.1f}$ ft', 'solution': sol, 'data': {'a': a, 'b': b, 'D': D, 'h': h}}


def chk_wiper(d):
    A, Lb, deg = d['A'], d['L'], d['deg']
    n = 4000          # integrate r dr dθ numerically (midpoint rule in r; the θ-integral is exact)
    rs = [A - Lb + Lb * (i + 0.5) / n for i in range(n)]
    area = math.radians(deg) * sum(r * Lb / n for r in rs)
    need(close(area, d['area'], 1e-6), 'swept area')


@template(course=C, chapter='angles', id='m120-swept-area',
          title='Area swept by a windshield wiper',
          based_on={'exam': 'm120mid2Aut2009', 'problem': 3}, check=chk_wiper)
def swept_area(rng):
    Lb, gap = rng.choice([12, 14, 16, 18, 20]), rng.choice([4, 6, 8])
    A = Lb + gap
    deg = rng.choice([90, 105, 110, 120, 135, 150])
    area = math.radians(deg) / 2 * (A * A - gap * gap)
    problem = (f'<p>A wiper blade ${Lb}$ inches long is mounted on a ${A}$-inch arm, so the blade runs from ${gap}$ to ${A}$ inches from the pivot. '
               f'The wiper turns through ${deg}^\\circ$. How much area does the blade sweep clean?</p>')
    sol = (f'<p>The swept region is the part of a ${deg}^\\circ$ sector of radius ${A}$ outside the sector of radius ${gap}$. '
           f'A sector of angle $\\theta$ (radians) and radius $r$ has area $\\frac12r^2\\theta$, and ${deg}^\\circ={L(sp.Rational(deg, 180) * sp.pi)}$ rad:</p>'
           f'\\[A=\\frac12\\left({A}^2-{gap}^2\\right)\\cdot{L(sp.Rational(deg, 180) * sp.pi)}={L(sp.Rational(deg, 360) * (A * A - gap * gap) * sp.pi)}\\approx{area:.1f}\\ \\text{{in}}^2.\\]')
    return {'problem': problem, 'answer': f'$\\approx{area:.1f}$ in²', 'solution': sol, 'data': {'A': A, 'L': Lb, 'deg': deg, 'area': area}}


# ── angular speed, circular motion ───────────────────────────────────
def chk_bike(d):
    chain = d['r1'] * 2 * math.pi * d['rpm']               # in/min of chain
    rear_rpm = chain / (2 * math.pi * d['r2'])
    wheel = rear_rpm * 2 * math.pi * d['R']                # in/min of road
    need(close(wheel * 60 / 63360, d['mph'], 1e-12), 'road speed in mph')


@template(course=C, chapter='angular_speed', id='m120-bicycle-sprockets',
          title='Linked sprockets: how fast does the bike go?',
          based_on={'exam': 'm120finalAut2006', 'problem': 2}, check=chk_bike)
def bicycle(rng):
    r1, r2, R = rng.choice([4, 5, 6, 8, 9]), rng.choice([1.5, 2, 2.5, 3, 4]), rng.choice([12, 13, 14, 15])
    if r2 >= r1:
        raise Reject
    rpm = rng.choice([40, 50, 60, 75, 80, 90])
    v_chain = r1 * 2 * math.pi * rpm
    w_rear = v_chain / r2
    v = R * w_rear
    mph = v * 60 / 63360
    problem = (f'<p>A cyclist pedals at ${rpm}$ revolutions per minute. The front sprocket has radius ${r1}$ in and the rear sprocket has radius ${r2:g}$ in; '
               f'the rear wheel (radius ${R}$ in) turns with the rear sprocket. How fast is the bicycle moving, in miles per hour? (1 mile = 63,360 in.)</p>')
    sol = (f'<p>The chain moves at the same linear speed around both sprockets. Front sprocket: ${rpm}$ rev/min $={2 * rpm}\\pi$ rad/min, so the chain speed is</p>'
           f'\\[v={r1}\\cdot{2 * rpm}\\pi={2 * rpm * r1}\\pi\\approx{v_chain:.1f}\\ \\text{{in/min}}.\\]'
           f'<p>Rear sprocket angular speed: $\\omega=\\frac{{v}}{{{r2:g}}}\\approx{w_rear:.1f}$ rad/min. The wheel turns at the same $\\omega$, so its rim moves at</p>'
           f'\\[{R}\\omega\\approx{v:,.1f}\\ \\text{{in/min}}=\\frac{{{v:,.1f}\\cdot60}}{{63{{,}}360}}\\approx{mph:.2f}\\ \\text{{mph}}.\\]')
    return {'problem': problem, 'answer': f'$\\approx{mph:.2f}$ mph', 'solution': sol, 'data': {'r1': r1, 'r2': r2, 'R': R, 'rpm': rpm, 'mph': mph}}


DIRS = {'east': 0, 'north': 90, 'west': 180, 'south': 270}


def chk_track(d):
    th = math.radians(d['start']) + d['sgn'] * d['v'] * d['T'] / d['R']
    need(close(d['R'] * math.cos(th), d['x'], 1e-9) and close(d['R'] * math.sin(th), d['y'], 1e-9), 'position on the circle')


@template(course=C, chapter='circular_motion', id='m120-runner-on-track',
          title='Where is a runner on a circular track?',
          based_on={'exam': 'm120mid2Spr2007_Conroy', 'problem': 3}, check=chk_track)
def runner(rng):
    R, v, T = rng.choice([40, 50, 60, 75, 100]), rng.choice([3, 4, 5, 6]), rng.choice([20, 32, 45, 60, 90])
    start = rng.choice(list(DIRS))
    ccw = rng.random() < 0.6
    sgn = 1 if ccw else -1
    s = v * T
    ang = s / R
    th = math.radians(DIRS[start]) + sgn * ang
    X, Y = R * math.cos(th), R * math.sin(th)
    problem = (f'<p>A runner starts at the {start}ernmost point of a circular track of radius ${R}$ m and runs {"counterclockwise" if ccw else "clockwise"} at ${v}$ m/s. '
               f'Put the center of the track at the origin, with east along the positive $x$-axis and north along the positive $y$-axis. Where is the runner after ${T}$ seconds?</p>')
    sol = (f'<p>In ${T}$ s the runner covers ${v}\\cdot{T}={s}$ m of arc, which is an angle of $\\frac{{{s}}}{{{R}}}={ang:.4f}$ rad.</p>'
           f'<p>The start is at angle ${L(sp.Rational(DIRS[start], 180) * sp.pi)}$ (measured counterclockwise from east), so the runner is now at angle '
           f'$\\theta={L(sp.Rational(DIRS[start], 180) * sp.pi)}{"+" if ccw else "-"}{ang:.4f}\\approx{th:.4f}$ rad:</p>'
           f'\\[(x,y)=\\left({R}\\cos\\theta,\\ {R}\\sin\\theta\\right)\\approx({X:.2f},\\ {Y:.2f}).\\]')
    return {'problem': problem, 'answer': f'$\\approx({X:.2f},\\ {Y:.2f})$', 'solution': sol,
            'data': {'R': R, 'v': v, 'T': T, 'start': DIRS[start], 'sgn': sgn, 'x': X, 'y': Y}}


# ── sinusoids ────────────────────────────────────────────────────────
def chk_sin(d):
    f = lambda s: d['mid'] + d['amp'] * math.cos(2 * math.pi / d['P'] * (s - d['t1']))
    need(close(f(d['t1']), d['M'], 1e-12) and close(f(d['t2']), d['m'], 1e-12), 'max and min')
    need(close(f(d['tq']), d['val'], 1e-9), 'value at the asked time')
    first = d['first']
    need(close(f(first), d['level'], 1e-9), 'reaches the level')
    need(all(f(d['t1'] + (first - d['t1']) * k / 400) > d['level'] - 1e-9 for k in range(400)), 'and not before')


@template(course=C, chapter='sinusoidal_modeling', id='m120-sinusoidal-model',
          title='Build a sinusoidal model from its maximum and minimum',
          based_on={'exam': 'm120finalAut2007', 'problem': 7}, check=chk_sin)
def sinusoid(rng):
    M = rng.choice([52, 70, 112, 35, 6, 2500])
    amp = rng.choice([10, 12, 25, 40]) if M > 50 else (rng.choice([2, 5]) if M < 10 else rng.choice([5, 10]))
    m = M - 2 * amp
    t1 = rng.choice([2, 3, 5, 8])
    half = rng.choice([5, 6, 7.5, 9, 12])
    t2 = t1 + half
    P = 2 * half
    mid = (M + m) / 2
    tq = t1 + rng.choice([1, 2, 3, half + 2, P - 1])
    val = mid + amp * math.cos(2 * math.pi / P * (tq - t1))
    level = mid + amp * rng.choice([0.5, 0, -0.3, 0.8])
    first = t1 + P / (2 * math.pi) * math.acos((level - mid) / amp)
    problem = (f'<p>A quantity varies sinusoidally with time $t$ (hours). It reaches a maximum of ${M}$ at $t={t1}$ and the next minimum, ${m}$, at $t={t2:g}$.</p>'
               f'<p>(a) Find a formula $f(t)$.<br>(b) Find $f({tq:g})$.<br>(c) After $t={t1}$, when does it first drop to ${level:g}$?</p>')
    sol = (f'<p><strong>(a)</strong> Half a period runs from the maximum to the minimum, so the period is $P=2({t2:g}-{t1})={P:g}$. '
           f'The midline is $\\frac{{{M}+({m})}}{{2}}={mid:g}$ and the amplitude is $\\frac{{{M}-({m})}}{{2}}={amp}$. A cosine starts at its maximum, so shift it to $t={t1}$:</p>'
           f'\\[f(t)={mid:g}+{amp}\\cos\\!\\left(\\frac{{2\\pi}}{{{P:g}}}(t-{t1})\\right).\\]'
           f'<p><strong>(b)</strong> $f({tq:g})={mid:g}+{amp}\\cos\\!\\left(\\frac{{2\\pi}}{{{P:g}}}\\cdot{tq - t1:g}\\right)\\approx{val:.2f}$.</p>'
           f'<p><strong>(c)</strong> Solve ${mid:g}+{amp}\\cos\\!\\left(\\frac{{2\\pi}}{{{P:g}}}(t-{t1})\\right)={level:g}$: $\\cos(\\cdot)={(level - mid) / amp:g}$. '
           f'Going down from the maximum the angle increases from $0$, so the first solution is $\\frac{{2\\pi}}{{{P:g}}}(t-{t1})=\\cos^{{-1}}({(level - mid) / amp:g})\\approx{math.acos((level - mid) / amp):.4f}$:</p>'
           f'\\[t={t1}+\\frac{{{P:g}}}{{2\\pi}}\\cos^{{-1}}({(level - mid) / amp:g})\\approx{first:.2f}.\\]')
    return {'problem': problem, 'answer': f'$f(t)={mid:g}+{amp}\\cos\\left(\\frac{{2\\pi}}{{{P:g}}}(t-{t1})\\right)$; $f({tq:g})\\approx{val:.2f}$; $t\\approx{first:.2f}$',
            'solution': sol, 'data': {'M': M, 'm': m, 't1': t1, 't2': t2, 'P': P, 'mid': mid, 'amp': amp, 'tq': tq, 'val': val, 'level': level, 'first': first}}


# ── circles ──────────────────────────────────────────────────────────
LATTICE = {5: [(3, 4), (4, 3), (5, 0), (0, 5)], 10: [(6, 8), (8, 6), (10, 0), (0, 10)], 13: [(5, 12), (12, 5), (13, 0)], 25: [(7, 24), (15, 20), (20, 15), (24, 7)]}


def chk_circle(d):
    R, (A, B) = d['R'], d['pts']
    for X, Y in (A, B):
        need(X * X + Y * Y == R * R, 'point on the circle')
    (x1, y1), (x2, y2) = d['P'], d['Q']
    for X, Y in (A, B):
        need((x2 - x1) * (Y - y1) == (y2 - y1) * (X - x1), 'point on the path')


@template(course=C, chapter='circles', id='m120-path-through-circle',
          title='Where a straight path enters and leaves a circle',
          based_on={'exam': 'm120finalWin2009', 'problem': 2}, check=chk_circle)
def path_circle(rng):
    R = rng.choice(list(LATTICE))
    base = LATTICE[R]
    p1, p2 = rng.sample(base, 2)
    p1 = (p1[0] * rng.choice([1, -1]), p1[1] * rng.choice([1, -1]))
    p2 = (p2[0] * rng.choice([1, -1]), p2[1] * rng.choice([1, -1]))
    if p1 == p2 or (p1[0] == -p2[0] and p1[1] == -p2[1]):
        raise Reject
    # start and end outside the circle on the same line
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    P = (p1[0] - dx, p1[1] - dy)
    Q = (p2[0] + dx, p2[1] + dy)
    if dx == 0:
        line = f'x={p1[0]}'
    else:
        m = sp.Rational(dy, dx)
        line = f'y={L(sp.expand(m * (x - p1[0]) + p1[1]))}'
    problem = (f'<p>A circular pond of radius ${R}$ m is centered at the origin. A straight path runs from $({P[0]},{P[1]})$ to $({Q[0]},{Q[1]})$. '
               'At which two points does the path cross the edge of the pond?</p>')
    yl = sp.expand(sp.Rational(dy, dx) * (x - p1[0]) + p1[1]) if dx else None
    quad_ = sp.expand(x ** 2 + yl ** 2 - R * R) if dx else None
    sol = ((f'<p>The path lies on the line through the two points: slope $\\frac{{{Q[1]}-({P[1]})}}{{{Q[0]}-({P[0]})}}={L(sp.Rational(dy, dx))}$, so ${line}$.</p>'
            f'<p>Substitute into $x^2+y^2={R * R}$:</p>\\[x^2+\\left({L(yl)}\\right)^2={R * R}\\quad\\Longrightarrow\\quad {L(quad_)}=0,\\]'
            f'<p>whose roots are $x={p1[0]}$ and $x={p2[0]}$.</p>') if dx else
           f'<p>The path is the vertical line $x={p1[0]}$. Then $y^2={R * R}-{p1[0] ** 2}={R * R - p1[0] ** 2}$, so $y=\\pm{abs(p1[1])}$.</p>')
    sol += f'<p>The path crosses the edge at $({p1[0]},{p1[1]})$ and $({p2[0]},{p2[1]})$.</p>'
    return {'problem': problem, 'answer': f'$({p1[0]},{p1[1]})$ and $({p2[0]},{p2[1]})$', 'solution': sol,
            'data': {'R': R, 'pts': (p1, p2), 'P': P, 'Q': Q}}


# ── quadratics ───────────────────────────────────────────────────────
def chk_wire(d):
    Lw, k = d['L'], d['k']                # k = area of the polygon per (piece length)^2
    A = lambda s: k * s * s + (Lw - s) ** 2 / (4 * math.pi)
    best = min((A(Lw * i / 200000), Lw * i / 200000) for i in range(200001))
    need(abs(best[1] - d['x']) < 1e-3 * Lw and close(best[0], d['A'], 1e-8), 'minimum by sampling')


@template(course=C, chapter='quadratics', id='m120-wire-square-circle',
          title='Cut a wire into a polygon and a circle to minimize total area',
          based_on={'exam': 'm120finalAut2008', 'problem': 7}, check=chk_wire)
def wire(rng):
    Lw = rng.choice([12, 16, 20, 24, 30, 36, 40, 48, 50, 60, 72, 80, 90, 100, 120])
    shape = rng.choice(['square', 'equilateral triangle'])
    if shape == 'square':
        k, ktex, side = 1 / 16, '\\frac{x^2}{16}', '\\frac x4'
    else:
        k, ktex, side = math.sqrt(3) / 36, '\\frac{\\sqrt3}{36}x^2', '\\frac x3'
    xs = (Lw / (2 * math.pi)) / (2 * (k + 1 / (4 * math.pi)))
    A = k * xs * xs + (Lw - xs) ** 2 / (4 * math.pi)
    poly_area = 'side$^2$' if shape == 'square' else '$\\frac{\\sqrt3}{4}$side$^2$'
    problem = (f'<p>A wire ${Lw}$ cm long is cut into two pieces. One piece is bent into a{"n" if shape[0] == "e" else ""} {shape} and the other into a circle. '
               'Where should the wire be cut to make the total enclosed area as small as possible? What is that area?</p>')
    sol = (f'<p>Let $x$ be the length used for the {shape}, so its side is ${side}$ and its area ({poly_area}) is ${ktex}$. The circle gets ${Lw}-x$, so its radius is $\\frac{{{Lw}-x}}{{2\\pi}}$. The total area is</p>'
           f'\\[A(x)={ktex}+\\pi\\left(\\frac{{{Lw}-x}}{{2\\pi}}\\right)^2={ktex}+\\frac{{({Lw}-x)^2}}{{4\\pi}},\\]'
           f'<p>a quadratic in $x$ that opens upward. Its vertex (where $A\'(x)=0$) is at</p>'
           f'\\[x=\\frac{{{Lw}/(2\\pi)}}{{2\\left({k:.6f}+\\frac1{{4\\pi}}\\right)}}\\approx{xs:.2f}\\ \\text{{cm}}.\\]'
           f'<p>So use about ${xs:.2f}$ cm for the {shape} and ${Lw - xs:.2f}$ cm for the circle. The minimum total area is $A\\approx{A:.2f}$ cm².</p>')
    return {'problem': problem, 'answer': f'{shape.capitalize()} gets $\\approx{xs:.2f}$ cm; minimum area $\\approx{A:.2f}$ cm²', 'solution': sol,
            'data': {'L': Lw, 'k': k, 'x': xs, 'A': A}}


# ── exponentials ─────────────────────────────────────────────────────
def chk_towns(d):
    A = lambda s: d['PA'] * (1 + d['rA']) ** s
    B = lambda s: d['PB'] * 2 ** (s / d['D'])
    need(close(A(d['t']), B(d['t']), 1e-9), 'populations are equal')
    need((A(d['t'] - 1) - B(d['t'] - 1)) * (A(d['t'] + 1) - B(d['t'] + 1)) < 0, 'they cross there')


@template(course=C, chapter='exponentials', id='m120-exponential-towns',
          title='When will two exponentially growing towns be the same size?',
          based_on={'exam': 'm120finalWin2008', 'problem': 2}, check=chk_towns)
def towns(rng):
    PA, PB = rng.choice([8000, 12000, 20000, 1325]), rng.choice([30000, 45000, 60000, 4000])
    rA = rng.choice([0.03, 0.045, 0.05, 0.06, 0.08])
    D = rng.choice([30, 40, 50, 60])
    gA, gB = math.log(1 + rA), math.log(2) / D
    if PB <= PA or gA <= gB:
        raise Reject
    tt = math.log(PB / PA) / (gA - gB)
    if tt > 200:
        raise Reject
    problem = (f'<p>Arden has ${PA:,}$ people and grows by ${rA * 100:g}\\%$ per year. Brookfield has ${PB:,}$ people and its population doubles every ${D}$ years. '
               'After how many years will the two towns have the same population?</p>')
    sol = (f'<p>With $t$ in years: $A(t)={PA:,}(1+{rA:g})^t$ and $B(t)={PB:,}\\cdot2^{{t/{D}}}$. Set them equal and take logarithms:</p>'
           f'\\[\\ln {PA}+t\\ln({1 + rA:g})=\\ln {PB}+\\frac{{t}}{{{D}}}\\ln2\\quad\\Longrightarrow\\quad t=\\frac{{\\ln({PB}/{PA})}}{{\\ln({1 + rA:g})-\\frac{{\\ln2}}{{{D}}}}}\\approx{tt:.2f}\\ \\text{{years}}.\\]')
    return {'problem': problem, 'answer': f'$t\\approx{tt:.2f}$ years', 'solution': sol, 'data': {'PA': PA, 'PB': PB, 'rA': rA, 'D': D, 't': tt}}


# ── composition, functions ───────────────────────────────────────────
def chk_comp(d):
    f, g, K = d['f'], d['g'], d['K']
    h = sp.lambdify(x, f.subs(x, g), 'math')
    for s in d['sols']:
        need(close(h(float(s)), K, 1e-12), 'solution works')
    grid = [-50 + i * 0.001 for i in range(100001)]
    sign_changes = sum(1 for a, b in zip(grid, grid[1:]) if (h(a) - K) * (h(b) - K) < 0 or h(a) == K)
    need(sign_changes == len(d['sols']), 'no other solutions')


@template(course=C, chapter='composition', id='m120-composition-absolute-value',
          title='Solve an equation involving a composition with an absolute value',
          based_on={'exam': 'm120finalWin2009', 'problem': 7}, check=chk_comp)
def composition(rng):
    c, dd = rng.choice([2, 3]), rng.randint(-3, 3)
    f = x + c * sp.Abs(x - dd)
    a, b = nz(rng, -3, 3), rng.randint(-4, 4)
    g = a * x + b
    K = rng.randint(dd + 1, dd + 12)
    h = f.subs(x, g)
    brk = sp.Rational(dd - b, a)
    # on each side of the break, f(g(x)) is linear
    right = sp.expand(g + c * (g - dd))     # where g >= dd
    left = sp.expand(g - c * (g - dd))      # where g < dd
    sols = []
    for piece, cond in ((right, lambda s: g.subs(x, s) >= dd), (left, lambda s: g.subs(x, s) < dd)):
        r = sp.solve(sp.Eq(piece, K), x)
        sols += [s for s in r if cond(s)]
    sols = sorted(set(sols))
    if not sols:
        raise Reject
    side = 'x\\ge' if a > 0 else 'x\\le'
    other = 'x<' if a > 0 else 'x>'
    problem = f'<p>Let $f(x)={L(f)}$ and $g(x)={L(g)}$. Find a formula for $f(g(x))$ without absolute values, and solve $f(g(x))={K}$.</p>'
    sol = (f'<p>$f(g(x))=({L(g)})+{c}\\left|{L(g - dd)}\\right|$. The absolute value switches where ${L(g - dd)}=0$, at $x={L(brk)}$.</p>'
           f'\\[f(g(x))=\\begin{{cases}}{L(right)}, & {side} {L(brk)}\\\\ {L(left)}, & {other} {L(brk)}\\end{{cases}}\\]'
           f'<p>Solve ${K}$ on each piece and keep only solutions in that piece\'s range:</p><ul>'
           f'<li>${L(right)}={K}$ gives $x={L(sp.solve(sp.Eq(right, K), x)[0]) if sp.solve(sp.Eq(right, K), x) else "(none)"}$'
           f'{" (valid)" if any(s in sols for s in sp.solve(sp.Eq(right, K), x)) else " (not in this range, so rejected)"}.</li>'
           f'<li>${L(left)}={K}$ gives $x={L(sp.solve(sp.Eq(left, K), x)[0]) if sp.solve(sp.Eq(left, K), x) else "(none)"}$'
           f'{" (valid)" if any(s in sols for s in sp.solve(sp.Eq(left, K), x)) else " (not in this range, so rejected)"}.</li></ul>'
           f'<p>Solutions: {", ".join(f"$x={L(s)}$" for s in sols)}.</p>')
    return {'problem': problem, 'answer': ', '.join(f'$x={L(s)}$' for s in sols), 'solution': sol, 'data': {'f': f, 'g': g, 'K': K, 'sols': sols}}


def chk_ff(d):
    a, b = d['a'], d['b']
    need(sp.expand((a * (a * x + b) + b) - (d['p'] * x + d['q'])) == 0, 'f(f(x)) matches')
    need(sp.expand(((x - b) / a).subs(x, a * x + b) - x) == 0, 'inverse')


@template(course=C, chapter='functions', id='m120-composition-find-constant',
          title='Find a linear function from f(f(x)), and its inverse',
          based_on={'exam': 'm120mid2Aut2008', 'problem': 2}, check=chk_ff)
def find_constant(rng):
    a, b = rng.choice([-3, -2, 2, 3, 4, -4]), nz(rng, -6, 6)
    p, q = a * a, a * b + b
    if q == 0:
        raise Reject
    problem = f'<p>Let $f(x)=ax{"+" if b > 0 else "-"}{abs(b)}$ and suppose $f(f(x))={L(p * x + q)}$.</p><p>(a) Find $a$.<br>(b) Find $f^{{-1}}(x)$.</p>'
    roots = [sp.sqrt(p), -sp.sqrt(p)]
    sol = (f'<p><strong>(a)</strong> $f(f(x))=a\\left(ax{"+" if b > 0 else "-"}{abs(b)}\\right){"+" if b > 0 else "-"}{abs(b)}=a^2x+{b}a{"+" if b > 0 else "-"}{abs(b)}$. Matching coefficients with ${L(p * x + q)}$:</p>'
           f'\\[a^2={p}\\qquad\\text{{and}}\\qquad {b}a{"+" if b > 0 else "-"}{abs(b)}={q}.\\]'.replace('+-', '-')
           + f'<p>The first gives $a=\\pm{int(roots[0])}$; the second gives $a=\\frac{{{q}-({b})}}{{{b}}}={a}$. So $a={a}$.</p>'
           f'<p><strong>(b)</strong> Solve $y={a}x{"+" if b > 0 else "-"}{abs(b)}$ for $x$: $x=\\frac{{y{"-" if b > 0 else "+"}{abs(b)}}}{{{a}}}$, so</p>'
           f'\\[f^{{-1}}(x)={L((x - b) / a)}.\\]')
    return {'problem': problem, 'answer': f'$a={a}$; $f^{{-1}}(x)={L((x - b) / a)}$', 'solution': sol, 'data': {'a': a, 'b': b, 'p': p, 'q': q}}


# ── rational functions, linear models, rates ────────────────────────
def chk_rational(d):
    a, b, c = d['abc']
    H = (a * x + b) / (c * x + 1)
    for X, Y in d['pts']:
        need(H.subs(x, X) == Y, 'passes through the data')
    need(sp.limit(H, x, sp.oo) == d['asym'], 'long-run value')


@template(course=C, chapter='rational_functions', id='m120-linear-to-linear',
          title='Fit a linear-to-linear function to three data points',
          based_on={'exam': 'm120finalAut2008', 'problem': 2}, check=chk_rational)
def linear_to_linear(rng):
    c = rng.choice([sp.Rational(1, 2), sp.Rational(1, 4), sp.Rational(1, 5), sp.Rational(1, 10), sp.Integer(1)])
    b = rng.choice([4, 10, 20, 21, 30])
    a = rng.choice([q for q in (40, 60, 90, 100, 120) if sp.Rational(q) / c > b]) * c
    H = (a * x + b) / (c * x + 1)
    xs = [0] + rng.sample([1, 2, 3, 4, 5, 6, 8, 10], 2)
    xs = sorted(xs)
    pts = [(X, H.subs(x, X)) for X in xs]
    if any(sp.fraction(Y)[1] > 20 for _, Y in pts):
        raise Reject
    A_, B_, C_ = sp.symbols('a b c')
    eqs = [sp.Eq(A_ * X + B_, Y * (C_ * X + 1)) for X, Y in pts]
    problem = (f'<p>A quantity is modeled by $H(x)=\\dfrac{{ax+b}}{{cx+1}}$. It is ${L(pts[0][1])}$ at $x={xs[0]}$, ${L(pts[1][1])}$ at $x={xs[1]}$ and ${L(pts[2][1])}$ at $x={xs[2]}$.</p>'
               '<p>(a) Find $a$, $b$ and $c$.<br>(b) What value does $H$ approach in the long run?</p>')
    sol = (f'<p><strong>(a)</strong> $H(0)=b$, so $b={b}$. Clear the denominator, $ax+b=H(x)(cx+1)$, at the other two points:</p>'
           f'\\[{L(eqs[1].lhs.subs(B_, b))}={L(eqs[1].rhs)},\\qquad {L(eqs[2].lhs.subs(B_, b))}={L(eqs[2].rhs)}.\\]'
           f'<p>Solving these two linear equations gives $a={L(a)}$ and $c={L(c)}$. So $H(x)=\\dfrac{{{L(a * x + b)}}}{{{L(c * x + 1)}}}$.</p>'
           f'<p><strong>(b)</strong> For large $x$, $H(x)\\approx\\frac{{ax}}{{cx}}=\\frac{{a}}{{c}}={L(a / c)}$.</p>')
    return {'problem': problem, 'answer': f'$a={L(a)}$, $b={b}$, $c={L(c)}$; $H\\to{L(a / c)}$', 'solution': sol,
            'data': {'abc': (a, b, c), 'pts': pts, 'asym': a / c}}


def chk_lines(d):
    (t1, u1), (t2, u2) = d['A']
    (s1, v1), (s2, v2) = d['B']
    lerp = lambda p, q, s: p[1] + (q[1] - p[1]) * (s - p[0]) / (q[0] - p[0])
    need(close(lerp((t1, u1), (t2, u2), float(d['t'])), lerp((s1, v1), (s2, v2), float(d['t'])), 1e-12), 'equal at the answer')
    need(close(lerp((t1, u1), (t2, u2), float(d['t'])), float(d['val']), 1e-12), 'the common value')


@template(course=C, chapter='linear_models', id='m120-two-linear-models',
          title='Two linear models: when are they equal?',
          based_on={'exam': 'm120finalAut2007', 'problem': 1}, check=chk_lines)
def two_lines(rng):
    m1, b1 = rng.choice([sp.Rational(3, 4), 2, sp.Rational(5, 2), 3]), rng.randint(5, 20)
    m2, b2 = rng.choice([sp.Rational(1, 2), -1, sp.Rational(-3, 2), 1]), rng.randint(20, 40)
    if m1 == m2:
        raise Reject
    tA = sorted(rng.sample(range(0, 8), 2))
    tB = sorted(rng.sample(range(0, 8), 2))
    A = [(s, m1 * s + b1) for s in tA]
    B = [(s, m2 * s + b2) for s in tB]
    tt = sp.Rational(b2 - b1) / (m1 - m2)
    if tt <= 0:
        raise Reject
    val = m1 * tt + b1
    problem = (f'<p>The price of item A grows linearly: ${L(A[0][1])}$ dollars in year ${A[0][0]}$ and ${L(A[1][1])}$ dollars in year ${A[1][0]}$. '
               f'Item B also changes linearly: ${L(B[0][1])}$ dollars in year ${B[0][0]}$ and ${L(B[1][1])}$ dollars in year ${B[1][0]}$. '
               'In what year are the prices equal, and what is the price then?</p>')
    sol = (f'<p>A: slope $\\frac{{{L(A[1][1])}-{L(A[0][1])}}}{{{A[1][0]}-{A[0][0]}}}={L(m1)}$, so $P_A(t)={L(m1 * t + b1)}$. '
           f'B: slope $\\frac{{{L(B[1][1])}-{L(B[0][1])}}}{{{B[1][0]}-{B[0][0]}}}={L(m2)}$, so $P_B(t)={L(m2 * t + b2)}$.</p>'
           f'\\[{L(m1 * t + b1)}={L(m2 * t + b2)}\\quad\\Longrightarrow\\quad t=\\frac{{{b2}-{b1}}}{{{L(m1)}-\\left({L(m2)}\\right)}}={L(tt)}{"" if tt.is_Integer else f"\\approx{float(tt):.2f}"}.\\]'
           f'<p>The common price is $P_A({L(tt)})={L(val)}{"" if val.is_Integer else f"\\approx{float(val):.2f}"}$ dollars.</p>')
    return {'problem': problem, 'answer': f'$t={L(tt)}$, price ${L(val)}$', 'solution': sol,
            'data': {'A': A, 'B': B, 't': tt, 'val': val}}


def chk_closest(d):
    ax, ay, vax, vay, bx, by, vbx, vby, T = d['p']
    dist = lambda s: math.hypot(ax + vax * s - bx - vbx * s, ay + vay * s - by - vby * s)
    best = min((dist(T * i / 200000), T * i / 200000) for i in range(200001))
    need(abs(best[1] - d['t']) < 1e-3 and close(best[0], d['dmin'], 1e-8), 'closest approach by sampling')


@template(course=C, chapter='rates', id='m120-closest-approach',
          title='Two people walking in straight lines: when are they closest?',
          based_on={'exam': 'm120finalWin2009', 'problem': 5}, check=chk_closest)
def closest(rng):
    A0 = (rng.randint(-10, 0), rng.randint(0, 10))
    A1 = (rng.randint(5, 15), rng.randint(-5, 5))
    TA = rng.choice([4, 5, 8, 10])
    B0 = (rng.randint(0, 10), rng.randint(-12, -4))
    B1 = (rng.randint(-5, 5), rng.randint(5, 15))
    TB = rng.choice([4, 5, 8, 10])
    va = ((A1[0] - A0[0]) / TA, (A1[1] - A0[1]) / TA)
    vb = ((B1[0] - B0[0]) / TB, (B1[1] - B0[1]) / TB)
    dx0, dy0 = A0[0] - B0[0], A0[1] - B0[1]
    dvx, dvy = va[0] - vb[0], va[1] - vb[1]
    aa = dvx ** 2 + dvy ** 2
    if aa == 0:
        raise Reject
    tt = -(dx0 * dvx + dy0 * dvy) / aa
    T = min(TA, TB)
    if not 0.3 < tt < T - 0.3:
        raise Reject
    dmin = math.hypot(dx0 + dvx * tt, dy0 + dvy * tt)
    bb = 2 * (dx0 * dvx + dy0 * dvy)
    cc = dx0 ** 2 + dy0 ** 2
    problem = (f'<p>At $t=0$ Ann starts at $({A0[0]},{A0[1]})$ and walks in a straight line at constant speed, reaching $({A1[0]},{A1[1]})$ at $t={TA}$ s. '
               f'At the same moment Ben starts at $({B0[0]},{B0[1]})$ and walks straight to $({B1[0]},{B1[1]})$, arriving at $t={TB}$ s. (Units: meters.)</p>'
               f'<p>When are they closest together (during the first ${T}$ s), and how close do they get?</p>')
    sol = (f'<p>Ann: $x={A0[0]}{va[0]:+g}t$, $y={A0[1]}{va[1]:+g}t$. Ben: $x={B0[0]}{vb[0]:+g}t$, $y={B0[1]}{vb[1]:+g}t$.</p>'
           f'<p>The vector from Ben to Ann is $\\langle {dx0}{dvx:+g}t,\\ {dy0}{dvy:+g}t\\rangle$, so the squared distance is</p>'
           f'\\[D(t)^2=({dx0}{dvx:+g}t)^2+({dy0}{dvy:+g}t)^2={aa:g}t^2{bb:+g}t+{cc:g},\\]'
           f'<p>a quadratic opening upward. Its vertex is at $t=-\\dfrac{{{bb:g}}}{{2({aa:g})}}\\approx{tt:.3f}$ s, which is within $[0,{T}]$. There</p>'
           f'\\[D=\\sqrt{{D(t)^2}}\\approx{dmin:.3f}\\ \\text{{m}}.\\]')
    return {'problem': problem, 'answer': f'$t\\approx{tt:.3f}$ s, distance $\\approx{dmin:.3f}$ m', 'solution': sol,
            'data': {'p': (A0[0], A0[1], va[0], va[1], B0[0], B0[1], vb[0], vb[1], T), 't': tt, 'dmin': dmin}}

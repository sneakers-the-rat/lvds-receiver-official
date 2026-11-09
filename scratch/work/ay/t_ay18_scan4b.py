import sys, json, math
import numpy as np
sys.path.insert(0, 'scratch/work/ax')

src = open('scratch/work/ax/t_ax252_design214ae.py').read()
head = src.split("\nbox = (64.0")[0]
exec(head)

D = json.load(open('scratch/work/ax/design214_ax252.json'))
for J in D['stp_legs']:
    add_items(journey_items_dense(J, 'ULPI_STP', hw=0.10))
add_items({0: [('seg', 'ULPI_STP', (76.25, 16.95, 76.05, 18.0, 0.1), 0.2),
               ('via', 'ULPI_STP', (76.065, 17.99, 0.25), 0.2)]})
c22old = [it for it in pool[0] if it[0] == 'pad' and it[1] in ('PHY_1V8', 'GND')
          and abs(it[2][1] - 18.6) < 0.01 and it[2][0] in (79.12, 80.08)]
rip_items(c22old)
print('ripped prep C22 pads:', len(c22old), flush=True)

# ---- numpy conservative margin field over candidate centres ----
RX0, RX1, RY0, RY1 = 78.2, 85.0, 5.5, 14.5
step = 0.1
xs = np.arange(RX0, RX1 + 1e-9, step)
ys = np.arange(RY0, RY1 + 1e-9, step)
GX, GY = np.meshgrid(xs, ys)
HALF_DIAG = math.hypot(0.28, 0.31)


def df_grid(it, PX, PY):
    kind, d = it[0], it[2]
    if kind == 'pad':
        cx, cy, hw, hh, rot = d
        dx, dy = PX - cx, PY - cy
        c, s = math.cos(-rot), math.sin(-rot)
        lx, ly = dx * c - dy * s, dx * s + dy * c
        return np.hypot(np.maximum(np.abs(lx) - hw, 0.0),
                        np.maximum(np.abs(ly) - hh, 0.0))
    if kind == 'seg':
        x1, y1, x2, y2, hw = d
        px, py = PX - x1, PY - y1
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else np.clip((px * dx + py * dy) / L2, 0, 1)
        return np.hypot(px - t * dx, py - t * dy) - hw
    return np.hypot(PX - d[0], PY - d[1]) - d[2]


# items that can fence the region (bbox within 1.2 of it)
items = []
for it in pool[0]:
    kind, d = it[0], it[2]
    if kind == 'pad':
        cx, cy = d[0], d[1]
        if RX0 - 1.2 < cx < RX1 + 1.2 and RY0 - 1.2 < cy < RY1 + 1.2:
            items.append(it)
    elif kind == 'seg':
        if max(d[0], d[2]) >= RX0 - 1.2 and min(d[0], d[2]) <= RX1 + 1.2 \
           and max(d[1], d[3]) >= RY0 - 1.2 and min(d[1], d[3]) <= RY1 + 1.2:
            items.append(it)
    else:
        if RX0 - 1.2 < d[0] < RX1 + 1.2 and RY0 - 1.2 < d[1] < RY1 + 1.2:
            items.append(it)
print('region F items:', len(items), flush=True)

fields = {}
for rot, offs in ((0, ((-0.48, 0.0), (0.48, 0.0))),
                  (90, ((0.0, -0.48), (0.0, 0.48)))):
    fmin = np.full(GX.shape, 9.9)
    for (ox, oy), net in zip(offs, ('PHY_1V8', 'GND')):
        PX, PY = GX + ox, GY + oy
        f = np.full(GX.shape, 9.9)
        for it in items:
            if it[1] == net:
                continue  # same-net copper does not fence its own pad
            req = max(0.2, it[3])
            f = np.minimum(f, df_grid(it, PX, PY) - req - HALF_DIAG)
        fmin = np.minimum(fmin, f)
    fields[rot] = fmin
short = []
for rot in (0, 90):
    f = fields[rot]
    idx = np.argwhere(f >= 0.03)
    for (j, i) in idx:
        cx, cy = float(xs[i]), float(ys[j])
        short.append((float(f[j, i]), cx, cy, rot))
short.sort(reverse=True)
print('shortlist (bound margin >= +0.03):', len(short), flush=True)
for s in short[:15]:
    print('   ', s, flush=True)


# ---- exact pad margin for the shortlist ----
def rect_seg_dist(cx, cy, hw, hh, d):
    x1, y1, x2, y2, shw = d
    # endpoints to rect
    def pt_rect(px, py):
        return math.hypot(max(abs(px - cx) - hw, 0.0),
                          max(abs(py - cy) - hh, 0.0))
    best = min(pt_rect(x1, y1), pt_rect(x2, y2))
    # rect corners to segment
    dx, dy = x2 - x1, y2 - y1
    L2 = dx * dx + dy * dy
    for (px, py) in ((cx - hw, cy - hh), (cx - hw, cy + hh),
                     (cx + hw, cy - hh), (cx + hw, cy + hh)):
        t = 0.0 if L2 == 0 else max(0.0, min(1.0,
                                    ((px - x1) * dx + (py - y1) * dy) / L2))
        best = min(best, math.hypot(px - (x1 + t * dx), py - (y1 + t * dy)))
    # intersection test: segment endpoints inside rect or crossing edges
    def inside(px, py):
        return abs(px - cx) <= hw and abs(py - cy) <= hh
    if inside(x1, y1) or inside(x2, y2):
        return 0.0
    # segment vs each rect edge (proper intersection)
    def seg_int(a, b, c, d2):
        def cross(o, p, q):
            return (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0])
        d1 = cross(c, d2, a)
        d2v = cross(c, d2, b)
        d3 = cross(a, b, c)
        d4 = cross(a, b, d2)
        return ((d1 > 0) != (d2v > 0)) and ((d3 > 0) != (d4 > 0))
    S = (x1, y1)
    E = (x2, y2)
    for e1, e2 in (((cx - hw, cy - hh), (cx + hw, cy - hh)),
                   ((cx + hw, cy - hh), (cx + hw, cy + hh)),
                   ((cx + hw, cy + hh), (cx - hw, cy + hh)),
                   ((cx - hw, cy + hh), (cx - hw, cy - hh))):
        if seg_int(S, E, e1, e2):
            return 0.0
    return best - shw


def pad_margin_exact(cx, cy, net):
    best, who = 9.9, None
    for it in items:
        if it[1] == net:
            continue
        kind, d = it[0], it[2]
        if kind == 'pad':
            dx = max(abs(d[0] - cx) - (0.28 + d[2]), 0.0)
            dy = max(abs(d[1] - cy) - (0.31 + d[3]), 0.0)
            dist = math.hypot(dx, dy)
        elif kind == 'seg':
            dist = rect_seg_dist(cx, cy, 0.28, 0.31, d)
        else:
            dist = math.hypot(max(abs(d[0] - cx) - 0.28, 0.0),
                              max(abs(d[1] - cy) - 0.31, 0.0)) - d[2]
        m = dist - max(0.2, it[3])
        if m < best:
            best, who = m, it
    return best, who


exact = []
for (_, cx, cy, rot) in short:
    offs = ((-0.48, 0.0), (0.48, 0.0)) if rot == 0 else ((0.0, -0.48),
                                                         (0.0, 0.48))
    m1, w1 = pad_margin_exact(cx + offs[0][0], cy + offs[0][1], 'PHY_1V8')
    m2, w2 = pad_margin_exact(cx + offs[1][0], cy + offs[1][1], 'GND')
    exact.append((min(m1, m2), cx, cy, rot, m1, m2))
    print(f'  exact centre ({cx:.1f},{cy:.1f}) rot {rot}: PHY {m1:+.3f} '
          f'GND {m2:+.3f}', flush=True)
exact = [e for e in exact if e[0] >= 0.02]
exact.sort(reverse=True)
print('exact-pass sites:', len(exact), flush=True)



# ---- ay tail v2: webs ordered by pad->via distance, capped ----
GOALS = [(0, 77.9, 10.08, 'SviaF'), (2, 77.9, 10.08, 'SviaB'),
         (1, 77.9, 10.08, 'SviaIn2'), (2, 76.95, 14.5, 'Bvert145'),
         (2, 77.8, 16.2, 'Bcorner')]
def pad_of(cx, cy, rot):
    return (cx - 0.48, cy) if rot == 0 else (cx, cy - 0.48)
exact.sort(key=lambda e: math.hypot(pad_of(e[1], e[2], e[3])[0] - 77.9,
                                    pad_of(e[1], e[2], e[3])[1] - 10.08))
print('web-testing in distance order, first 60 of', len(exact), flush=True)
results = []
astar = make_astar((75.0, 85.0, 4.0, 17.0), 0.05)
for (m, cx, cy, rot, m1, m2) in exact[:60]:
    p1 = pad_of(cx, cy, rot)
    for gi, (gl, gx, gy, gn) in enumerate(GOALS):
        J = astar('PHY_1V8', ((0,), p1[0], p1[1]), (gl, gx, gy), hw=0.10)
        if J:
            nv = len(J['vias'])
            length = 0.0
            for r in J['runs']:
                pp = r['pts']
                for a, b2 in zip(pp, pp[1:]):
                    length += math.hypot(a[0]-b2[0], a[1]-b2[1])
            print(f'  WEB OK centre ({cx},{cy}) rot {rot} goal {gn}: '
                  f'vias {nv} len {length:.2f} margin {m:+.3f}', flush=True)
            results.append((gi, nv, length, -m, cx, cy, rot, J))
            break
    if results and results[0][0] == 0:
        break
results.sort()
winner = None
if results:
    gi, nv, length, negm, cx, cy, rot, J = results[0]
    winner = (cx, cy, rot, J)
    print('WINNER:', winner[:3], 'goal', GOALS[gi][3], 'vias', nv,
          flush=True)
out = {}
if winner:
    out['c22_site'] = winner[:3]
    out['c22_web'] = winner[3]
json.dump(out, open('scratch/work/ax/design251fix.json', 'w'))
print('AY SCAN4B DONE, fix written:', bool(out), flush=True)

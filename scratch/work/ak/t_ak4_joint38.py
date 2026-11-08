"""t_ak4: joint search for the GND U6.38 heal.
Variables: DAC_SYNC In2 staircase-corner shift (dx,dy) applied to its
3 interior joints; ULPI_D0 dive point P (d0.5) with F stub from its
pad escape; D0 onward flood on In2/B to a rejoin via Q on D0's own
F chain; GND w0.2 track flood on F from U6.38's pad to C21.2's pad
with D0's S2/S3 segs ripped. All gates over the exact item model
(t_ai_lib, fixed in_box_pool). Usage: t_ak4_joint38.py board"""
import collections, math, sys
sys.path.insert(0, 'hw')
sys.path.insert(0, 'scratch/work/ai')
import wx
_app = wx.App(False)
import pcbnew
from t_ai_lib import load_items, pt_margin, in_box_pool, pair_clr

board = pcbnew.LoadBoard(sys.argv[1])
items = load_items(board)

# D0 F chain joints (from board dump, verified 2026-11-07)
QJOINTS = [(74.375, 6.125), (74.625, 6.375), (74.875, 6.625),
           (75.375, 6.625), (75.625, 6.875), (75.875, 7.125),
           (76.125, 7.375), (76.375, 7.625), (76.625, 7.875),
           (76.875, 8.125), (77.125, 8.375), (77.375, 8.625),
           (77.625, 8.875), (77.875, 9.125)]
# DAC_SYNC In2 interior joints to shift (staircase corner)
DAC_JOINTS = [(72.875, 6.125), (73.125, 5.875), (73.375, 5.625)]
SHIFTS = [(0, 0), (-0.125, 0), (-0.25, 0), (0, -0.125),
          (-0.125, -0.125), (-0.25, -0.125), (-0.125, 0.125),
          (0.125, -0.125), (-0.375, 0)]
# D0 segs ripped in every hypothesis (its diagonal + horizontal)
RIP_D0 = [((73.25, 5.662), (73.875, 5.875)),
          ((73.875, 5.875), (74.125, 5.875))]


def shift_items(items, dx, dy):
    out = {0: [], 1: [], 2: []}
    for li in range(3):
        for it in items[li]:
            k, n, d, c = it
            if li == 1 and n == 'DAC_SYNC' and k == 'seg':
                pts = [(d[0], d[1]), (d[2], d[3])]
                np_ = []
                for p in pts:
                    if any(abs(p[0] - j[0]) < 0.01 and
                           abs(p[1] - j[1]) < 0.01 for j in DAC_JOINTS):
                        np_.append((p[0] + dx, p[1] + dy))
                    else:
                        np_.append(p)
                d = (np_[0][0], np_[0][1], np_[1][0], np_[1][1], d[4])
            out[li].append((k, n, d, c))
    return out


def rip_segs(items, net, segs):
    out = {0: [], 1: [], 2: []}
    for li in range(3):
        for it in items[li]:
            k, n, d, c = it
            drop = False
            if k == 'seg' and n == net:
                a, b = (d[0], d[1]), (d[2], d[3])
                for (p, q) in segs:
                    if (abs(a[0] - p[0]) < 0.01 and abs(a[1] - p[1]) < 0.01
                            and abs(b[0] - q[0]) < 0.01
                            and abs(b[1] - q[1]) < 0.01) or \
                       (abs(a[0] - q[0]) < 0.01 and abs(a[1] - q[1]) < 0.01
                            and abs(b[0] - p[0]) < 0.01
                            and abs(b[1] - p[1]) < 0.01):
                        drop = True
            if not drop:
                out[li].append(it)
    return out


def flood(items_mod, li, net, hw, S, T, box, extra_vias=()):
    """extra_vias: (x,y,r,net) treated as items on this layer."""
    pool = list(in_box_pool(items_mod, box, pad=1.2)[li])
    for (x, y, r, n) in extra_vias:
        pool.append(('via', n, (x, y, r), 0.2))
    X0, X1, Y0, Y1 = box
    STEP = 0.0625
    NX = int(round((X1 - X0) / STEP)) + 1
    NY = int(round((Y1 - Y0) / STEP)) + 1
    passable = set()
    for ix in range(NX):
        for iy in range(NY):
            x, y = X0 + ix * STEP, Y0 + iy * STEP
            m, _ = pt_margin(li, x, y, net, hw, pool)
            if m >= 0:
                passable.add((ix, iy))
    si = (int(round((S[0] - X0) / STEP)), int(round((S[1] - Y0) / STEP)))
    if si not in passable:
        # start may sit on same-net copper (pad) not in the model
        passable.add(si)
    seen = {si}
    dq = collections.deque([si])
    while dq:
        c = dq.popleft()
        cx, cy = X0 + c[0] * STEP, Y0 + c[1] * STEP
        if math.hypot(cx - T[0], cy - T[1]) <= hw + 0.08:
            return True
        for ddx in (-1, 0, 1):
            for ddy in (-1, 0, 1):
                n = (c[0] + ddx, c[1] + ddy)
                if n in passable and n not in seen:
                    seen.add(n)
                    dq.append(n)
    return False


def via_ok(items_mod, P, net='ULPI_D0', r=0.25):
    for li in range(3):
        pool = in_box_pool(items_mod, (P[0] - 1.2, P[0] + 1.2,
                                       P[1] - 1.2, P[1] + 1.2),
                           pad=0.3)[li]
        m, w = pt_margin(li, P[0], P[1], net, r, pool)
        if m < 0:
            return False, (li, m, w)
    return True, None


def seg_ok(items_mod, li, a, b, net, hw):
    pool = in_box_pool(items_mod, (min(a[0], b[0]) - 1.2,
                                   max(a[0], b[0]) + 1.2,
                                   min(a[1], b[1]) - 1.2,
                                   max(a[1], b[1]) + 1.2), pad=0.3)[li]
    n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 0.03))
    for k in range(n + 1):
        x = a[0] + (b[0] - a[0]) * k / n
        y = a[1] + (b[1] - a[1]) * k / n
        m, _ = pt_margin(li, x, y, net, hw, pool)
        if m < 0:
            return False
    return True


sols = []
for (dx, dy) in SHIFTS:
    mod = shift_items(items, dx, dy)
    mod = rip_segs(mod, 'ULPI_D0', RIP_D0)
    # candidate dive points
    cands = []
    gx = 72.90
    while gx <= 73.70:
        gy = 5.45
        while gy <= 6.20:
            P = (round(gx, 4), round(gy, 4))
            ok, _why = via_ok(mod, P)
            if ok and seg_ok(mod, 0, (73.25, 5.662), P, 'ULPI_D0', 0.1):
                cands.append(P)
            gy += 0.0625
        gx += 0.0625
    if not cands:
        print(f'shift ({dx},{dy}): no feasible D0 dive')
        continue
    print(f'shift ({dx},{dy}): {len(cands)} feasible D0 dives: '
          f'{cands[:8]}')
    for P in cands:
        # GND flood with D0's dive via present as an F obstacle
        g = flood(mod, 0, 'GND', 0.1, (73.75, 5.30), (73.525, 9.50),
                  (70.0, 77.0, 3.0, 11.0),
                  extra_vias=[(P[0], P[1], 0.25, 'ULPI_D0')])
        if not g:
            continue
        # D0 onward: try In2 and B floods to each Q joint; Q via gates
        for li, lname in ((1, 'In2'), (2, 'B')):
            for Q in QJOINTS:
                okq, _ = via_ok(mod, Q)
                if not okq:
                    continue
                if flood(mod, li, 'ULPI_D0', 0.125, P, Q,
                         (70.0, 80.0, 3.0, 13.0),
                         extra_vias=[(P[0], P[1], 0.25, 'ULPI_D0'),
                                     (Q[0], Q[1], 0.25, 'ULPI_D0')]):
                    sols.append((dx, dy, P, lname, Q))
                    print(f'  SOLUTION shift=({dx},{dy}) P={P} '
                          f'onward {lname} Q={Q}')
print(f'total solutions: {len(sols)}')

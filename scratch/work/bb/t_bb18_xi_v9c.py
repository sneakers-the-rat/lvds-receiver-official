"""t_bb16: XI design v9 (model, from exp254). Moves A3 (STP descent
v3), B (CK jog), C (notch v3), XO re-lay (join at (76.55,10.40)),
PV (75.82,10.30) + F leg via (76.20,10.95), ride v9 (DIR-south band
-> y16.85 strip -> under EP -> PV). Exact seg-distance gate for ride."""
import sys, math
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

BOARD = 'hw/pdlvds_rx.exp254.kicad_pcb'
BOX = (58.0, 96.0, -30.0, 34.0)
LAYN = {0: 'F', 1: 'In2', 2: 'B'}
pool = load_board_pool(BOARD)

# ---------- exact geometry helpers ----------
def pt_seg(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    if L2 == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))

def seg_seg(a, b, c, d):
    def orient(p, q, r):
        v = (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
        return 0 if abs(v) < 1e-12 else (1 if v > 0 else -1)
    if orient(a, b, c) != orient(a, b, d) and orient(c, d, a) != orient(c, d, b):
        return 0.0
    return min(pt_seg(a, c, d), pt_seg(b, c, d), pt_seg(c, a, b), pt_seg(d, a, b))

def exact_gate(segs, net, layer, label, thr=0.30):
    """segs: list of ((x1,y1),(x2,y2),hw). Exact edge clearance vs pool
    items on `layer` (+vias on all layers if layer==2 or 0 handled by
    caller listing). Returns worst list."""
    worst = []
    for (a, b, hw) in segs:
        cx, cy = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        for o in pool[layer]:
            if o[1] == net:
                continue
            oc = C(o)
            if abs(oc[0] - cx) > 6 or abs(oc[1] - cy) > 6:
                continue
            if o[0] == 'seg':
                d = seg_seg(a, b, (o[2][0], o[2][1]), (o[2][2], o[2][3]))
                edge = d - hw - o[2][4]
            elif o[0] == 'via':
                d = min(pt_seg((o[2][0], o[2][1]), a, b),
                        math.hypot(o[2][0] - a[0], o[2][1] - a[1]),
                        math.hypot(o[2][0] - b[0], o[2][1] - b[1]))
                d = pt_seg((o[2][0], o[2][1]), a, b)
                edge = d - hw - o[2][2]
            elif o[0] == 'pad':
                # rect distance from segment: sample endpoints + closest
                px, py = o[2][0], o[2][1]
                hx, hy = o[2][2], o[2][3]
                if len(o[2]) > 4 and abs(o[2][4]) > 0.1:
                    hx, hy = hy, hx
                # distance point->rect for a,b and segment param sweep
                def rect_d(p):
                    dx = max(abs(p[0] - px) - hx, 0.0)
                    dy = max(abs(p[1] - py) - hy, 0.0)
                    return math.hypot(dx, dy)
                d = min(rect_d(a), rect_d(b))
                for t in (0.25, 0.5, 0.75):
                    d = min(d, rect_d((a[0] + t * (b[0] - a[0]),
                                       a[1] + t * (b[1] - a[1]))))
                edge = d - hw
            else:
                continue
            m = edge - 0.2
            if m < thr:
                worst.append((round(m, 3), o[1], o[0], o[2]))
    worst.sort()
    print(f'{label}: worst 8 {worst[:8]}')
    return worst

def gate_items(items_by_layer, label, skip_nets, thr=0.12):
    ps = []
    for l in range(3):
        for it in items_by_layer.get(l, []):
            for o in pool[l]:
                if o[1] in skip_nets:
                    continue
                oc, ic = C(o), C(it)
                if abs(oc[0] - ic[0]) > 3.5 or abs(oc[1] - ic[1]) > 3.5:
                    continue
                m = item_margin(l, it, [o])
                if m < thr:
                    ps.append((round(m, 3), LAYN[l], o))
    ps.sort(key=lambda t: t[0])
    print(f'{label}: worst 6 {[(p[0], p[1], p[2]) for p in ps[:6]]}')
    return ps

def add_via(net, x, y, clr=0.2, r=0.25):
    v = ('via', net, (x, y, r), clr)
    add_items({0: [v], 1: [v], 2: [v]})
    return v

# ---- Move A3: STP descent v3 ----
ripA = [it for it in pool[2]
        if it[1] == 'ULPI_STP' and it[0] == 'seg'
        and 75.9 <= C(it)[0] <= 76.5 and 9.2 <= C(it)[1] <= 13.5]
rip_items(ripA)
newA = {2: [('seg', 'ULPI_STP', (76.44, 9.03, 76.42, 9.50, 0.1), 0.2),
            ('seg', 'ULPI_STP', (76.42, 9.50, 76.425, 12.90, 0.1), 0.2),
            ('seg', 'ULPI_STP', (76.425, 12.90, 76.05, 13.45, 0.1), 0.2)]}
exact_gate([((76.44, 9.03), (76.42, 9.50), 0.1),
            ((76.42, 9.50), (76.425, 12.90), 0.1),
            ((76.425, 12.90), (76.05, 13.45), 0.1)], 'ULPI_STP', 2, 'A3 exact (B)')
add_items(newA)
print('STP frags:', len(fragments('ULPI_STP', BOX)), '(base 2)')

# ---- Move B: CK In2 jog ----
ripB = []
for it in pool[1]:
    if it[1] != 'ULPI_CK' or it[0] != 'seg':
        continue
    d = it[2]
    if abs(d[0] - 74.625) < 0.02 and abs(d[2] - 74.625) < 0.02 and \
       min(d[1], d[3]) <= 9.40 and max(d[1], d[3]) >= 11.00:
        ripB.append(it)
rip_items(ripB)
newB = {1: [('seg', 'ULPI_CK', (74.625, 6.375, 74.625, 9.40, 0.125), 0.2),
            ('seg', 'ULPI_CK', (74.625, 9.40, 74.32, 10.20, 0.125), 0.2),
            ('seg', 'ULPI_CK', (74.32, 10.20, 74.625, 11.00, 0.125), 0.2),
            ('seg', 'ULPI_CK', (74.625, 11.00, 74.625, 13.50, 0.125), 0.2)]}
add_items(newB)
print('CK frags:', len(fragments('ULPI_CK', BOX)), '(base 1)')

# ---- Move C: notch v3 ----
ripC = []
for it in list(pool[0]):
    if it[1] == 'PHY_1V8A' and it[0] == 'seg':
        d = it[2]
        if abs(d[0] - 75.72) < 0.05 and abs(d[1] - 11.0) < 0.05 and \
           abs(d[2] - 75.45) < 0.05 and abs(d[3] - 10.6) < 0.05:
            ripC.append(it)
for it in list(pool[2]):
    if it[1] == 'PHY_1V8A' and it[0] == 'seg':
        d = it[2]
        if abs(d[0] - 75.45) < 0.05 and abs(d[1] - 10.6) < 0.05:
            ripC.append(it)
ripC.append(('via', 'PHY_1V8A', (75.45, 10.6, 0.25), 0.25))
rip_items(ripC)
NV = (74.99, 10.28)
add_items({0: [('seg', 'PHY_1V8A', (75.72, 11.00, NV[0], NV[1], 0.1), 0.25)],
           2: [('seg', 'PHY_1V8A', (NV[0], NV[1], 75.00, 11.50, 0.1), 0.25)]})
add_via('PHY_1V8A', NV[0], NV[1], clr=0.25)
print('1V8A frags:', len(fragments('PHY_1V8A', BOX)), '(base 1)')

# ---- XO re-lay (rip the 8 incl. (76.55,10.45)->(76.55,10.40)) ----
ripX = []
for it in pool[0]:
    if it[1] != 'XO' or it[0] != 'seg':
        continue
    d = it[2]
    pts = ((d[0], d[1]), (d[2], d[3]))
    if any(abs(p[0] - 76.55) < 0.03 and p[1] >= 10.44 for p in pts) or \
       (abs(d[0] - 76.5) < 0.03 and abs(d[1] - 10.75) < 0.03) or \
       (abs(d[2] - 76.5) < 0.03 and abs(d[3] - 10.75) < 0.03):
        ripX.append(it)
print(f'XO rip: {len(ripX)} (expect 8 incl. the 10.40 piece)')
rip_items(ripX)
newX = {0: [('seg', 'XO', (76.55, 10.40, 76.56, 10.80, 0.1), 0.2),
            ('seg', 'XO', (76.56, 10.80, 76.725, 11.15, 0.1), 0.2)]}
gate_items(newX, 'XO gate (model)', ('XO',))
exact_gate([((76.55, 10.40), (76.56, 10.80), 0.1),
            ((76.56, 10.80), (76.725, 11.15), 0.1)], 'XO', 0, 'XO exact (F)')
add_items(newX)
print('XO frags:', len(fragments('XO', BOX)))

# ---- XI PV + F leg ----
PV = (75.82, 10.30)
add_via('XI', PV[0], PV[1])
exact_gate([(PV, PV, 0.25)], 'XI', 0, 'PV point (F, hw=r)')
fleg = {0: [('seg', 'XI', (PV[0], PV[1], 76.18, 10.94, 0.1), 0.2),
            ('seg', 'XI', (76.18, 10.94, 76.25, 11.5625, 0.1), 0.2)]}
exact_gate([((PV[0], PV[1]), (76.18, 10.94), 0.1),
            ((76.18, 10.94), (76.25, 11.5625), 0.1)], 'XI', 0, 'F leg exact (F)')
add_items(fleg)

# ---- XI ride v9 ----
RIDE = [(75.625, 18.625), (74.75, 20.02), (72.05, 20.05), (70.35, 19.35),
        (70.35, 18.15), (72.30, 17.55), (73.10, 16.85), (74.90, 16.85),
        (74.75, 14.20), (75.15, 12.60), (75.70, 11.20), PV]
rsegs = [(a, b, 0.125) for a, b in zip(RIDE, RIDE[1:])]
exact_gate(rsegs, 'XI', 2, 'ride exact (B)')
add_items({2: [('seg', 'XI', (a[0], a[1], b[0], b[1], 0.125), 0.2)
               for a, b in zip(RIDE, RIDE[1:])]})

for n in ('ULPI_STP', 'PHY_1V8A', 'ULPI_CK', 'ULPI_DIR', 'XO', 'XI'):
    print(f'frags {n}: {len(fragments(n, BOX))}')
fr = fragments('XI', BOX)
for i, f in enumerate(fr):
    print(f'  XI frag{i} terms: {f["terms"]}')

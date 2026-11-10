"""t_bb22: XI design v10 (model, from exp254). Moves A3, B, C,
XO v3, PV (75.82,10.30) + F leg v3 (bend (76.18,10.94)), ride v10:
B arc->(74.9,19.95)->(75.5,21.0)->(75.45,22.95)->(72.15,22.95)
->S2 via (72.15,20.0) ->In2 hop-> N2 via (72.25,17.3)
->B (73.1,16.85)->(74.9,16.85)->(74.75,14.2)->(75.15,12.6)
->(75.7,11.2)->PV. Exact gates everywhere."""
import sys, math
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

BOARD = 'hw/pdlvds_rx.exp254.kicad_pcb'
BOX = (58.0, 96.0, -30.0, 34.0)
pool = load_board_pool(BOARD)

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

def item_edge_dist(kind_data, a, b, hw):
    """edge distance from subject seg (a,b,hw) to pool item."""
    kind, data = kind_data
    if kind == 'seg':
        d = seg_seg(a, b, (data[0], data[1]), (data[2], data[3]))
        return d - hw - data[4]
    if kind == 'via':
        return pt_seg((data[0], data[1]), a, b) - hw - data[2]
    if kind == 'pad':
        px, py, hx, hy = data[0], data[1], data[2], data[3]
        if len(data) > 4 and abs(data[4]) > 0.1:
            hx, hy = hy, hx
        def rect_d(p):
            dx = max(abs(p[0] - px) - hx, 0.0)
            dy = max(abs(p[1] - py) - hy, 0.0)
            if abs(p[0] - px) < hx and abs(p[1] - py) < hy:
                return -min(hx - abs(p[0] - px), hy - abs(p[1] - py))
            return math.hypot(dx, dy)
        d = min(rect_d(a), rect_d(b))
        for t in (0.2, 0.4, 0.6, 0.8):
            d = min(d, rect_d((a[0] + t * (b[0] - a[0]),
                               a[1] + t * (b[1] - a[1]))))
        return d - hw
    return 9.9

def exact_gate(segs, net, layer, label, thr=0.30):
    worst = []
    for (a, b, hw) in segs:
        cx, cy = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        for o in pool[layer]:
            if o[1] == net:
                continue
            oc = C(o)
            if abs(oc[0] - cx) > 7 or abs(oc[1] - cy) > 7:
                continue
            m = item_edge_dist((o[0], o[2]), a, b, hw) - 0.2
            if m < thr:
                worst.append((round(m, 3), o[1], o[0], o[2]))
    worst.sort(key=lambda t: t[0])
    print(f'{label}: worst 6 {worst[:6]}')
    return worst

def via_gate(x, y, net, label, r=0.25):
    worst = []
    for l in range(3):
        for o in pool[l]:
            if o[1] == net:
                continue
            oc = C(o)
            if abs(oc[0] - x) > 4 or abs(oc[1] - y) > 4:
                continue
            m = item_edge_dist((o[0], o[2]), (x, y), (x, y), r) - 0.2
            if m < 0.3:
                worst.append((round(m, 3), l, o[1], o[0], o[2]))
    worst.sort(key=lambda t: t[0])
    print(f'{label}: worst 6 {worst[:6]}')
    return worst

def add_via(net, x, y, clr=0.2, r=0.25):
    v = ('via', net, (x, y, r), clr)
    add_items({0: [v], 1: [v], 2: [v]})
    return v

# ---- Move A3 ----
ripA = [it for it in pool[2]
        if it[1] == 'ULPI_STP' and it[0] == 'seg'
        and 75.9 <= C(it)[0] <= 76.5 and 9.2 <= C(it)[1] <= 13.5]
rip_items(ripA)
add_items({2: [('seg', 'ULPI_STP', (76.44, 9.03, 76.42, 9.50, 0.1), 0.2),
               ('seg', 'ULPI_STP', (76.42, 9.50, 76.425, 12.90, 0.1), 0.2),
               ('seg', 'ULPI_STP', (76.425, 12.90, 76.05, 13.45, 0.1), 0.2)]})
print('STP frags:', len(fragments('ULPI_STP', BOX)), '(base 2)')

# ---- Move B ----
ripB = []
for it in pool[1]:
    if it[1] != 'ULPI_CK' or it[0] != 'seg':
        continue
    d = it[2]
    if abs(d[0] - 74.625) < 0.02 and abs(d[2] - 74.625) < 0.02 and \
       min(d[1], d[3]) <= 9.40 and max(d[1], d[3]) >= 11.00:
        ripB.append(it)
rip_items(ripB)
add_items({1: [('seg', 'ULPI_CK', (74.625, 6.375, 74.625, 9.40, 0.125), 0.2),
               ('seg', 'ULPI_CK', (74.625, 9.40, 74.32, 10.20, 0.125), 0.2),
               ('seg', 'ULPI_CK', (74.32, 10.20, 74.625, 11.00, 0.125), 0.2),
               ('seg', 'ULPI_CK', (74.625, 11.00, 74.625, 13.50, 0.125), 0.2)]})
print('CK frags:', len(fragments('ULPI_CK', BOX)), '(base 1)')

# ---- Move C ----
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

# ---- XO v3 ----
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
print(f'XO rip: {len(ripX)} (expect 8)')
rip_items(ripX)
exact_gate([((76.55, 10.40), (76.56, 10.80), 0.1),
            ((76.56, 10.80), (76.725, 11.15), 0.1)], 'XO', 0, 'XO exact (F)')
add_items({0: [('seg', 'XO', (76.55, 10.40, 76.56, 10.80, 0.1), 0.2),
               ('seg', 'XO', (76.56, 10.80, 76.725, 11.15, 0.1), 0.2)]})
print('XO frags:', len(fragments('XO', BOX)))

# ---- PV + F leg v3 ----
PV = (75.82, 10.30)
via_gate(PV[0], PV[1], 'XI', 'PV via gate')
add_via('XI', PV[0], PV[1])
exact_gate([(PV, (76.18, 10.94), 0.1),
            ((76.18, 10.94), (76.25, 11.5625), 0.1)], 'XI', 0, 'F leg exact (F)')
add_items({0: [('seg', 'XI', (PV[0], PV[1], 76.18, 10.94, 0.1), 0.2),
               ('seg', 'XI', (76.18, 10.94, 76.25, 11.5625, 0.1), 0.2)]})

# ---- ride v10 ----
S2 = (72.15, 20.00)
N2 = (72.25, 17.30)
B1 = [(75.625, 18.625), (74.90, 19.95), (75.50, 21.00), (75.45, 22.95),
      (72.15, 22.95), S2]
exact_gate([(a, b, 0.125) for a, b in zip(B1, B1[1:])], 'XI', 2, 'ride B1 exact (B)')
via_gate(S2[0], S2[1], 'XI', 'S2 via gate')
add_via('XI', S2[0], S2[1])
exact_gate([(S2, N2, 0.125)], 'XI', 1, 'hop exact (In2)')
via_gate(N2[0], N2[1], 'XI', 'N2 via gate')
add_via('XI', N2[0], N2[1])
B2 = [N2, (73.10, 16.85), (74.90, 16.85), (74.75, 14.20), (75.15, 12.60),
      (75.70, 11.20), PV]
exact_gate([(a, b, 0.125) for a, b in zip(B2, B2[1:])], 'XI', 2, 'ride B2 exact (B)')
add_items({2: [('seg', 'XI', (a[0], a[1], b[0], b[1], 0.125), 0.2)
               for a, b in zip(B1 + B2[1:], (B1 + B2[1:])[1:])],
           1: [('seg', 'XI', (S2[0], S2[1], N2[0], N2[1], 0.125), 0.2)]})

for n in ('ULPI_STP', 'PHY_1V8A', 'ULPI_CK', 'ULPI_DIR', 'XO', 'XI'):
    print(f'frags {n}: {len(fragments(n, BOX))}')
fr = fragments('XI', BOX)
for i, f in enumerate(fr):
    print(f'  XI frag{i} terms: {f["terms"]}')

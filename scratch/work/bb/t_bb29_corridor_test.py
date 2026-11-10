"""t_bb29: USER-DIRECTION TEST (model, from exp256).
The under-chip B corridor loop = ULPI_STP pass-217 chain bowing east
around GND EP-stitch via (75.6,14.75) (verified t_bb28).
Variant 1: shift the STP chain EAST (76.05,13.45)->(76.48,14.05)
->(76.48,15.55)->(76.05,16.7); gate STP frags+terms; then gate the
STRAIGHT XI B run arc (75.625,18.625) -> PV (75.82,10.30) exactly,
printing every fence.
Variant 2: additionally move the stitch via west-north inside the
EP to (75.0,12.8) (east is sandwiched: priced in analysis); re-gate."""
import sys, math
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

BOARD = 'hw/pdlvds_rx.exp256.kicad_pcb'
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

def fences_for_seg(a, b, hw, net, layer, thr=0.35):
    out = []
    for o in pool[layer]:
        if o[1] == net:
            continue
        oc = C(o)
        if abs(oc[0] - (a[0] + b[0]) / 2) > 6 or abs(oc[1] - (a[1] + b[1]) / 2) > 6:
            continue
        if o[0] == 'seg':
            d = seg_seg(a, b, (o[2][0], o[2][1]), (o[2][2], o[2][3]))
            edge = d - hw - o[2][4]
        elif o[0] == 'via':
            edge = pt_seg((o[2][0], o[2][1]), a, b) - hw - o[2][2]
        else:
            continue
        if edge - 0.2 < thr:
            out.append((round(edge - 0.2, 3), o[1], o[0], o[2]))
    out.sort(key=lambda t: t[0])
    return out

def terms(n):
    fr = fragments(n, BOX)
    return len(fr), sorted(t for f in fr for t in f['terms'])

# ---------- Variant 1: STP chain east ----------
f0, t0 = terms('ULPI_STP')
chain = [it for it in pool[2]
         if it[1] == 'ULPI_STP' and it[0] == 'seg'
         and ((abs(it[2][0] - 76.05) < 0.03 and abs(it[2][1] - 13.45) < 0.03) or
              (abs(it[2][0] - 76.35) < 0.03 and abs(it[2][1] - 13.90) < 0.03) or
              (abs(it[2][2] - 76.05) < 0.03 and abs(it[2][3] - 16.70) < 0.03))]
print(f'chain victims: {len(chain)} (expect 3)')
for it in chain:
    print('   ', it)
rip_items(chain)
NEWCH = [((76.05, 13.45), (76.48, 14.05)), ((76.48, 14.05), (76.48, 15.55)),
         ((76.48, 15.55), (76.05, 16.70))]
for a, b in NEWCH:
    fs = fences_for_seg(a, b, 0.1, 'ULPI_STP', 2)
    print(f'chain-east seg {a}->{b}: fences {fs[:4]}')
add_items({2: [('seg', 'ULPI_STP', (a[0], a[1], b[0], b[1], 0.1), 0.2)
               for a, b in NEWCH]})
f1, t1 = terms('ULPI_STP')
print(f'STP frags {f0}->{f1}; terms equal: {t0 == t1}')

# ---------- Straight XI run, variant 1 ----------
A, B = (75.625, 18.625), (75.82, 10.30)
fs = fences_for_seg(A, B, 0.125, 'XI', 2)
print(f'STRAIGHT RUN v1 fences (margin<0.35): {fs}')

# ---------- Variant 2: stitch via -> (75.0,12.8) ----------
gf0, gt0 = terms('GND')
rip_items([('via', 'GND', (75.6, 14.75, 0.3), 0.2)])
add_items({0: [('via', 'GND', (75.0, 12.8, 0.3), 0.2)],
           1: [('via', 'GND', (75.0, 12.8, 0.3), 0.2)],
           2: [('via', 'GND', (75.0, 12.8, 0.3), 0.2)]})
gf1, gt1 = terms('GND')
padterms0 = sorted(t for t in gt0 if t[0] == 0)
padterms1 = sorted(t for t in gt1 if t[0] == 0)
print(f'GND frags {gf0}->{gf1}; F-pad terms equal: {padterms0 == padterms1}')
fs2 = fences_for_seg(A, B, 0.125, 'XI', 2)
print(f'STRAIGHT RUN v2 fences (margin<0.35): {fs2}')

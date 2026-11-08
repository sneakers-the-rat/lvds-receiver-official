"""t_at11: joint SCL-via / SDA-via placement search for the CAP slot.
Fixed fences: esc items minus {SCL In2 diag tail SE of P0, SCL via,
SDA via (69.32,2.14), SCL F segs east of x68.6 (tail re-lays), GND tree,
+3V3D web, XO web} plus {band jog v4, SDA via S=(70.05,0.82)+B re-lay,
+3V3D via shrink}.
Variables: V_scl, V_sda on 0.05 grids. Constraints (hard gates vs fixed
fences on all layers for vias; chord P0->V_scl gates; slot width =
dist(band corner V1, chord) and dist(chord, V_sda) reported; SDA stub
dist to U9.6 pad rect <= 1.0; SCL F-tail reach soft).
Score: min(slot_v1_chord - 0.825, chord_vs_sda slack, gates)."""
import wx
_app = wx.App(False)
import pcbnew, sys, math
import numpy as np
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
import t_ai_lib as L
from router import netclass

P0 = (68.3, 3.1)          # point ON existing SCL diagonal
V1 = (68.375, 1.125)      # band corner vertex
U96 = (69.225, 2.1, 0.225, 0.15)   # SDA pad rect (cx, cy, hw, hh)
S = (70.05, 0.82)
board = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
items = L.load_items(board)

def key_seg(d):
    a = (round(d[0], 3), round(d[1], 3), round(d[2], 3), round(d[3], 3))
    b = (round(d[2], 3), round(d[3], 3), round(d[0], 3), round(d[1], 3))
    return a, b

REM_SEGS = {
    1: [('HV_SHDN', s) for s in [
        (68.875, 0.625, 69.125, 0.375), (69.125, 0.375, 69.375, 0.125),
        (69.375, 0.125, 69.625, -0.125), (69.625, -0.125, 69.875, -0.375),
        (69.875, -0.375, 70.125, -0.625)]] + [
        ('I2C_SCL', (67.875, 5.125, 68.875, 1.625)),
        ('I2C_SCL', (68.875, 1.625, 69.375, 1.375))],
    2: [('I2C_SDA', s) for s in [
        (69.900, 0.820, 69.875, 0.625), (69.875, 0.625, 69.875, -9.125)]],
    0: [('GND', s) for s in [
        (71.000, 0.270, 69.600, 0.250), (69.600, 0.250, 68.900, 0.850),
        (68.900, 0.850, 68.200, 1.150), (68.200, 1.150, 67.850, 1.220),
        (67.850, 1.220, 67.500, 0.950)]] + [
        ('I2C_SCL', s) for s in [
            (68.625, 1.625, 68.875, 1.625), (68.875, 1.625, 69.125, 1.375),
            (69.125, 1.375, 69.375, 1.375)]],
}
REM_VIAS = [(69.9, 0.82, 'I2C_SDA'), (69.32, 2.14, 'I2C_SDA'),
            (69.375, 1.375, 'I2C_SCL')]
pool = {0: [], 1: [], 2: []}
for li in range(3):
    remkeys = set()
    for n, s in REM_SEGS.get(li, []):
        a, b = key_seg(s)
        remkeys.add((n, a)); remkeys.add((n, b))
    for it in items[li]:
        if it[0] == 'via':
            skip = False
            for vx, vy, vn in REM_VIAS:
                if it[1] == vn and abs(it[2][0] - vx) < 0.01 and \
                   abs(it[2][1] - vy) < 0.01:
                    skip = True
            if skip:
                continue
            if it[1] == '+3V3D' and abs(it[2][0] - 74.625) < 0.01 and \
               abs(it[2][1] - 24.375) < 0.01:
                pool[li].append(('via', '+3V3D', (74.625, 24.375, 0.25),
                                 it[3]))
                continue
        if it[0] == 'seg':
            a, b = key_seg(it[2])
            if (it[1], a) in remkeys:
                continue
            cx = (it[2][0] + it[2][2]) / 2
            cy = (it[2][1] + it[2][3]) / 2
            if li == 0 and it[1] == '+3V3D' and 70 < cx < 76 and 20 < cy < 26:
                continue
            if li == 1 and it[1] == 'XO' and 66 < cx < 76 and 16 < cy < 23:
                continue
        pool[li].append(it)

def add_via(net, x, y, r=0.25):
    for li in range(3):
        pool[li].append(('via', net, (x, y, r), netclass(net)[1]))

def add_seg(li, net, a, b, w):
    pool[li].append(('seg', net, (a[0], a[1], b[0], b[1], w / 2),
                     netclass(net)[1]))

BANDV = [(68.625, 0.875), (68.75, 0.5), (69.0, 0.25), (69.25, 0.0),
         (69.5, -0.25), (69.75, -0.5), (70.125, -0.625)]
for i in range(len(BANDV) - 1):
    add_seg(1, 'HV_SHDN', BANDV[i], BANDV[i + 1], 0.25)
add_via('I2C_SDA', *S)
add_seg(2, 'I2C_SDA', (69.875, -1.5), (69.875, -9.125), 0.25)
add_seg(2, 'I2C_SDA', (69.875, -1.5), S, 0.25)
# diagonal stub up to P0 (kept part): (67.875,5.125)->P0 on the old line
add_seg(1, 'I2C_SCL', (67.875, 5.125), P0, 0.20)

BOX = (66.0, 72.5, -0.5, 5.0)
local = L.in_box_pool(pool, BOX, pad=0.6)

def via_gate(net, x, y, extra=()):
    worst = 9.9
    for l in range(3):
        p = local[l] + [e for e in extra if e[1] != net]
        mm, _ = L.pt_margin(l, x, y, net, 0.25, p)
        worst = min(worst, mm)
    return worst

def seg_gate(l, net, a, b, extra=()):
    p = local[l] + [e for e in extra if e[1] != net]
    mm, _ = L.seg_margin(l, a, b, net, 0.10, p, step=0.02)
    return mm

def pt_seg(px, py, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0,
                    ((px - a[0]) * dx + (py - a[1]) * dy) / L2))
    return math.hypot(px - (a[0] + t * dx), py - (a[1] + t * dy))

def rect_dist(px, py, r):
    cx, cy, hw, hh = r
    return math.hypot(max(abs(px - cx) - hw, 0.0),
                      max(abs(py - cy) - hh, 0.0))

results = []
scl_grid = [(69.0 + 0.05 * i, 1.05 + 0.05 * j)
            for i in range(25) for j in range(24)]
sda_grid = [(68.55 + 0.05 * i, 1.55 + 0.05 * j)
            for i in range(30) for j in range(24)]
# pre-gate SDA candidates alone (fast reject)
sda_ok = []
for (x, y) in sda_grid:
    if rect_dist(x, y, U96) > 1.05:
        continue
    g = via_gate('I2C_SDA', x, y)
    if g >= 0.0:
        sda_ok.append((x, y, g))
print(f'SDA via candidates passing fixed gates: {len(sda_ok)}', flush=True)
for (sx, sy) in scl_grid:
    gs = via_gate('I2C_SCL', sx, sy)
    if gs < 0.0:
        continue
    chord = (P0, (sx, sy))
    gc = seg_gate(1, 'I2C_SCL', P0, (sx, sy))
    if gc < -0.02:
        continue
    slot = pt_seg(V1[0], V1[1], P0, (sx, sy)) - 0.325
    for (ax, ay, ga) in sda_ok:
        if math.hypot(ax - sx, ay - sy) < 0.70:
            continue
        d = pt_seg(ax, ay, P0, (sx, sy))
        if d < 0.575:
            continue
        g2 = via_gate('I2C_SDA', ax, ay,
                      extra=[('via', 'I2C_SCL', (sx, sy, 0.25), 0.2)])
        if g2 < 0.0:
            continue
        gc2 = seg_gate(1, 'I2C_SCL', P0, (sx, sy),
                       extra=[('via', 'I2C_SDA', (ax, ay, 0.25), 0.2)])
        if gc2 < -0.02:
            continue
        score = min(slot, d - 0.575, gs, ga, gc2 + 0.02)
        results.append((score, slot, d - 0.575, (sx, sy), (ax, ay),
                        gs, ga, gc))
results.sort(reverse=True)
print(f'joint feasible: {len(results)}')
for r in results[:15]:
    print(f'score {r[0]:+.3f} slot {r[1]:+.3f} chord-sda {r[2]:+.3f} '
          f'Vscl {r[3]} Vsda {r[4]} gates scl {r[5]:+.3f} sda {r[6]:+.3f} '
          f'chord {r[7]:+.3f}')

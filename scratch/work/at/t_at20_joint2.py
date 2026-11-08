"""t_at20: joint search {SCL via, SDA via, chord bend} in the
U9-west-1.0 configuration.
Base pool: v6 (t_at16) edits PLUS:
 - U9 pads shifted west 1.0 (old U9 pads removed from F pool;
   new pads added as fences; U9's own-net F stubs near the pads
   removed: SCL F west cluster, TMP_ALERT F start, +3V3A pad feed,
   GND F tree already out).
 - SCL via / SDA fanout via / SCL In2 tail / SCL F tail east of
   (67.625,1.625) all removed (variables / re-lays).
Chord: (68.55,2.75) [on diagonal] -> bend -> SCL via.
Score: min(all gates, slot slack) with slot = min over chord segs
and SCL via of dist-to-band-polyline - 0.425 (track need)."""
import wx
_app = wx.App(False)
import pcbnew, sys, math
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
import t_ai_lib as L
from router import netclass

S = (70.05, 0.82)
CHORD0 = (68.55, 2.75)
board = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
items = L.load_items(board)

def key_seg(d):
    a = (round(d[0], 3), round(d[1], 3), round(d[2], 3), round(d[3], 3))
    b = (round(d[2], 3), round(d[3], 3), round(d[0], 3), round(d[1], 3))
    return a, b

BAND_RIP = [(68.625, 0.875, 68.875, 0.625),
            (68.875, 0.625, 69.125, 0.375), (69.125, 0.375, 69.375, 0.125),
            (69.375, 0.125, 69.625, -0.125),
            (69.625, -0.125, 69.875, -0.375),
            (69.875, -0.375, 70.125, -0.625)]
REM_SEGS = {
    1: [('HV_SHDN', s) for s in BAND_RIP] + [
        ('I2C_SCL', (68.875, 1.625, 69.375, 1.375)),
        ('I2C_SCL', (67.875, 5.125, 68.875, 1.625))],
    0: [('CAP_CLK', (70.6, 1.78, 70.02, 1.83))] + [
        ('GND', s) for s in [
            (71.000, 0.270, 69.600, 0.250), (69.600, 0.250, 68.900, 0.850),
            (68.900, 0.850, 68.200, 1.150), (68.200, 1.150, 67.850, 1.220),
            (67.850, 1.220, 67.500, 0.950)]] + [
        ('I2C_SCL', s) for s in [
            (69.375, 1.375, 67.875, 1.625), (67.875, 1.625, 67.500, 1.625),
            (67.500, 1.625, 67.375, 2.000), (67.375, 1.875, 67.625, 1.625),
            (67.625, 1.625, 68.625, 1.625), (68.625, 1.625, 68.875, 1.625),
            (68.875, 1.625, 69.125, 1.375), (69.125, 1.375, 69.375, 1.375),
            (67.275, 2.100, 67.275, 1.850), (67.275, 1.850, 67.375, 1.875)]] + [
        ('TMP_ALERT', s) for s in [
            (67.275, 3.400, 67.025, 3.400)]] + [
        ('+3V3A', (69.225, 2.750, 69.475, 2.750))],
    2: [('I2C_SDA', s) for s in [
        (69.900, 0.820, 69.875, 0.625), (69.875, 0.625, 69.875, -9.125)]],
}
REM_VIAS = [(69.9, 0.82, 'I2C_SDA'), (69.375, 1.375, 'I2C_SCL'),
            (70.02, 1.83, 'CAP_CLK'), (69.32, 2.14, 'I2C_SDA')]
U9_OLD_PADS = [(67.275, 2.1), (67.275, 2.75), (67.275, 3.4),
               (69.225, 3.4), (69.225, 2.75), (69.225, 2.1), (68.25, 2.75)]
pool = {0: [], 1: [], 2: []}
for li in range(3):
    remkeys = set()
    for n, s in REM_SEGS.get(li, []):
        a, b = key_seg(s)
        remkeys.add((n, a)); remkeys.add((n, b))
    for it in items[li]:
        if it[0] == 'pad':
            d = it[2]
            if any(abs(d[0] - px) < 0.01 and abs(d[1] - py) < 0.01
                   for px, py in U9_OLD_PADS):
                continue
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

def add_via(net, x, y, r=0.25, pool_=None):
    p = pool_ if pool_ is not None else pool
    for li in range(3):
        p[li].append(('via', net, (x, y, r), netclass(net)[1]))

def add_seg(li, net, a, b, w, pool_=None):
    p = pool_ if pool_ is not None else pool
    p[li].append(('seg', net, (a[0], a[1], b[0], b[1], w / 2),
                  netclass(net)[1]))

def add_pad(net, x, y, hw, hh):
    pool[0].append(('pad', net, (x, y, hw, hh, 0.0), netclass(net)[1]))

# fixed v6 copper
BANDV = [(68.625, 0.875), (68.75, 0.5), (69.0, 0.25), (69.25, 0.0),
         (69.5, -0.25), (69.75, -0.5), (70.125, -0.625)]
for i in range(len(BANDV) - 1):
    add_seg(1, 'HV_SHDN', BANDV[i], BANDV[i + 1], 0.25)
add_via('CAP_CLK', 70.15, 1.72)
add_seg(0, 'CAP_CLK', (70.6, 1.78), (70.15, 1.72), 0.20)
add_via('I2C_SDA', *S)
add_seg(2, 'I2C_SDA', (69.875, -1.5), (69.875, -9.125), 0.25)
add_seg(2, 'I2C_SDA', (69.875, -1.5), S, 0.25)
add_seg(1, 'I2C_SCL', (67.875, 5.125), CHORD0, 0.20)  # diagonal stub
# U9 new pads (west 1.0): (net, x, y, hw, hh)
for n, x, y, hw, hh in [
        ('I2C_SCL', 66.275, 2.1, 0.225, 0.15), ('GND', 66.275, 2.75,
         0.225, 0.15), ('TMP_ALERT', 66.275, 3.4, 0.225, 0.15),
        ('GND', 68.225, 3.4, 0.225, 0.15), ('+3V3A', 68.225, 2.75,
         0.225, 0.15), ('I2C_SDA', 68.225, 2.1, 0.225, 0.15),
        ('GND', 67.25, 2.75, 0.5, 0.8)]:
    add_pad(n, x, y, hw, hh)

BAND_POLY = [(61.875, 7.625), (62.125, 7.375), (62.375, 7.125),
             (62.625, 6.875), (62.875, 6.625), (63.125, 6.375),
             (63.375, 6.125), (63.625, 5.875), (63.875, 5.625),
             (64.125, 5.375), (64.375, 5.125), (64.625, 4.875),
             (64.875, 4.625), (65.125, 4.375), (65.375, 4.125),
             (65.625, 3.875), (65.875, 3.625), (66.125, 3.375),
             (66.375, 3.125), (66.625, 2.875), (66.875, 2.625),
             (67.125, 2.375), (67.375, 2.125), (67.625, 1.875),
             (67.875, 1.625), (68.125, 1.375)] + BANDV + [
             (70.375, -0.875), (70.625, -1.125), (70.875, -1.375)]

def pt_seg(px, py, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0,
                    ((px - a[0]) * dx + (py - a[1]) * dy) / L2))
    return math.hypot(px - (a[0] + t * dx), py - (a[1] + t * dy))

def band_dist(px, py):
    return min(pt_seg(px, py, BAND_POLY[i], BAND_POLY[i + 1])
               for i in range(len(BAND_POLY) - 1))

BOX = (65.5, 72.5, -0.5, 5.5)
local = L.in_box_pool(pool, BOX, pad=0.6)
SDA_PAD_RECT = (68.225, 2.1, 0.225, 0.15)

def rect_dist(px, py, r):
    cx, cy, hw, hh = r
    return math.hypot(max(abs(px - cx) - hw, 0.0),
                      max(abs(py - cy) - hh, 0.0))

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

results = []
scl_grid = [(69.0 + 0.05 * i, 1.15 + 0.05 * j)
            for i in range(17) for j in range(12)]
sda_grid = [(68.5 + 0.05 * i, 1.8 + 0.05 * j)
            for i in range(23) for j in range(19)]
bend_grid = [(68.7 + 0.1 * i, 1.9 + 0.1 * j)
             for i in range(10) for j in range(9)]
sda_ok = []
for (x, y) in sda_grid:
    if rect_dist(x, y, SDA_PAD_RECT) > 1.6:
        continue
    g = via_gate('I2C_SDA', x, y)
    if g >= 0.0:
        sda_ok.append((x, y, g))
print(f'SDA candidates: {len(sda_ok)}', flush=True)
for (sx, sy) in scl_grid:
    gs = via_gate('I2C_SCL', sx, sy)
    if gs < 0.0:
        continue
    slot_via = band_dist(sx, sy) - 0.25 - 0.125 - 0.20
    for (bx, by) in bend_grid:
        if math.hypot(bx - sx, by - sy) < 0.3:
            continue
        g1 = seg_gate(1, 'I2C_SCL', CHORD0, (bx, by))
        if g1 < 0.0:
            continue
        g2 = seg_gate(1, 'I2C_SCL', (bx, by), (sx, sy))
        if g2 < 0.0:
            continue
        slot = min(slot_via,
                   min(pt_seg(0, 0, (0, 0), (0, 0)), 9.9))
        # slot for segs: sample points along both segs
        smin = 9.9
        for (a, b) in ((CHORD0, (bx, by)), ((bx, by), (sx, sy))):
            for k in range(21):
                px = a[0] + (b[0] - a[0]) * k / 20
                py = a[1] + (b[1] - a[1]) * k / 20
                smin = min(smin, band_dist(px, py) - 0.10 - 0.125 - 0.20)
        slot = min(slot_via, smin)
        if slot < 0.0:
            continue
        for (ax, ay, ga) in sda_ok:
            if math.hypot(ax - sx, ay - sy) < 0.70:
                continue
            extra = [('via', 'I2C_SCL', (sx, sy, 0.25), 0.2)]
            g3 = via_gate('I2C_SDA', ax, ay, extra=extra)
            if g3 < 0.0:
                continue
            g4 = seg_gate(1, 'I2C_SCL', CHORD0, (bx, by),
                          extra=[('via', 'I2C_SDA', (ax, ay, 0.25), 0.2)])
            g5 = seg_gate(1, 'I2C_SCL', (bx, by), (sx, sy),
                          extra=[('via', 'I2C_SDA', (ax, ay, 0.25), 0.2)])
            if min(g4, g5) < 0.0:
                continue
            score = min(gs, ga, g1, g2, g3, g4, g5, slot)
            results.append((score, slot, (sx, sy), (bx, by), (ax, ay)))
results.sort(reverse=True)
print(f'joint feasible: {len(results)}')
for r in results[:12]:
    print(f'score {r[0]:+.3f} slot {r[1]:+.3f} SCLvia {r[2]} '
          f'bend {r[3]} SDAvia {r[4]}')

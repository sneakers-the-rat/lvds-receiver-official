"""t_aq3: +3V3D U11.14 connection (exp234 -> exp235).

Design (exact-model gated before build):
+5V: rip the F staircase SW branch south of U11 (4 thin segs) and the
w0.6 trunk seg; re-lay the trunk shorter (to x54.60) and detour the
feed SOUTH on F through the empty field (y22.95) joining the trunk
from below. This frees the channel south of U11.14's pad.
+3V3D: F stub south from U11.14 pad (56.75,24.812) to via
(56.75,24.00) d0.5; In2 south to y21.0, east to x66.55, north to
rise via (66.55,22.35) landing on C38's F chain seg
(66.55,22.75)->(66.55,21.75).
"""
import sys, math, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
from t_ai_lib import (load_items, pt_margin, seg_margin, in_box_pool,
                      fmt_it)
from router import netclass

SRC = 'hw/pdlvds_rx.exp234.kicad_pcb'
DST = 'hw/pdlvds_rx.exp235.kicad_pcb'
LAY = [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
MM = lambda v: int(round(v * 1e6))  # noqa: E731
BIGBOX = (46.0, 70.0, 14.0, 28.0)  # in_box_pool box = (x0,x1,y0,y1)!

SEG_RIPS = [
    ('+5V', 57.375, 24.375, 57.125, 24.125),
    ('+5V', 57.125, 24.125, 56.875, 23.875),
    ('+5V', 56.875, 23.875, 56.625, 23.875),
    ('+5V', 56.625, 23.875, 56.375, 23.625),
    ('+5V', 56.375, 23.625, 47.875, 23.625),
]
VIA_RIPS = []


def seg(net, li, a, c, w):
    return (li, ('seg', net, (a[0], a[1], c[0], c[1], w / 2),
                 netclass(net)[1]))


def via(net, x, y, d):
    return ('via', net, (x, y, d / 2), netclass(net)[1])


ADDS = [
    seg('+5V', 0, (57.250, 24.562), (57.850, 23.950), 0.2),
    seg('+5V', 0, (57.850, 23.950), (57.850, 22.950), 0.2),
    seg('+5V', 0, (57.850, 22.950), (54.600, 22.950), 0.2),
    seg('+5V', 0, (54.600, 22.950), (54.600, 23.450), 0.2),
    seg('+5V', 0, (54.600, 23.625), (47.875, 23.625), 0.6),
    seg('+3V3D', 0, (56.750, 24.812), (56.750, 24.000), 0.2),
    via('+3V3D', 56.750, 24.000, 0.5),
    seg('+3V3D', 1, (56.750, 24.000), (56.750, 20.800), 0.2),
    seg('+3V3D', 1, (56.750, 20.800), (66.550, 20.800), 0.2),
    seg('+3V3D', 1, (66.550, 20.800), (66.550, 22.350), 0.2),
    via('+3V3D', 66.550, 22.350, 0.5),
]

b = pcbnew.LoadBoard(SRC)
codes = {n: b.GetNetcodeFromNetname(n) for n in ('+5V', '+3V3D')}
items = load_items(b)

sr = set()
for (net, ax, ay, bx, by) in SEG_RIPS:
    sr.add((net, round(ax, 3), round(ay, 3), round(bx, 3), round(by, 3)))
    sr.add((net, round(bx, 3), round(by, 3), round(ax, 3), round(ay, 3)))
vr = set((net, round(x, 3), round(y, 3)) for net, x, y in VIA_RIPS)
statics = {li: [] for li in range(3)}
nrip = 0
for li in range(3):
    for it in items[li]:
        if it[0] == 'seg':
            d = it[2]
            if (it[1], round(d[0], 3), round(d[1], 3), round(d[2], 3),
                    round(d[3], 3)) in sr:
                nrip += 1
                continue
        elif it[0] == 'via':
            d = it[2]
            if (it[1], round(d[0], 3), round(d[1], 3)) in vr:
                nrip += 1
                continue
        statics[li].append(it)
print(f'model rips: {nrip} (expect 5)')
assert nrip == 5

pool = in_box_pool(statics, BIGBOX, pad=1.2)
# pool sanity: known fence items MUST be present (a pool that can
# silently omit copper voids the gate -- aj-session law)
def _inpool(li, kind, net, x, y):
    for it in pool[li]:
        if it[0] == kind and it[1] == net and abs(it[2][0] - x) < 0.01 \
                and abs(it[2][1] - y) < 0.01:
            return True
    return False
assert _inpool(1, 'via', 'SW1', 64.875, 21.625), 'POOL MISSING SW1 via'
assert _inpool(0, 'pad', '+5V', 57.250, 24.812), 'POOL MISSING +5V pad'
assert _inpool(0, 'pad', 'GND', 56.500, 26.250), 'POOL MISSING U11 EP'
print(f'pool sizes: F={len(pool[0])} In2={len(pool[1])} B={len(pool[2])}')
worst = 9.9
worst_desc = None
for idx, a in enumerate(ADDS):
    plist = [list(pool[l]) for l in range(3)]
    for prev in ADDS[:idx]:
        if isinstance(prev[0], int):
            plist[prev[0]].append(prev[1])
        else:
            for l in range(3):
                plist[l].append(prev)
    if isinstance(a[0], int):
        li, it = a
        m, w = seg_margin(li, (it[2][0], it[2][1]), (it[2][2], it[2][3]),
                          it[1], it[2][4], plist[li], step=0.01)
        if m < worst:
            worst, worst_desc = m, (fmt_it(it), li, fmt_it(w))
    else:
        for l in range(3):
            m, w = pt_margin(l, a[2][0], a[2][1], a[1], a[2][2], plist[l])
            if m < worst:
                worst, worst_desc = m, (fmt_it(a), l, fmt_it(w))
print(f'exact gate: worst {worst:+.4f} at {worst_desc}')
assert worst >= -0.001, 'GATE FAIL - aborting build'

# ---- board rip ---------------------------------------------------------------
victims = []
for t in list(b.GetTracks()):
    net = t.GetNetname()
    if isinstance(t, pcbnew.PCB_VIA):
        continue
    s = t.GetStart()
    e = t.GetEnd()
    key = (net, round(s.x / 1e6, 3), round(s.y / 1e6, 3),
           round(e.x / 1e6, 3), round(e.y / 1e6, 3))
    if key in sr:
        victims.append(('seg', net, key[1:]))
        b.Remove(t)
print(f'rip victims: {len(victims)} (expect 5)')
for v in victims:
    print('   ', v)
assert len(victims) == 5


def add_track(net, li, a, c, w):
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(MM(c[0]), MM(c[1])))
    t.SetWidth(MM(w))
    t.SetLayer(LAY[li])
    t.SetNetCode(codes[net])
    b.Add(t)


def add_via(net, x, y, d=0.5, drill=0.3):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    v.SetWidth(MM(d))
    v.SetDrill(MM(drill))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNetCode(codes[net])
    b.Add(v)


for a in ADDS:
    if isinstance(a[0], int):
        li, it = a
        d = it[2]
        add_track(it[1], li, (d[0], d[1]), (d[2], d[3]), d[4] * 2)
    else:
        add_via(a[1], a[2][0], a[2][1], a[2][2] * 2)

filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())
b.Save(DST)
print('saved', DST)

print('BUILD DONE (census via t_aq4)')

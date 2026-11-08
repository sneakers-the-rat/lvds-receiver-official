"""t_ap14: probe A6 band via candidates in the ap13 pool
(statics + CC2 band re-plan): per-layer worst fences + stub margins."""
import sys, math, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
from t_ai_lib import (load_items, pt_margin, seg_margin, in_box_pool,
                      fmt_it)
from router import netclass

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp233.kicad_pcb')
items = load_items(b)
A6 = (29.750, 71.480)
B5 = (30.500, 73.180)
CC2_NORTH = (31.375, 69.375)
BIGBOX = (26.0, 48.0, 42.0, 76.0)

def seg(net, li, a, c, w):
    return (li, ('seg', net, (a[0], a[1], c[0], c[1], w / 2),
                 netclass(net)[1]))
def via(net, x, y, d):
    return ('via', net, (x, y, d / 2), netclass(net)[1])

SEG_RIPS = [
    ('CC2', 30.500, 72.930, 30.375, 72.375),
    ('CC2', 30.500, 73.180, 30.500, 72.930),
    ('CC2', 30.375, 72.375, 30.375, 71.625),
    ('CC2', 30.375, 71.625, 30.375, 70.875),
    ('CC2', 30.375, 70.875, 30.625, 70.625),
    ('CC2', 30.625, 70.625, 30.625, 70.125),
    ('CC2', 30.625, 70.125, 30.875, 69.875),
    ('CC2', 30.875, 69.875, 31.125, 69.625),
    ('CC2', 31.125, 69.625, 31.375, 69.375)]
sr = set()
for (net, ax, ay, bx, by) in SEG_RIPS:
    sr.add((net, round(ax, 3), round(ay, 3), round(bx, 3), round(by, 3)))
    sr.add((net, round(bx, 3), round(by, 3), round(ax, 3), round(ay, 3)))
st = {li: [] for li in range(3)}
for li in range(3):
    for it in items[li]:
        if it[0] == 'seg':
            d = it[2]
            if (it[1], round(d[0], 3), round(d[1], 3), round(d[2], 3),
                    round(d[3], 3)) in sr:
                continue
        elif it[0] == 'via':
            d = it[2]
            if it[1] == 'CC2' and round(d[0], 3) == 30.375 \
                    and round(d[1], 3) == 72.375:
                continue
        st[li].append(it)
# CC2 band via + stub + a REPRESENTATIVE join chain is complex; probe
# with via+stub only (chain runs north on In2, east of x30.5).
adds = [via('CC2', 30.5, 72.275, 0.5),
        seg('CC2', 0, B5, (30.5, 72.275), 0.2)]
it2 = {li: list(st[li]) for li in range(3)}
for a in adds:
    if isinstance(a[0], int):
        it2[a[0]].append(a[1])
    else:
        for li in range(3):
            it2[li].append(a)
pool = in_box_pool(it2, BIGBOX, pad=1.2)
for (x, y) in [(30.15, 72.28), (30.10, 72.30), (30.20, 72.25),
               (30.05, 72.35), (30.25, 72.30), (29.95, 72.40)]:
    ms = []
    for li in range(3):
        m, w = pt_margin(li, x, y, 'DP_CON', 0.25, pool[li])
        ms.append(f'L{li} {m:+.3f} [{fmt_it(w)}]')
    print(f'via ({x},{y}): ' + ' | '.join(ms))
    for poly in [[A6, (29.820, 72.150), (x, y)],
                 [A6, (29.800, 72.050), (x, y)],
                 [A6, (x, y)]]:
        mm = 9.9
        ww = None
        for a, c in zip(poly, poly[1:]):
            m2, w2 = seg_margin(0, a, c, 'DP_CON', 0.10, pool[0],
                                step=0.02)
            if m2 < mm:
                mm, ww = m2, w2
        print(f'    stub {poly[1:-1]}: {mm:+.3f} [{fmt_it(ww)}]')

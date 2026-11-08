"""t_ap21: probe A6 south via (29.94,74.0) + stub shape 1 in the
ap20 pool variants: (a) +CC2 via/stub + DM B7 d0.5; (b) also with a
representative CC2 join chain present."""
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
            if (it[1], round(d[0], 3), round(d[1], 3)) in (
                    ('CC2', 30.375, 72.375), ('DM_CON', 29.375, 72.375)):
                continue
        st[li].append(it)

def probe(adds, label, x=29.94, y=74.0):
    it2 = {li: list(st[li]) for li in range(3)}
    for a in adds:
        if isinstance(a[0], int):
            it2[a[0]].append(a[1])
        else:
            for li in range(3):
                it2[li].append(a)
    pool = in_box_pool(it2, BIGBOX, pad=1.2)
    print(f'-- {label}')
    for li in range(3):
        m, w = pt_margin(li, x, y, 'DP_CON', 0.25, pool[li])
        print(f'   via L{li}: {m:+.3f} [{fmt_it(w)}]')
    poly = [A6, (29.800, 71.970), (29.940, 72.320), (x, y)]
    for a, c in zip(poly, poly[1:]):
        m, w = seg_margin(0, a, c, 'DP_CON', 0.10, pool[0], step=0.02)
        print(f'   stub {a}->{c}: {m:+.3f} [{fmt_it(w)}]')

base = [via('CC2', 30.5, 72.275, 0.5),
        seg('CC2', 0, B5, (30.5, 72.275), 0.2),
        via('DM_CON', 29.375, 72.375, 0.5)]
probe(base, 'cc2 via/stub + DM d0.5')
probe(base, 'same, via at (29.96,73.85)', x=29.96, y=73.85)
probe(base, 'same, via at (29.92,74.10)', x=29.92, y=74.10)

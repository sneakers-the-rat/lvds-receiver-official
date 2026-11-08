"""t_ap15: probe CC2 band via candidates EAST of x30.5 in the
statics pool (ap13 rip set): why did the scan stop at x30.525?"""
import sys, math, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
from t_ai_lib import (load_items, pt_margin, seg_margin, in_box_pool,
                      fmt_it)

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp233.kicad_pcb')
items = load_items(b)
B5 = (30.500, 73.180)
BIGBOX = (26.0, 48.0, 42.0, 76.0)
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
pool = in_box_pool(st, BIGBOX, pad=1.2)
for (x, y) in [(30.85, 72.30), (30.95, 72.40), (31.10, 72.30),
               (30.75, 72.60), (30.65, 72.20), (31.20, 72.60),
               (30.85, 71.95), (31.05, 71.95)]:
    ms = []
    for li in range(3):
        m, w = pt_margin(li, x, y, 'CC2', 0.25, pool[li])
        ms.append(f'L{li} {m:+.3f} [{fmt_it(w)}]')
    print(f'via ({x},{y}): ' + ' | '.join(ms))
    for poly in [[B5, (x, y)], [B5, (B5[0], y), (x, y)],
                 [B5, (30.90, 72.90), (x, y)]]:
        mm = 9.9
        ww = None
        for a, c in zip(poly, poly[1:]):
            m2, w2 = seg_margin(0, a, c, 'CC2', 0.10, pool[0],
                                step=0.02)
            if m2 < mm:
                mm, ww = m2, w2
        print(f'    stub {poly[1:-1]}: {mm:+.3f} [{fmt_it(ww)}]')

"""t_ap5: why do NE DM_CON via positions fail? (exp233)
For a grid of DM via positions, print via margin / F stub best /
In2 rejoin margins (to B7 anchor (29.625,70.625) and staircase
anchor (30.125,70.125)) with killer items, no thresholds.
Rips = t_ap4's DM junction rip."""
import sys, math, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
from t_ai_lib import (load_items, in_box_pool, apply_rip, fmt_it,
                      pair_clr)
from router import netclass, dist_to_item

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp233.kicad_pcb')
items = load_items(b)
A7 = (30.250, 71.480)
BIGBOX = (26.0, 48.0, 42.0, 76.0)
DM_B7PT = (29.625, 70.625)
DM_STPT = (30.125, 70.125)
RIP_DM = [('via', 'DM_CON', 29.875, 70.375),
          ('seg', 'DM_CON', 29.875, 70.375),
          ('seg', 'DM_CON', 30.250, 70.980),
          ('seg', 'DM_CON', 30.125, 70.125),
          ('seg', 'DM_CON', 29.625, 70.625)]
statics, nrip = apply_rip(items, RIP_DM)
print(f'rips: {nrip}')

def prep(pool):
    out = []
    for it in pool:
        k, net, d, clr = it
        if k == 'pad':
            c = (d[0], d[1]); reach = math.hypot(d[2], d[3])
        elif k == 'via':
            c = (d[0], d[1]); reach = d[2]
        else:
            c = ((d[0] + d[2]) / 2, (d[1] + d[3]) / 2)
            reach = math.hypot(d[2] - d[0], d[3] - d[1]) / 2 + d[4]
        out.append((it, c, reach))
    return out

def ptm_fast(pp, x, y, net, rad):
    m = 9.9; worst = None
    for it, c, reach in pp:
        if it[1] == net:
            continue
        if math.hypot(x - c[0], y - c[1]) - reach - rad \
                - pair_clr(net, it[1]) >= m:
            continue
        d = dist_to_item(it, x, y) - rad - pair_clr(net, it[1])
        if d < m:
            m, worst = d, it
    return m, worst

def segm_fast(pp, a, b, net, hw, step=0.05):
    n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / step))
    m = 9.9; worst = None
    for k in range(n + 1):
        mm_, w_ = ptm_fast(pp, a[0] + (b[0] - a[0]) * k / n,
                           a[1] + (b[1] - a[1]) * k / n, net, hw)
        if mm_ < m:
            m, worst = mm_, w_
    return m, worst

it2 = {li: list(statics[li]) for li in range(3)}
pool = in_box_pool(it2, BIGBOX, pad=1.2)
pp = {li: prep(pool[li]) for li in range(3)}

rows = []
for ix in range(19):
    x = 29.90 + ix * 0.05
    for iy in range(31):
        y = 69.30 + iy * 0.05
        mv = min(ptm_fast(pp[li], x, y, 'DM_CON', 0.30)
                 for li in range(3))
        ms = -9.9
        for poly in ([A7, (x, y)], [A7, (30.250, 70.980), (x, y)],
                     [A7, (x, A7[1]), (x, y)]):
            m = 9.9
            for a, c in zip(poly, poly[1:]):
                mm, _ = segm_fast(pp[0], a, c, 'DM_CON', 0.10)
                m = min(m, mm)
            ms = max(ms, m)
        mb, wb = segm_fast(pp[1], (x, y), DM_B7PT, 'DM_CON', 0.10)
        mt, wt = segm_fast(pp[1], (x, y), DM_STPT, 'DM_CON', 0.10)
        rows.append((min(mv[0], ms, mb, mt), x, y, mv, ms, (mb, wb),
                     (mt, wt)))
rows.sort(reverse=True)
print('top 12 DM positions by joint score:')
for r in rows[:12]:
    print(f'  tot {r[0]:+.3f} ({r[1]:.2f},{r[2]:.2f}): via {r[3][0]:+.3f}'
          f' (L? vs {fmt_it(r[3][1])}) stub {r[4]:+.3f} '
          f'rejoinB7 {r[5][0]:+.3f} vs {fmt_it(r[5][1])} '
          f'rejoinST {r[6][0]:+.3f} vs {fmt_it(r[6][1])}')
print('\nbest NE positions (x>=30.30, y<=70.10):')
ne = [r for r in rows if r[1] >= 30.30 and r[2] <= 70.10]
for r in ne[:8]:
    print(f'  tot {r[0]:+.3f} ({r[1]:.2f},{r[2]:.2f}): via {r[3][0]:+.3f}'
          f' vs {fmt_it(r[3][1])}; stub {r[4]:+.3f}; '
          f'rejoinB7 {r[5][0]:+.3f} vs {fmt_it(r[5][1])}; '
          f'rejoinST {r[6][0]:+.3f} vs {fmt_it(r[6][1])}')

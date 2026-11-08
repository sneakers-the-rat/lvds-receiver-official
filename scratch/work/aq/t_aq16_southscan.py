"""t_aq16: scan SPI south via pair on exp235 statics with the
DBG_RX In2 re-lay (x88.875 -> x88.10) applied in the model.
MOSI via: x[88.60,88.90] y[-18.30,-17.30], stub vertical from via
to (x,-17.00). SCK via: x[89.30,90.10] y[-18.30,-16.95], stub
straight to (89.75,-16.95). d0.5 vias; full-pool pt/seg margin
(main gate semantics); pair mutual >= 0.70 centre distance.
"""
import sys, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
from t_ai_lib import load_items, pt_margin, seg_margin, in_box_pool

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp235.kicad_pcb')
items = load_items(b)
sr = set()
for (net, ax, ay, bx, by) in [
        ('DBG_RX', 89.125, -15.125, 88.875, -15.375),
        ('DBG_RX', 88.875, -15.375, 88.875, -19.875),
        ('DBG_RX', 88.875, -19.875, 88.875, -20.125)]:
    sr.add((net, round(ax, 3), round(ay, 3), round(bx, 3), round(by, 3)))
    sr.add((net, round(bx, 3), round(by, 3), round(ax, 3), round(ay, 3)))
statics = {li: [] for li in range(3)}
for li in range(3):
    for it in items[li]:
        if it[0] == 'seg':
            d = it[2]
            if (it[1], round(d[0], 3), round(d[1], 3), round(d[2], 3),
                    round(d[3], 3)) in sr:
                continue
        statics[li].append(it)
for a, c in [((89.125, -15.125), (88.100, -15.375)),
             ((88.100, -15.375), (88.100, -19.875)),
             ((88.100, -19.875), (88.875, -19.875))]:
    statics[1].append(('seg', 'DBG_RX',
                       (a[0], a[1], c[0], c[1], 0.1), 0.2))
pool = in_box_pool(statics, (84.0, 94.0, -21.0, -13.0), pad=1.2)
print(f'pool F={len(pool[0])} In2={len(pool[1])} B={len(pool[2])}')


def feas(net, vx, vy, stub_pts):
    worst = 9.9
    for l in range(3):
        m, _w = pt_margin(l, vx, vy, net, 0.25, pool[l])
        worst = min(worst, m)
    for (a, c) in stub_pts:
        m, _w = seg_margin(0, a, c, net, 0.1, pool[0], step=0.02)
        worst = min(worst, m)
    return worst


mosi = []
gx = 88.60
while gx <= 88.901:
    gy = -18.30
    while gy <= -17.299:
        m = feas('SPI_MOSI', gx, gy, [((gx, gy), (gx, -17.00))])
        if m >= 0.0:
            mosi.append((gx, gy, m))
        gy += 0.05
    gx += 0.05
print(f'MOSI feasible: {len(mosi)}')
for t in mosi[:40]:
    print(f'   ({t[0]:.2f},{t[1]:.2f}) worst {t[2]:+.3f}')
sck = []
gx = 89.30
while gx <= 90.101:
    gy = -18.30
    while gy <= -16.949:
        m = feas('SPI_SCK', gx, gy, [((gx, gy), (89.75, -16.95))])
        if m >= 0.0:
            sck.append((gx, gy, m))
        gy += 0.05
    gx += 0.05
print(f'SCK feasible: {len(sck)}')
for t in sck[:40]:
    print(f'   ({t[0]:.2f},{t[1]:.2f}) worst {t[2]:+.3f}')
pairs = []
for (mx, my, mm) in mosi:
    for (sx, sy, sm) in sck:
        d = ((mx - sx) ** 2 + (my - sy) ** 2) ** 0.5
        if d >= 0.70:
            pairs.append((min(mm, sm, d - 0.5 - 0.2), mx, my, sx, sy))
pairs.sort(reverse=True)
print(f'mutual pairs: {len(pairs)}')
for p in pairs[:12]:
    print(f'   pair min-margin {p[0]:+.3f}: MOSI ({p[1]:.2f},{p[2]:.2f})'
          f' SCK ({p[3]:.2f},{p[4]:.2f})')

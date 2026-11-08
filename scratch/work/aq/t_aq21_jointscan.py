"""t_aq21: joint scan for the SPI/DAC south triple on exp235.
Statics = exp235 minus: DAC_SYNC F run+diagonal, DBG_RX In2
vertical (re-laid x89.175 added), R16 pads (moved site added),
BOOT0 feed (re-laid added). Candidates (d0.5 vias):
- MOSI via (mx,my), stub vertical (mx,my)->(mx,-17.05), mx in
  [88.60,88.90] (stub must land on MOSI pad rect).
- SCK via (sx,sy), stub vertical (sx,sy)->(sx,-17.30), sx in
  [89.60,89.90].
- DAC rise via (dx,dy), F seg (dx,dy)->(90.25,-17.55); B approach
  vertical x=dx y[-19.6,dy] + horizontal (88.9,-19.6)->(dx,-19.6)
  gated vs B pool.
All gated vs full pools + mutually. Report best triples.
"""
import sys, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
from t_ai_lib import load_items, pt_margin, seg_margin, in_box_pool
from router import netclass

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp235.kicad_pcb')
items = load_items(b)
RIP = {
    ('DAC_SYNC', 90.250, -17.550, 89.300, -18.150),
    ('DAC_SYNC', 89.300, -18.150, 87.300, -18.150),
    ('DBG_RX', 89.125, -15.125, 88.875, -15.375),
    ('DBG_RX', 88.875, -15.375, 88.875, -19.875),
    ('DBG_RX', 88.875, -19.875, 88.875, -20.125),
    ('BOOT0', 88.925, -19.000, 88.675, -19.000),
    ('BOOT0', 88.675, -19.000, 88.625, -18.875),
    ('BOOT0', 88.625, -18.875, 87.375, -18.875),
}
sr = set()
for (net, ax, ay, bx, by) in RIP:
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
        if it[0] == 'pad' and abs(it[2][1] + 19.000) < 0.01 and \
                (abs(it[2][0] - 88.925) < 0.01 or
                 abs(it[2][0] - 90.575) < 0.01):
            continue
        statics[li].append(it)


def segit(net, a, c, w=0.2):
    return ('seg', net, (a[0], a[1], c[0], c[1], w / 2), netclass(net)[1])


statics[1].append(segit('DBG_RX', (89.125, -15.125), (89.175, -15.375)))
statics[1].append(segit('DBG_RX', (89.175, -15.375), (89.175, -19.875)))
statics[1].append(segit('DBG_RX', (89.175, -19.875), (88.875, -19.875)))
statics[0].append(('pad', 'BOOT0', (85.475, -21.3, 0.4, 0.475, 0.0), 0.2))
statics[0].append(('pad', 'GND', (87.125, -21.3, 0.4, 0.475, 0.0), 0.2))
statics[0].append(segit('BOOT0', (87.375, -18.875), (86.6, -20.2)))
statics[0].append(segit('BOOT0', (86.6, -20.2), (85.475, -21.3)))
pool = in_box_pool(statics, (84.0, 94.0, -21.5, -13.0), pad=1.2)
print(f'pool F={len(pool[0])} In2={len(pool[1])} B={len(pool[2])}')


def via_m(net, x, y, extra=()):
    m = 9.9
    for l in range(3):
        mm, _ = pt_margin(l, x, y, net, 0.25, pool[l] + list(extra))
        m = min(m, mm)
    return m


def seg_m(net, a, c, li, extra=()):
    mm, _ = seg_margin(li, a, c, net, 0.1, pool[li] + list(extra),
                       step=0.02)
    return mm


def grid(x0, x1, y0, y1, st=0.05):
    xs = []
    x = x0
    while x <= x1 + 1e-9:
        xs.append(round(x, 3))
        x += st
    ys = []
    y = y0
    while y <= y1 + 1e-9:
        ys.append(round(y, 3))
        y += st
    return xs, ys


mosi = []
xs, ys = grid(88.60, 88.90, -18.60, -17.55)
for x in xs:
    for y in ys:
        m = via_m('SPI_MOSI', x, y)
        m = min(m, seg_m('SPI_MOSI', (x, y), (x, -17.05), 0))
        if m >= 0:
            mosi.append((x, y, m))
print(f'MOSI feasible: {len(mosi)}')
sck = []
xs, ys = grid(89.60, 89.90, -18.80, -17.55)
for x in xs:
    for y in ys:
        m = via_m('SPI_SCK', x, y)
        m = min(m, seg_m('SPI_SCK', (x, y), (x, -17.30), 0))
        if m >= 0:
            sck.append((x, y, m))
print(f'SCK feasible: {len(sck)}')
dac = []
xs, ys = grid(88.90, 90.30, -19.30, -17.60)
for x in xs:
    for y in ys:
        m = via_m('DAC_SYNC', x, y)
        m = min(m, seg_m('DAC_SYNC', (x, y), (90.25, -17.55), 0))
        m = min(m, seg_m('DAC_SYNC', (x, -19.6), (x, y), 2))
        m = min(m, seg_m('DAC_SYNC', (88.9, -19.6), (x, -19.6), 2))
        if m >= 0:
            dac.append((x, y, m))
print(f'DAC feasible: {len(dac)}')
for nm, lst in (('MOSI', mosi), ('SCK', sck), ('DAC', dac)):
    lst.sort(key=lambda t: -t[2])
    for t in lst[:6]:
        print(f'   {nm} ({t[0]:.2f},{t[1]:.2f}) worst {t[2]:+.3f}')

best = []
for (mx, my, mm) in mosi:
    mv = ('via', 'SPI_MOSI', (mx, my, 0.25), 0.2)
    ms = segit('SPI_MOSI', (mx, my), (mx, -17.05))
    for (sx, sy, sm) in sck:
        d = ((mx - sx) ** 2 + (my - sy) ** 2) ** 0.5
        if d < 0.70:
            continue
        m2 = min(mm, sm, d - 0.7)
        m2 = min(m2, seg_m('SPI_SCK', (sx, sy), (sx, -17.30), 0,
                           extra=(ms,)))
        sv = ('via', 'SPI_SCK', (sx, sy, 0.25), 0.2)
        m2 = min(m2, via_m('SPI_SCK', sx, sy, extra=(mv,)))
        if m2 < 0:
            continue
        ss = segit('SPI_SCK', (sx, sy), (sx, -17.30))
        for (dx, dy, dm) in dac:
            d1 = ((mx - dx) ** 2 + (my - dy) ** 2) ** 0.5
            d2 = ((sx - dx) ** 2 + (sy - dy) ** 2) ** 0.5
            if d1 < 0.70 or d2 < 0.70:
                continue
            m3 = min(m2, dm, d1 - 0.7, d2 - 0.7)
            m3 = min(m3, seg_m('DAC_SYNC', (dx, dy), (90.25, -17.55),
                               0, extra=(ms, ss)))
            dv = ('via', 'DAC_SYNC', (dx, dy, 0.25), 0.2)
            m3 = min(m3, via_m('SPI_MOSI', mx, my, extra=(dv,)))
            m3 = min(m3, via_m('SPI_SCK', sx, sy, extra=(dv,)))
            m3 = min(m3, seg_m('SPI_MOSI', (mx, my), (mx, -17.05), 0,
                               extra=(segit('DAC_SYNC', (dx, dy),
                                            (90.25, -17.55)),)))
            m3 = min(m3, seg_m('SPI_SCK', (sx, sy), (sx, -17.30), 0,
                               extra=(segit('DAC_SYNC', (dx, dy),
                                            (90.25, -17.55)),)))
            if m3 >= 0:
                best.append((m3, mx, my, sx, sy, dx, dy))
best.sort(reverse=True)
print(f'triples: {len(best)}')
for t in best[:10]:
    print(f'   min {t[0]:+.3f}: MOSI ({t[1]:.2f},{t[2]:.2f}) '
          f'SCK ({t[3]:.2f},{t[4]:.2f}) DAC ({t[5]:.2f},{t[6]:.2f})')

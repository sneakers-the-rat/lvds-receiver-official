"""t_aq14: SPI prep build v3 (exp235 -> exp236prep, NOT a pass board).

U8 end = t_aq7 scan scenario S2 + two re-lays:
- rip +3V3D w0.6 trunk tip (6 F segs (73.875,6.875)..(72.2,5.75));
  re-lay on F at w0.5: (73.875,6.875)->(73.0,6.3)->(72.5,5.9)
  ->(72.2,5.75) (kept feed joint).
- rip DAC_SYNC via (72.125,6.875), F feed+stub segs, 2 In2 head
  segs (braid kept from (72.625,6.375)); DAC escape re-laid:
  F stub (70.7,7.25)->(70.7,7.8) + via (70.7,7.8) d0.5 (B margin
  vs +3V3A y8.625 trunk +0.025 at power pair).
- SPI_SCK via (72.05,7.10) + F stub; SPI_MOSI via (71.90,6.40)
  + F stub (t_aq7 best mutual pair, min margin +0.026).
South end: SWCLK via ->(90.75,-18.60) + F stub + B tail re-lay;
DAC_SYNC F arrival re-laid at y-18.45; SPI_MOSI via (88.25,-17.80)
+ stub; SPI_SCK via (89.65,-17.85) + stub.
All adds gated mutually in the exact model before build.
"""
import sys, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
from t_ai_lib import (load_items, pt_margin, seg_margin, in_box_pool,
                      fmt_it)
from router import netclass

SRC = 'hw/pdlvds_rx.exp235.kicad_pcb'
DST = 'hw/pdlvds_rx.exp236prep.kicad_pcb'
LAY = [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
MM = lambda v: int(round(v * 1e6))  # noqa: E731
BIGBOX = (66.0, 96.0, -25.0, 10.0)  # (x0,x1,y0,y1)

SEG_RIPS = [
    ('+3V3D', 73.875, 6.875, 73.625, 6.625),
    ('+3V3D', 73.625, 6.625, 73.375, 6.625),
    ('+3V3D', 73.375, 6.625, 73.125, 6.375),
    ('+3V3D', 73.125, 6.375, 72.875, 6.375),
    ('+3V3D', 72.875, 6.375, 72.625, 6.125),
    ('+3V3D', 72.625, 6.125, 72.200, 5.750),
    ('DAC_SYNC', 70.700, 7.250, 71.700, 7.250),
    ('DAC_SYNC', 71.700, 7.250, 72.125, 6.875),
    ('DAC_SYNC', 72.125, 6.875, 72.375, 6.625),
    ('DAC_SYNC', 72.375, 6.625, 72.625, 6.375),
    ('DAC_SYNC', 90.250, -17.550, 89.300, -18.150),
    ('DAC_SYNC', 89.300, -18.150, 87.300, -18.150),
    ('SWCLK', 90.750, -17.600, 90.550, -18.050),
    ('SWCLK', 90.550, -18.050, 89.900, -23.000),
]
VIA_RIPS = [('DAC_SYNC', 72.125, 6.875), ('SWCLK', 90.550, -18.050)]


def seg(net, li, a, c, w):
    return (li, ('seg', net, (a[0], a[1], c[0], c[1], w / 2),
                 netclass(net)[1]))


def via(net, x, y, d=0.5):
    return ('via', net, (x, y, d / 2), netclass(net)[1])


ADDS = [
    seg('+3V3D', 0, (73.875, 6.875), (73.000, 6.300), 0.5),
    seg('+3V3D', 0, (73.000, 6.300), (72.500, 5.900), 0.5),
    seg('+3V3D', 0, (72.500, 5.900), (72.200, 5.750), 0.5),
    seg('DAC_SYNC', 0, (70.700, 7.250), (70.700, 7.800), 0.2),
    via('DAC_SYNC', 70.700, 7.800),
    via('SPI_SCK', 72.050, 7.100),
    seg('SPI_SCK', 0, (71.425, 6.750), (72.050, 7.100), 0.2),
    via('SPI_MOSI', 71.900, 6.400),
    seg('SPI_MOSI', 0, (71.425, 6.250), (71.900, 6.400), 0.2),
    seg('SWCLK', 0, (90.750, -17.600), (90.750, -18.600), 0.2),
    via('SWCLK', 90.750, -18.600),
    seg('SWCLK', 2, (90.750, -18.600), (89.900, -23.000), 0.2),
    seg('DAC_SYNC', 0, (87.300, -18.150), (88.000, -18.450), 0.2),
    seg('DAC_SYNC', 0, (88.000, -18.450), (90.150, -18.450), 0.2),
    seg('DAC_SYNC', 0, (90.150, -18.450), (90.250, -17.550), 0.2),
    via('SPI_MOSI', 88.250, -17.800),
    seg('SPI_MOSI', 0, (88.250, -17.800), (88.700, -17.500), 0.2),
    seg('SPI_MOSI', 0, (88.700, -17.500), (88.750, -17.000), 0.2),
    via('SPI_SCK', 89.650, -17.850),
    seg('SPI_SCK', 0, (89.650, -17.850), (89.750, -16.900), 0.2),
]

b = pcbnew.LoadBoard(SRC)
codes = {}
for n in ('+3V3D', 'DAC_SYNC', 'SWCLK', 'SPI_SCK', 'SPI_MOSI'):
    codes[n] = b.GetNetcodeFromNetname(n)
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
print(f'model rips: {nrip} (expect 14 segs + 2 vias x3 = 20)')
assert nrip == 20, nrip

pool = in_box_pool(statics, BIGBOX, pad=1.2)


def _inpool(li, kind, net, x, y):
    for it in pool[li]:
        if it[0] == kind and it[1] == net and abs(it[2][0] - x) < 0.01 \
                and abs(it[2][1] - y) < 0.01:
            return True
    return False


assert _inpool(2, 'seg', '+3V3A', 75.625, 8.625), 'POOL MISS +3V3A B trunk'
assert _inpool(1, 'seg', 'DBG_RX', 88.875, -19.875), 'POOL MISS DBG_RX'
assert _inpool(0, 'pad', 'GND', 90.575, -19.000), 'POOL MISS R16 GND pad'
assert _inpool(0, 'pad', 'DAC_SYNC', 70.700, 7.250), 'POOL MISS DAC pad'
print(f'pool: F={len(pool[0])} In2={len(pool[1])} B={len(pool[2])}')

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

victims = []
for t in list(b.GetTracks()):
    net = t.GetNetname()
    if isinstance(t, pcbnew.PCB_VIA):
        p = t.GetPosition()
        if (net, round(p.x / 1e6, 3), round(p.y / 1e6, 3)) in vr:
            victims.append(('via', net, p.x / 1e6, p.y / 1e6))
            b.Remove(t)
    else:
        s = t.GetStart()
        e = t.GetEnd()
        key = (net, round(s.x / 1e6, 3), round(s.y / 1e6, 3),
               round(e.x / 1e6, 3), round(e.y / 1e6, 3))
        if key in sr:
            victims.append(('seg', net, key[1:]))
            b.Remove(t)
print(f'rip victims: {len(victims)} (expect 16)')
for v in victims:
    print('   ', v)
assert len(victims) == 16


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

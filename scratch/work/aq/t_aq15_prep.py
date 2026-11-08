"""t_aq15: SPI prep build v4 (exp235 -> exp236prep, NOT a pass board).

U8 end = t_aq7 scan scenario S2 + two re-lays:
- rip +3V3D w0.6 trunk tip (6 F segs); re-lay F w0.5:
  (73.875,6.875)->(73.0,6.3)->(72.5,5.9)->(72.2,5.75).
- rip DAC_SYNC via (72.125,6.875) + F feed/stub + 2 In2 head segs
  (braid kept from (72.625,6.375)); escape re-laid: F stub
  (70.7,7.25)->(70.7,7.8) + via (70.7,7.8) d0.5.
- SPI_SCK via (72.05,7.10) + stub; SPI_MOSI via (71.90,6.40)
  + stub (t_aq7 best mutual pair).
South end (DAC_SYNC + SWCLK copper UNTOUCHED):
- DBG_RX In2 vertical re-laid x88.875 -> x88.10 (3 segs ripped,
  3 added; joints at (89.125,-15.125) and (88.875,-19.875)).
  Gated against In2 statics EXCLUDING pads: U6/R16 pads are SMD
  (F-only copper); KiCad DRC referees the built board.
- SPI_MOSI via (88.75,-17.85) + vertical F stub to pad;
  SPI_SCK via (89.65,-17.85) + F stub (vs DAC diagonal +0.213).
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
    ('DBG_RX', 89.125, -15.125, 88.875, -15.375),
    ('DBG_RX', 88.875, -15.375, 88.875, -19.875),
    ('DBG_RX', 88.875, -19.875, 88.875, -20.125),
    ('DAC_SYNC', 90.250, -17.550, 89.300, -18.150),
    ('DAC_SYNC', 89.300, -18.150, 87.300, -18.150),
    ('BOOT0', 88.925, -19.000, 88.675, -19.000),
    ('BOOT0', 88.675, -19.000, 88.625, -18.875),
    ('BOOT0', 88.625, -18.875, 87.375, -18.875),
]
VIA_RIPS = [('DAC_SYNC', 72.125, 6.875)]


def seg(net, li, a, c, w):
    return (li, ('seg', net, (a[0], a[1], c[0], c[1], w / 2),
                 netclass(net)[1]))


def via(net, x, y, d=0.5):
    return ('via', net, (x, y, d / 2), netclass(net)[1])


ADDS = [
    seg('+3V3D', 0, (73.875, 6.875), (73.000, 6.300), 0.5),
    seg('+3V3D', 0, (73.000, 6.300), (72.500, 5.900), 0.5),
    seg('+3V3D', 0, (72.500, 5.900), (72.200, 5.750), 0.2),
    seg('DAC_SYNC', 0, (70.700, 7.250), (70.700, 7.800), 0.2),
    via('DAC_SYNC', 70.700, 7.800),
    via('SPI_SCK', 72.050, 7.100),
    seg('SPI_SCK', 0, (71.425, 6.750), (72.050, 7.100), 0.2),
    via('SPI_MOSI', 71.850, 6.350),
    seg('SPI_MOSI', 0, (71.425, 6.250), (71.850, 6.350), 0.2),
    via('SPI_MOSI', 88.600, -17.900),
    seg('SPI_MOSI', 0, (88.600, -17.900), (88.800, -17.050), 0.2),
    via('SPI_SCK', 89.800, -19.050),
    seg('SPI_SCK', 0, (89.800, -19.050), (89.150, -18.700), 0.2),
    seg('SPI_SCK', 0, (89.150, -18.700), (89.150, -17.900), 0.2),
    seg('SPI_SCK', 0, (89.150, -17.900), (89.520, -17.720), 0.2),
    seg('SPI_SCK', 0, (89.520, -17.720), (89.750, -17.480), 0.2),
    seg('SPI_SCK', 0, (89.750, -17.480), (89.750, -17.300), 0.2),
    seg('DAC_SYNC', 2, (87.300, -18.150), (88.400, -18.700), 0.2),
    seg('DAC_SYNC', 2, (88.400, -18.700), (88.900, -19.350), 0.2),
    seg('DAC_SYNC', 2, (88.900, -19.350), (89.200, -19.350), 0.2),
    seg('DAC_SYNC', 2, (89.200, -19.350), (89.200, -18.500), 0.2),
    seg('DAC_SYNC', 2, (89.200, -18.500), (89.750, -18.300), 0.2),
    via('DAC_SYNC', 89.750, -18.300),
    seg('DAC_SYNC', 0, (89.750, -18.300), (89.950, -17.850), 0.2),
    seg('DAC_SYNC', 0, (89.950, -17.850), (90.250, -17.550), 0.2),
    seg('BOOT0', 0, (87.375, -18.875), (86.600, -20.200), 0.2),
    seg('BOOT0', 0, (86.600, -20.200), (85.475, -21.300), 0.2),
    seg('GND', 0, (87.125, -21.300), (87.125, -22.750), 0.2),
    via('GND', 87.125, -22.750),
]
DBG_ADDS = [
    seg('DBG_RX', 1, (89.125, -15.125), (89.175, -15.375), 0.2),
    seg('DBG_RX', 1, (89.175, -15.375), (89.175, -19.875), 0.2),
    seg('DBG_RX', 1, (89.175, -19.875), (88.875, -19.875), 0.2),
]

b = pcbnew.LoadBoard(SRC)
R16FP = None
for fp in b.GetFootprints():
    if fp.GetReference() == 'R16':
        R16FP = fp
        break
assert R16FP is not None, 'R16 not found at load'
codes = {}
for n in ('+3V3D', 'DAC_SYNC', 'SPI_SCK', 'SPI_MOSI', 'DBG_RX',
          'BOOT0', 'GND'):
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
print(f'model rips: {nrip} (expect 18 segs + 1 via x3 = 21)')
assert nrip == 21, nrip

# R16 moves (89.75,-19.0) -> (86.3,-21.3): drop its old pads from
# statics, inject the new pads as F fences.
for li in range(3):
    statics[li] = [it for it in statics[li]
                   if not (it[0] == 'pad' and
                           (abs(it[2][0] - 88.925) < 0.01 or
                            abs(it[2][0] - 90.575) < 0.01) and
                           abs(it[2][1] + 19.000) < 0.01)]
statics[0].append(('pad', 'BOOT0', (85.475, -21.300, 0.4, 0.475, 0.0),
                   0.2))
statics[0].append(('pad', 'GND', (87.125, -21.300, 0.4, 0.475, 0.0),
                   0.2))

pool = in_box_pool(statics, BIGBOX, pad=1.2)


def _inpool(li, kind, net, x, y):
    for it in pool[li]:
        if it[0] == kind and it[1] == net and abs(it[2][0] - x) < 0.01 \
                and abs(it[2][1] - y) < 0.01:
            return True
    return False


assert _inpool(2, 'seg', '+3V3A', 75.625, 8.625), 'POOL MISS +3V3A B trunk'
assert _inpool(0, 'seg', 'BOOT0', 87.375, -18.875), 'POOL MISS BOOT0 run'
assert _inpool(0, 'pad', 'DAC_SYNC', 70.700, 7.250), 'POOL MISS DAC pad'
print(f'pool: F={len(pool[0])} In2={len(pool[1])} B={len(pool[2])}')


def gate(adds, poolmap, label):
    worst = 9.9
    worst_desc = None
    for idx, a in enumerate(adds):
        plist = [list(poolmap[l]) for l in range(3)]
        for prev in adds[:idx]:
            if isinstance(prev[0], int):
                plist[prev[0]].append(prev[1])
            else:
                for l in range(3):
                    plist[l].append(prev)
        if isinstance(a[0], int):
            li, it = a
            m, w = seg_margin(li, (it[2][0], it[2][1]),
                              (it[2][2], it[2][3]), it[1], it[2][4],
                              plist[li], step=0.01)
            if m < worst:
                worst, worst_desc = m, (fmt_it(it), li, fmt_it(w))
        else:
            for l in range(3):
                m, w = pt_margin(l, a[2][0], a[2][1], a[1], a[2][2],
                                 plist[l])
                if m < worst:
                    worst, worst_desc = m, (fmt_it(a), l, fmt_it(w))
    print(f'{label}: worst {worst:+.4f} at {worst_desc}')
    return worst


w1 = gate(ADDS, pool, 'main gate')
assert w1 >= -0.001, 'MAIN GATE FAIL'
# DBG_RX re-lay: In2 pool minus pads (SMD pads are F-only copper)
pool_nopad = {l: [it for it in pool[l] if it[0] != 'pad']
              for l in range(3)}
# SPI vias are real In2 fences for the DBG segs: add them in
for a in ADDS:
    if not isinstance(a[0], int):
        for l in range(3):
            pool_nopad[l].append(a)
w2 = gate(DBG_ADDS, pool_nopad, 'DBG_RX gate (In2, pads excluded)')
assert w2 >= -0.001, 'DBG GATE FAIL'

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
print(f'rip victims: {len(victims)} (expect 19)')
for v in victims:
    print('   ', v)
assert len(victims) == 19


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


for a in ADDS + DBG_ADDS:
    if isinstance(a[0], int):
        li, it = a
        d = it[2]
        add_track(it[1], li, (d[0], d[1]), (d[2], d[3]), d[4] * 2)
    else:
        add_via(a[1], a[2][0], a[2][1], a[2][2] * 2)

R16FP.SetPosition(pcbnew.VECTOR2I(MM(86.3), MM(-21.3)))
print('R16 moved to (86.3,-21.3)')

filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())
b.Save(DST)
print('saved', DST)

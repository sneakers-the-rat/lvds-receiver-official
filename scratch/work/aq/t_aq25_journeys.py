"""t_aq25 v2: journeys on exp236prep -> exp236.
Rips: prep's +3V3D tip (3 F segs, re-laid north), prep's DAC detour
(5 B segs, replaced by the north-approach detour).
DAC_SYNC: In2 hop (70.7,7.8) west-around to braid joint (73.375,5.625);
detour B (87.3,-18.15)->(88.6,-16.6)->(89.85,-17.5)->via (89.75,-18.3).
SPI_SCK: F dive via (73.95,4.75), B to via (77.9,2.2), In2 channel run
(sum ~80.2), via (85.0,-5.5), B south-west approach to via (89.8,-19.05).
SPI_MOSI: F to via (73.3,4.1), B west of D7 wall, via (77.9,-3.0), In2
crossing, via (79.6,-4.4), B SW of DAC wall, south pocket weave into
via (88.6,-17.9). All items gated vs full pool + prior adds."""
import sys, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
from t_ai_lib import load_items, pt_margin, seg_margin, fmt_it, apply_rip

SRC = 'hw/pdlvds_rx.exp236prep.kicad_pcb'
OUT = 'hw/pdlvds_rx.exp236.kicad_pcb'
MM = pcbnew.FromMM
LAY = {0: pcbnew.F_Cu, 1: pcbnew.In2_Cu, 2: pcbnew.B_Cu}

RIPS = [
    ('seg', '+3V3D', 0, 73.875, 6.875, 73.000, 6.300),
    ('seg', '+3V3D', 0, 73.000, 6.300, 72.500, 5.900),
    ('seg', '+3V3D', 0, 72.500, 5.900, 72.200, 5.750),
    ('seg', 'DAC_SYNC', 2, 87.300, -18.150, 88.400, -18.700),
    ('seg', 'DAC_SYNC', 2, 88.400, -18.700, 88.900, -19.350),
    ('seg', 'DAC_SYNC', 2, 88.900, -19.350, 89.200, -19.350),
    ('seg', 'DAC_SYNC', 2, 89.200, -19.350, 89.200, -18.500),
    ('seg', 'DAC_SYNC', 2, 89.200, -18.500, 89.750, -18.300),
]
# (net, layer, ax, ay, bx, by, width)
SEGS = [
    ('+3V3D', 0, 73.875, 6.875, 73.200, 6.150, 0.5),
    ('+3V3D', 0, 73.200, 6.150, 72.750, 5.800, 0.5),
    ('+3V3D', 0, 72.750, 5.800, 72.200, 5.750, 0.2),
    ('DAC_SYNC', 1, 70.700, 7.800, 70.200, 6.900, 0.2),
    ('DAC_SYNC', 1, 70.200, 6.900, 70.900, 5.900, 0.2),
    ('DAC_SYNC', 1, 70.900, 5.900, 72.300, 5.500, 0.2),
    ('DAC_SYNC', 1, 72.300, 5.500, 73.375, 5.625, 0.2),
    ('DAC_SYNC', 2, 87.300, -18.150, 88.600, -16.600, 0.2),
    ('DAC_SYNC', 2, 88.600, -16.600, 89.850, -17.500, 0.2),
    ('DAC_SYNC', 2, 89.850, -17.500, 89.750, -18.300, 0.2),
    ('SPI_SCK', 0, 72.050, 7.100, 73.300, 5.200, 0.2),
    ('SPI_SCK', 0, 73.300, 5.200, 73.950, 4.750, 0.2),
    ('SPI_SCK', 2, 73.950, 4.750, 76.800, 3.000, 0.2),
    ('SPI_SCK', 2, 76.800, 3.000, 77.900, 2.200, 0.2),
    ('SPI_SCK', 1, 77.900, 2.200, 79.500, 0.600, 0.2),
    ('SPI_SCK', 1, 79.500, 0.600, 81.500, -1.200, 0.2),
    ('SPI_SCK', 1, 81.500, -1.200, 84.300, -4.300, 0.2),
    ('SPI_SCK', 2, 85.000, -5.500, 84.600, -9.000, 0.2),
    ('SPI_SCK', 2, 84.600, -9.000, 85.300, -13.500, 0.2),
    ('SPI_SCK', 2, 85.300, -13.500, 85.900, -16.400, 0.2),
    ('SPI_SCK', 2, 85.900, -16.400, 87.000, -18.900, 0.2),
    ('SPI_SCK', 2, 87.000, -18.900, 89.000, -19.700, 0.2),
    ('SPI_SCK', 2, 89.000, -19.700, 89.800, -19.050, 0.2),
    ('SPI_MOSI', 0, 71.850, 6.350, 72.450, 5.150, 0.2),
    ('SPI_MOSI', 0, 72.450, 5.150, 73.300, 4.100, 0.2),
    ('SPI_MOSI', 2, 73.300, 4.100, 75.400, 3.550, 0.2),
    ('SPI_MOSI', 2, 75.400, 3.550, 77.600, 1.500, 0.2),
    ('SPI_MOSI', 2, 77.600, 1.500, 77.900, -3.000, 0.2),
    ('SPI_MOSI', 1, 77.900, -3.000, 79.600, -4.400, 0.2),
    ('SPI_MOSI', 2, 79.600, -4.400, 82.000, -5.600, 0.2),
    ('SPI_MOSI', 2, 82.000, -5.600, 86.500, -9.300, 0.2),
    ('SPI_MOSI', 2, 86.500, -9.300, 87.500, -12.500, 0.2),
    ('SPI_MOSI', 2, 87.500, -12.500, 87.300, -16.000, 0.2),
    ('SPI_MOSI', 2, 87.300, -16.000, 86.600, -18.600, 0.2),
    ('SPI_MOSI', 2, 86.600, -18.600, 87.800, -18.750, 0.2),
    ('SPI_MOSI', 2, 87.800, -18.750, 88.600, -17.900, 0.2),
]
VIAS = [('SPI_SCK', 73.950, 4.750), ('SPI_SCK', 77.900, 2.200),
        ('SPI_SCK', 85.000, -5.500), ('SPI_MOSI', 73.300, 4.100),
        ('SPI_MOSI', 77.900, -3.000), ('SPI_MOSI', 79.600, -4.400)]

board = pcbnew.LoadBoard(SRC)
items = load_items(board)
MODEL_RIPS = [('seg', '+3V3D', 73.000, 6.300), ('seg', '+3V3D', 72.500, 5.900),
              ('seg', 'DAC_SYNC', 88.400, -18.700),
              ('seg', 'DAC_SYNC', 89.200, -19.350),
              ('seg', 'DAC_SYNC', 89.200, -18.500)]
statics, nrip = apply_rip({l: list(items[l]) for l in range(3)}, MODEL_RIPS)
assert nrip == 8, f'model rips {nrip} != 8'
pool = {l: list(statics[l]) for l in range(3)}

def segit(net, a, b, w):
    return ('seg', net, (a[0], a[1], b[0], b[1], w / 2), 0.2)
def viait(net, x, y):
    return ('via', net, (x, y, 0.25), 0.2)

fails = 0
for (net, x, y) in VIAS:
    it = viait(net, x, y)
    for l in range(3):
        m, w = pt_margin(l, x, y, net, 0.25, pool[l])
        print(f'  via {net} ({x},{y}) L{l}: {m:+.3f} vs {fmt_it(w)}')
        if m < -0.001:
            fails += 1
        pool[l].append(it)
for (net, li, ax, ay, bx, by, wd) in SEGS:
    it = segit(net, (ax, ay), (bx, by), wd)
    m, w = seg_margin(li, (ax, ay), (bx, by), net, wd / 2, pool[li], step=0.04)
    print(f'  seg {net} L{li} ({ax},{ay})->({bx},{by}) w{wd}: {m:+.3f} vs {fmt_it(w)}')
    if m < -0.001:
        fails += 1
    pool[li].append(it)
assert fails == 0, f'{fails} GATE FAILURES'
print('ALL GATES PASS')

# ---- build ----
codes = {}
for n in ('+3V3D', 'DAC_SYNC', 'SPI_SCK', 'SPI_MOSI'):
    codes[n] = board.GetNetcodeFromNetname(n)
tracks = list(board.GetTracks())
victims = []
for spec in RIPS:
    _, net, li, ax, ay, bx, by = spec
    for t in tracks:
        if isinstance(t, pcbnew.PCB_VIA) or t.GetNetname() != net:
            continue
        if LAY[li] != t.GetLayer():
            continue
        a = pcbnew.ToMM(t.GetStart()); b = pcbnew.ToMM(t.GetEnd())
        key = (round(a[0], 3), round(a[1], 3), round(b[0], 3), round(b[1], 3))
        want = {(round(ax, 3), round(ay, 3), round(bx, 3), round(by, 3)),
                (round(bx, 3), round(by, 3), round(ax, 3), round(ay, 3))}
        if key in want and t not in victims:
            victims.append(t)
assert len(victims) == len(RIPS), f'rip victims {len(victims)} != {len(RIPS)}'
for t in victims:
    board.Remove(t)
print(f'ripped {len(victims)}')
for (net, x, y) in VIAS:
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    v.SetWidth(MM(0.5)); v.SetDrill(MM(0.3))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNetCode(codes[net])
    board.Add(v)
for (net, li, ax, ay, bx, by, wd) in SEGS:
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MM(ax), MM(ay)))
    t.SetEnd(pcbnew.VECTOR2I(MM(bx), MM(by)))
    t.SetWidth(MM(wd)); t.SetLayer(LAY[li]); t.SetNetCode(codes[net])
    board.Add(t)
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
board.Save(OUT)
print('saved', OUT)

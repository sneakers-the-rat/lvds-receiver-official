"""t_aq39: build exp236 from exp236prep.
- Rips prep's DAC detour (5 B segs); adds the north-approach detour
  (3 B segs, hand-gated in t_aq25 v2 analysis).
- Applies router plans: DAC hop, SPI_SCK, SPI_MOSI (JSON files of
  ['seg',net,li,ax,ay,bx,by,w] / ['via',net,x,y] entries).
- Re-gates EVERY add vs statics + prior adds; builds; refill; save.
Usage: t_aq39_build.py sck_plan.json mosi_plan.json"""
import sys, wx, json
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
from t_ai_lib import load_items, pt_margin, seg_margin, fmt_it, apply_rip

SRC = 'hw/pdlvds_rx.exp236prep3.kicad_pcb'
OUT = 'hw/pdlvds_rx.exp236.kicad_pcb'
MM = pcbnew.FromMM
LAY = {0: pcbnew.F_Cu, 1: pcbnew.In2_Cu, 2: pcbnew.B_Cu}

RIPS = [
    ('seg', 'DAC_SYNC', 2, 87.300, -18.150, 88.400, -18.700),
    ('seg', 'DAC_SYNC', 2, 88.400, -18.700, 88.900, -19.350),
    ('seg', 'DAC_SYNC', 2, 88.900, -19.350, 89.200, -19.350),
    ('seg', 'DAC_SYNC', 2, 89.200, -19.350, 89.200, -18.500),
    ('seg', 'DAC_SYNC', 2, 89.200, -18.500, 89.750, -18.300),
]
MODEL_RIPS = [
    ('via', 'SPI_SCK', 72.05, 7.1),
    ('seg', 'SPI_SCK', 72.05, 7.1),
    ('via', 'SPI_MOSI', 71.85, 6.35),
    ('seg', 'SPI_MOSI', 71.85, 6.35),('seg', 'DAC_SYNC', 88.400, -18.700), ('seg', 'DAC_SYNC', 89.200, -19.350),
              ('seg', 'DAC_SYNC', 89.200, -18.500),
              ('seg', 'DAC_SYNC', 72.875, 6.125), ('seg', 'DAC_SYNC', 73.125, 5.875),
              ('seg', 'DAC_SYNC', 73.375, 5.625), ('seg', 'DAC_SYNC', 73.625, 5.375),
              ('seg', 'DAC_SYNC', 73.875, 5.125), ('seg', 'DAC_SYNC', 74.125, 4.875),
              ('seg', 'DAC_SYNC', 74.375, 4.625), ('seg', 'DAC_SYNC', 74.625, 4.375),
              ('seg', 'DAC_SYNC', 74.875, 4.125), ('seg', 'DAC_SYNC', 75.125, 3.875),
              ('seg', 'DAC_SYNC', 75.375, 3.625), ('seg', 'DAC_SYNC', 75.625, 3.375),
              ('seg', 'DAC_SYNC', 75.875, 3.125), ('seg', 'DAC_SYNC', 75.875, 2.125),
              ('seg', 'DAC_SYNC', 76.125, 1.875)]
DETOUR = [('seg', 'DAC_SYNC', 2, 87.300, -18.150, 88.600, -16.600, 0.2),
          ('seg', 'DAC_SYNC', 2, 88.600, -16.600, 89.850, -17.500, 0.2),
          ('seg', 'DAC_SYNC', 2, 89.850, -17.500, 89.750, -18.300, 0.2)]
DAC_HOP = [('seg', 'DAC_SYNC', 1, 70.700, 7.800, 71.375, 5.875, 0.2),
           ('seg', 'DAC_SYNC', 1, 71.375, 5.875, 75.500, 3.500, 0.2),
           ('seg', 'DAC_SYNC', 1, 75.500, 3.500, 76.550, 1.450, 0.2)]

plans = list(DETOUR) + list(DAC_HOP)
for f in sys.argv[1:]:
    for e in json.load(open(f)):
        plans.append(tuple(e))

board = pcbnew.LoadBoard(SRC)
items = load_items(board)
statics, nrip = apply_rip({l: list(items[l]) for l in range(3)}, MODEL_RIPS)
assert nrip == 29, f'model rips {nrip} != 29'
pool = {l: list(statics[l]) for l in range(3)}

fails = 0
for e in plans:
    if e[0] == 'via':
        _, net, x, y = e
        it = ('via', net, (x, y, 0.25), 0.2)
        for l in range(3):
            m, w = pt_margin(l, x, y, net, 0.25, pool[l])
            print(f'  via {net} ({x},{y}) L{l}: {m:+.3f} vs {fmt_it(w)}')
            if m < -0.001:
                fails += 1
            pool[l].append(it)
    else:
        _, net, li, ax, ay, bx, by, wd = e
        it = ('seg', net, (ax, ay, bx, by, wd / 2), 0.2)
        m, w = seg_margin(li, (ax, ay), (bx, by), net, wd / 2, pool[li],
                          step=0.04)
        print(f'  seg {net} L{li} ({ax},{ay})->({bx},{by}): {m:+.3f} '
              f'vs {fmt_it(w)}')
        if m < -0.001:
            fails += 1
        pool[li].append(it)
assert fails == 0, f'{fails} GATE FAILURES'
print(f'ALL {len(plans)} PLAN ITEMS GATE-CLEAN')

codes = {}
for n in ('DAC_SYNC', 'SPI_SCK', 'SPI_MOSI'):
    codes[n] = board.GetNetcodeFromNetname(n)
BOARD_SEG_RIPS = list(RIPS) + [
    ('seg', 'DAC_SYNC', 1, 72.625, 6.375, 72.875, 6.125),
    ('seg', 'DAC_SYNC', 1, 72.875, 6.125, 73.125, 5.875),
    ('seg', 'DAC_SYNC', 1, 73.125, 5.875, 73.375, 5.625),
    ('seg', 'DAC_SYNC', 1, 73.375, 5.625, 73.625, 5.375),
    ('seg', 'DAC_SYNC', 1, 73.625, 5.375, 73.875, 5.125),
    ('seg', 'DAC_SYNC', 1, 73.875, 5.125, 74.125, 4.875),
    ('seg', 'DAC_SYNC', 1, 74.125, 4.875, 74.375, 4.625),
    ('seg', 'DAC_SYNC', 1, 74.375, 4.625, 74.625, 4.375),
    ('seg', 'DAC_SYNC', 1, 74.625, 4.375, 74.875, 4.125),
    ('seg', 'DAC_SYNC', 1, 74.875, 4.125, 75.125, 3.875),
    ('seg', 'DAC_SYNC', 1, 75.125, 3.875, 75.375, 3.625),
    ('seg', 'DAC_SYNC', 1, 75.375, 3.625, 75.625, 3.375),
    ('seg', 'DAC_SYNC', 1, 75.625, 3.375, 75.875, 3.125),
    ('seg', 'DAC_SYNC', 1, 75.875, 3.125, 75.875, 2.125),
    ('seg', 'DAC_SYNC', 1, 75.875, 2.125, 76.125, 1.875),
    ('seg', 'DAC_SYNC', 1, 76.125, 1.875, 76.375, 1.625),
    ('seg', 'SPI_SCK', 0, 71.425, 6.750, 72.050, 7.100),
    ('seg', 'SPI_MOSI', 0, 71.425, 6.250, 71.850, 6.350),
]
BOARD_VIA_RIPS = [('SPI_SCK', 72.05, 7.1), ('SPI_MOSI', 71.85, 6.35)]
tracks = list(board.GetTracks())
victims = []
for spec in BOARD_SEG_RIPS:
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
assert len(victims) == len(BOARD_SEG_RIPS), \
    f'seg rip victims {len(victims)} != {len(BOARD_SEG_RIPS)}'
nvias = 0
for net, x, y in BOARD_VIA_RIPS:
    for t in tracks:
        if not isinstance(t, pcbnew.PCB_VIA) or t.GetNetname() != net:
            continue
        p = pcbnew.ToMM(t.GetPosition())
        if abs(p[0] - x) < 0.01 and abs(p[1] - y) < 0.01 and t not in victims:
            victims.append(t); nvias += 1
assert nvias == len(BOARD_VIA_RIPS), f'via rip victims {nvias}'
for t in victims:
    board.Remove(t)
print(f'ripped {len(victims)} board items ({len(BOARD_SEG_RIPS)} segs + {nvias} vias)')
for e in plans:
    if e[0] == 'via':
        _, net, x, y = e
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
        v.SetWidth(MM(0.5)); v.SetDrill(MM(0.3))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNetCode(codes[net])
        board.Add(v)
    else:
        _, net, li, ax, ay, bx, by, wd = e
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(MM(ax), MM(ay)))
        t.SetEnd(pcbnew.VECTOR2I(MM(bx), MM(by)))
        t.SetWidth(MM(wd)); t.SetLayer(LAY[li]); t.SetNetCode(codes[net])
        board.Add(t)
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
board.Save(OUT)
print('saved', OUT)

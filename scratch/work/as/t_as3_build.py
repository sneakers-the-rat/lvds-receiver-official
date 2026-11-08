"""t_as3: build exp238 from exp236 - SPI_SCK connection (as session).
Design: sck_v8.json (35 items) + mods_v10.json (LOL B re-lay x67.375->x67.075
unsealing the (67.8,8.1) dive; DAC_SYNC F exit re-lay threading SCK arrival
vs SWCLK; SWCLK via (90.55,-18.05)->(90.35,-18.75)).
Re-gates every add in-script (exact item model), rips board items by exact
start/end with victim asserts, refill, save."""
import sys, wx, json
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
from t_ai_lib import load_items, pt_margin, seg_margin, fmt_it, apply_rip

SRC = 'hw/pdlvds_rx.exp236.kicad_pcb'
OUT = 'hw/pdlvds_rx.exp238.kicad_pcb'
MM = pcbnew.FromMM
LAY = {0: pcbnew.F_Cu, 1: pcbnew.In2_Cu, 2: pcbnew.B_Cu}

mods = json.load(open('scratch/work/ar/mods_v10.json'))
plans = [tuple(e) for e in mods['adds']]
for e in json.load(open('scratch/work/ar/sck_v12.json')):
    plans.append(tuple(e))

board = pcbnew.LoadBoard(SRC)
items = load_items(board)
statics, nrip = apply_rip({l: list(items[l]) for l in range(3)},
                          [tuple(r) for r in mods['rips']])
print(f'model rips applied: {nrip}')
pool = {l: list(statics[l]) for l in range(3)}
fails = 0
for e in plans:
    if e[0] == 'via':
        _, net, x, y = e
        it = ('via', net, (x, y, 0.25), 0.2)
        for l in range(3):
            m, w = pt_margin(l, x, y, net, 0.25, pool[l])
            if m < -0.001:
                fails += 1
                print(f'  FAIL via {net} ({x},{y}) L{l}: {m:+.3f} vs {fmt_it(w)}')
            pool[l].append(it)
    else:
        _, net, li, ax, ay, bx, by, wd = e
        it = ('seg', net, (ax, ay, bx, by, wd / 2), 0.2)
        m, w = seg_margin(li, (ax, ay), (bx, by), net, wd / 2, pool[li], step=0.04)
        if m < -0.001:
            fails += 1
            print(f'  FAIL seg {net} L{li} ({ax},{ay})->({bx},{by}): {m:+.3f} vs {fmt_it(w)}')
        pool[li].append(it)
assert fails == 0, f'{fails} GATE FAILURES - NOT BUILDING'
print(f'ALL {len(plans)} PLAN ITEMS GATE-CLEAN')

codes = {}
for n in ('CDR_LOL', 'DAC_SYNC', 'SWCLK', 'SPI_SCK'):
    codes[n] = board.GetNetcodeFromNetname(n)

BOARD_SEG_RIPS = [
    ('CDR_LOL', 2, 67.125, 14.375, 67.375, 14.125),
    ('CDR_LOL', 2, 67.375, 14.125, 67.375, 6.875),
    ('CDR_LOL', 2, 67.375, 6.875, 67.625, 6.625),
    ('DAC_SYNC', 0, 89.75, -18.3, 89.95, -17.85),
    ('DAC_SYNC', 0, 89.95, -17.85, 90.25, -17.55),
    ('SWCLK', 0, 90.75, -17.6, 90.55, -18.05),
    ('SWCLK', 2, 90.55, -18.05, 89.9, -23.0),
]
BOARD_VIA_RIPS = [('SWCLK', 90.55, -18.05)]
tracks = list(board.GetTracks())
victims = []
for net, li, ax, ay, bx, by in BOARD_SEG_RIPS:
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

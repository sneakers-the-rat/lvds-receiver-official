"""t_aq40: exp236 referee fix pass.
- Delete DAC_SYNC via (87.3,-18.15): its F side was ripped in prep; the
  B junction (detour + old B chain) stands without it.
- Shorten DAC braid landing seg (76.375,1.625)->(76.625,1.375) to start
  at the T point (76.55,1.45) where DAC v2' seg3 lands: kills the
  dangling west tail.
- Rip SPI_SCK's south prep set (via 89.8,-19.05 + 5 F stub segs): its
  journey has not landed; a dangling prep via is not bankable.
- Move R16 (86.3,-21.3) -> (86.6,-21.7): clears DBG_TX F clearance
  (was 0.075) and the TP3 courtyard overlap; re-lay BOOT0/GND webs;
  place refdes at (86.6,-20.35) (prep move left it at the old site,
  overlapping TP3 silk).
Zone refill, save over exp236."""
import sys, wx
_app = wx.App(False)
import pcbnew

SRC = 'hw/pdlvds_rx.exp236.kicad_pcb'
MM = pcbnew.FromMM
LAY = {0: pcbnew.F_Cu, 1: pcbnew.In2_Cu, 2: pcbnew.B_Cu}

SEG_RIPS = [
    ('DAC_SYNC', 1, 76.375, 1.625, 76.625, 1.375),
    ('SPI_SCK', 0, 89.800, -19.050, 89.150, -18.700),
    ('SPI_SCK', 0, 89.150, -18.700, 89.150, -17.900),
    ('SPI_SCK', 0, 89.150, -17.900, 89.520, -17.720),
    ('SPI_SCK', 0, 89.520, -17.720, 89.750, -17.480),
    ('SPI_SCK', 0, 89.750, -17.480, 89.750, -17.300),
    ('BOOT0', 0, 87.375, -18.875, 86.600, -20.200),
    ('BOOT0', 0, 86.600, -20.200, 85.475, -21.300),
    ('GND', 0, 87.125, -21.300, 87.125, -22.750),
]
VIA_RIPS = [('DAC_SYNC', 87.300, -18.150), ('SPI_SCK', 89.800, -19.050),
            ('GND', 87.125, -22.750)]
ADDS = [
    ('seg', 'DAC_SYNC', 1, 76.550, 1.450, 76.625, 1.375, 0.25),
    ('seg', 'BOOT0', 0, 87.375, -18.875, 86.900, -20.500, 0.2),
    ('seg', 'BOOT0', 0, 86.900, -20.500, 85.775, -21.700, 0.2),
    ('seg', 'GND', 0, 87.425, -21.700, 87.350, -22.850, 0.2),
    ('via', 'GND', 87.350, -22.850),
]

board = pcbnew.LoadBoard(SRC)
codes = {n: board.GetNetcodeFromNetname(n)
         for n in ('DAC_SYNC', 'SPI_SCK', 'BOOT0', 'GND')}
tracks = list(board.GetTracks())
victims = []
for net, li, ax, ay, bx, by in SEG_RIPS:
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
assert len(victims) == len(SEG_RIPS), f'seg victims {len(victims)} != {len(SEG_RIPS)}'
nv = 0
for net, x, y in VIA_RIPS:
    for t in tracks:
        if not isinstance(t, pcbnew.PCB_VIA) or t.GetNetname() != net:
            continue
        p = pcbnew.ToMM(t.GetPosition())
        if abs(p[0] - x) < 0.01 and abs(p[1] - y) < 0.01 and t not in victims:
            victims.append(t); nv += 1
assert nv == len(VIA_RIPS), f'via victims {nv} != {len(VIA_RIPS)}'
for t in victims:
    board.Remove(t)
print(f'ripped {len(victims)}')

r16 = None
for fp in board.GetFootprints():
    if fp.GetReference() == 'R16':
        r16 = fp
assert r16 is not None
r16.SetPosition(pcbnew.VECTOR2I(MM(86.6), MM(-21.7)))
r16.Reference().SetPosition(pcbnew.VECTOR2I(MM(86.6), MM(-20.35)))
print('R16 moved to (86.6,-21.7), refdes (86.6,-20.35)')

for e in ADDS:
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
board.Save(SRC)
print('saved', SRC)

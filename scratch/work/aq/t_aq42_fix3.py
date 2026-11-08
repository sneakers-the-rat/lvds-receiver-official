"""t_aq42: R16 final site (86.9,-23.4): courtyard clears TP3 (north
edge -22.645 < TP3 south -22.525) and TP2 (west edge 85.395 > TP2 east
85.275); refdes (86.9,-25.3). Re-lay BOOT0/GND webs."""
import wx
_app = wx.App(False)
import pcbnew
SRC = 'hw/pdlvds_rx.exp236.kicad_pcb'
MM = pcbnew.FromMM
SEG_RIPS = [('BOOT0', 87.375, -18.875, 86.950, -20.700),
            ('BOOT0', 86.950, -20.700, 85.675, -22.100),
            ('GND', 87.325, -22.100, 87.300, -23.500)]
VIA_RIPS = [('GND', 87.300, -23.500)]
ADDS = [('seg', 'BOOT0', 87.375, -18.875, 87.100, -21.000, 0.2),
        ('seg', 'BOOT0', 87.100, -21.000, 86.075, -23.400, 0.2),
        ('seg', 'GND', 87.725, -23.400, 87.600, -24.600, 0.2),
        ('via', 'GND', 87.600, -24.600)]
board = pcbnew.LoadBoard(SRC)
codes = {n: board.GetNetcodeFromNetname(n) for n in ('BOOT0', 'GND')}
tracks = list(board.GetTracks())
victims = []
for net, ax, ay, bx, by in SEG_RIPS:
    for t in tracks:
        if isinstance(t, pcbnew.PCB_VIA) or t.GetNetname() != net:
            continue
        if t.GetLayer() != pcbnew.F_Cu:
            continue
        a = pcbnew.ToMM(t.GetStart()); b = pcbnew.ToMM(t.GetEnd())
        key = (round(a[0], 3), round(a[1], 3), round(b[0], 3), round(b[1], 3))
        want = {(round(ax, 3), round(ay, 3), round(bx, 3), round(by, 3)),
                (round(bx, 3), round(by, 3), round(ax, 3), round(ay, 3))}
        if key in want and t not in victims:
            victims.append(t)
assert len(victims) == len(SEG_RIPS), f'seg victims {len(victims)}'
nv = 0
for net, x, y in VIA_RIPS:
    for t in tracks:
        if not isinstance(t, pcbnew.PCB_VIA) or t.GetNetname() != net:
            continue
        p = pcbnew.ToMM(t.GetPosition())
        if abs(p[0] - x) < 0.01 and abs(p[1] - y) < 0.01 and t not in victims:
            victims.append(t); nv += 1
assert nv == len(VIA_RIPS)
for t in victims:
    board.Remove(t)
print(f'ripped {len(victims)}')
for fp in board.GetFootprints():
    if fp.GetReference() == 'R16':
        fp.SetPosition(pcbnew.VECTOR2I(MM(86.9), MM(-23.4)))
        fp.Reference().SetPosition(pcbnew.VECTOR2I(MM(86.9), MM(-25.3)))
print('R16 -> (86.9,-23.4), refdes (86.9,-25.3)')
for e in ADDS:
    if e[0] == 'via':
        _, net, x, y = e
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
        v.SetWidth(MM(0.5)); v.SetDrill(MM(0.3))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNetCode(codes[net]); board.Add(v)
    else:
        _, net, ax, ay, bx, by, wd = e
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(MM(ax), MM(ay)))
        t.SetEnd(pcbnew.VECTOR2I(MM(bx), MM(by)))
        t.SetWidth(MM(wd)); t.SetLayer(pcbnew.F_Cu); t.SetNetCode(codes[net])
        board.Add(t)
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
board.Save(SRC)
print('saved', SRC)

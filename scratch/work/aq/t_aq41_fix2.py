"""t_aq41: R16 final site (86.5,-22.1) - clears DBG_TX (x>=86.425),
TP3 pad gap, and TP3's silk circle (needs GND pad mask >=1.01 from
(88.75,-21.25)); refdes south at (86.5,-23.6). Re-lay BOOT0/GND webs."""
import wx
_app = wx.App(False)
import pcbnew
SRC = 'hw/pdlvds_rx.exp236.kicad_pcb'
MM = pcbnew.FromMM
SEG_RIPS = [('BOOT0', 0, 87.375, -18.875, 86.900, -20.500),
            ('BOOT0', 0, 86.900, -20.500, 85.775, -21.700),
            ('GND', 0, 87.425, -21.700, 87.350, -22.850)]
VIA_RIPS = [('GND', 87.350, -22.850)]
ADDS = [('seg', 'BOOT0', 0, 87.375, -18.875, 86.950, -20.700, 0.2),
        ('seg', 'BOOT0', 0, 86.950, -20.700, 85.675, -22.100, 0.2),
        ('seg', 'GND', 0, 87.325, -22.100, 87.300, -23.500, 0.2),
        ('via', 'GND', 87.300, -23.500)]
board = pcbnew.LoadBoard(SRC)
codes = {n: board.GetNetcodeFromNetname(n) for n in ('BOOT0', 'GND')}
tracks = list(board.GetTracks())
victims = []
for net, li, ax, ay, bx, by in SEG_RIPS:
    for t in tracks:
        if isinstance(t, pcbnew.PCB_VIA) or t.GetNetname() != net:
            continue
        if li != 0 or t.GetLayer() != pcbnew.F_Cu:
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
        fp.SetPosition(pcbnew.VECTOR2I(MM(86.5), MM(-22.1)))
        fp.Reference().SetPosition(pcbnew.VECTOR2I(MM(86.5), MM(-23.6)))
print('R16 -> (86.5,-22.1), refdes (86.5,-23.6)')
for e in ADDS:
    if e[0] == 'via':
        _, net, x, y = e
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
        v.SetWidth(MM(0.5)); v.SetDrill(MM(0.3))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNetCode(codes[net]); board.Add(v)
    else:
        _, net, li, ax, ay, bx, by, wd = e
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(MM(ax), MM(ay)))
        t.SetEnd(pcbnew.VECTOR2I(MM(bx), MM(by)))
        t.SetWidth(MM(wd)); t.SetLayer(pcbnew.F_Cu); t.SetNetCode(codes[net])
        board.Add(t)
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
board.Save(SRC)
print('saved', SRC)

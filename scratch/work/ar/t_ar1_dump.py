"""t_ar1: dump all copper items (pads w/ ref.pad, segs, vias) in a box,
per layer (0=F,1=In2,2=B). Usage: t_ar1_dump.py BOARD X0 X1 Y0 Y1 [NET ...]"""
import sys, wx
_app = wx.App(False)
import pcbnew

BOARD = sys.argv[1]
X0, X1, Y0, Y1 = (float(v) for v in sys.argv[2:6])
NETS = set(sys.argv[6:])
LAY = {pcbnew.F_Cu: 0, pcbnew.In2_Cu: 1, pcbnew.B_Cu: 2}
MM = pcbnew.ToMM

def inbox(x, y):
    return X0 - 1.5 <= x <= X1 + 1.5 and Y0 - 1.5 <= y <= Y1 + 1.5

board = pcbnew.LoadBoard(BOARD)
rows = []
for fp in board.GetFootprints():
    ref = fp.GetReference()
    for pad in fp.Pads():
        net = pad.GetNetname()
        if NETS and net not in NETS:
            continue
        p = MM(pad.GetPosition())
        if not inbox(p[0], p[1]):
            continue
        sz = MM(pad.GetSize())
        lay = 'SMD' if pad.GetLayerSet().Contains(pcbnew.F_Cu) and not pad.GetLayerSet().Contains(pcbnew.B_Cu) else 'TH'
        side = 'F' if pad.GetLayerSet().Contains(pcbnew.F_Cu) else 'B'
        rows.append((0 if side == 'F' else 2, f'PAD {ref}.{pad.GetNumber()} {net} ({p[0]:.3f},{p[1]:.3f}) {sz[0]:.3f}x{sz[1]:.3f} rot{fp.GetOrientationDegrees():.0f} {lay}{side}'))
for t in board.GetTracks():
    net = t.GetNetname()
    if NETS and net not in NETS:
        continue
    if isinstance(t, pcbnew.PCB_VIA):
        p = MM(t.GetPosition())
        if not inbox(p[0], p[1]):
            continue
        rows.append((-1, f'VIA {net} ({p[0]:.3f},{p[1]:.3f}) d{MM(t.GetWidth()):.2f} drill{MM(t.GetDrill()):.2f} [all layers]'))
    else:
        li = LAY.get(t.GetLayer())
        if li is None:
            continue
        a = MM(t.GetStart()); b = MM(t.GetEnd())
        if not (inbox(a[0], a[1]) or inbox(b[0], b[1])):
            continue
        rows.append((li, f'SEG L{li} {net} ({a[0]:.3f},{a[1]:.3f})->({b[0]:.3f},{b[1]:.3f}) w{MM(t.GetWidth()):.2f}'))
for z in board.Zones():
    net = z.GetNetname()
    if NETS and net not in NETS:
        continue
    li = LAY.get(z.GetLayer())
    if li is None:
        continue
    bb = z.GetBoundingBox()
    c = MM(bb.GetCenter())
    if inbox(c[0], c[1]):
        rows.append((li, f'ZONE L{li} {net} bbox=({MM(bb.GetLeft()):.2f},{MM(bb.GetTop()):.2f})-({MM(bb.GetRight()):.2f},{MM(bb.GetBottom()):.2f})'))
for li in (-1, 0, 1, 2):
    for _, r in sorted([x for x in rows if x[0] == li]):
        print(r)

import wx
wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp257.kicad_pcb')
LN = {pcbnew.F_Cu: 'F', pcbnew.In1_Cu: 'In1', pcbnew.In2_Cu: 'In2', pcbnew.B_Cu: 'B'}
X0, X1, Y0, Y1 = 70.5, 77.6, 3.0, 20.5
M = 0.7

def seg_hits_rect(ax, ay, bx, by):
    return not (max(ax, bx) < X0 - M or min(ax, bx) > X1 + M or
                max(ay, by) < Y0 - M or min(ay, by) > Y1 + M)

print('--- U6/U7 pads in region (rects)')
for fp in b.GetFootprints():
    ref = fp.GetReference()
    if ref not in ('U6', 'U7'):
        continue
    for p in fp.Pads():
        bb = p.GetBoundingBox()
        cx, cy = (bb.GetLeft() + bb.GetRight()) / 2e6, (bb.GetTop() + bb.GetBottom()) / 2e6
        if X0 - 1 < cx < X1 + 1 and Y0 - 1 < cy < Y1 + 1:
            print(f"  {ref}.{p.GetNumber()} [{p.GetNetname()}] rect x[{bb.GetLeft()/1e6:.3f},{bb.GetRight()/1e6:.3f}] y[{bb.GetTop()/1e6:.3f},{bb.GetBottom()/1e6:.3f}]")

from collections import defaultdict
items = defaultdict(list)
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        p = t.GetPosition(); x, y = p.x / 1e6, p.y / 1e6
        if X0 - M < x < X1 + M and Y0 - M < y < Y1 + M:
            items[(t.GetNetname(), 'via')].append(f"({x:.2f},{y:.2f})d{t.GetWidth()/1e6:.2f}")
    else:
        s, e = t.GetStart(), t.GetEnd()
        ax, ay, bx, by = s.x / 1e6, s.y / 1e6, e.x / 1e6, e.y / 1e6
        if seg_hits_rect(ax, ay, bx, by):
            items[(t.GetNetname(), LN[t.GetLayer()])].append(
                f"({ax:.2f},{ay:.2f})-({bx:.2f},{by:.2f})")
for (net, lay) in sorted(items):
    lst = items[(net, lay)]
    print(f"--- {net} [{lay}] x{len(lst)}")
    for s in lst:
        print('   ', s)

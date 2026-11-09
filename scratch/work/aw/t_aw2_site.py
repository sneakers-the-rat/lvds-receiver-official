"""t_aw2: real-board facts for the H5 site scan.
C1 (0402) pad geometry from the board; X2 footprint facts;
all footprint bboxes in region x[65,78] y[15,32]."""
import wx
_app = wx.App(False)
import pcbnew

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp240.kicad_pcb')
IU = 1e6  # nm per mm

def mm(v):
    return v / IU

for ref in ('C1', 'X2', 'C22', 'C24', 'C20', 'C28'):
    fp = b.FindFootprintByReference(ref)
    if fp is None:
        print(f'{ref}: NOT FOUND', flush=True)
        continue
    pos = fp.GetPosition()
    print(f'{ref}: centre=({mm(pos.x):.3f},{mm(pos.y):.3f}) '
          f'rot={fp.GetOrientationDegrees():.1f} '
          f'fp={fp.GetFPID().GetLibItemName()}', flush=True)
    for pad in fp.Pads():
        pp = pad.GetPosition()
        sz = pad.GetSize()
        print(f'   pad {pad.GetNumber()} net={pad.GetNetname()} '
              f'centre=({mm(pp.x):.3f},{mm(pp.y):.3f}) '
              f'size=({mm(sz.x):.3f},{mm(sz.y):.3f})', flush=True)
    bb = fp.GetBoundingBox()
    print(f'   bbox x[{mm(bb.GetLeft()):.3f},{mm(bb.GetRight()):.3f}] '
          f'y[{mm(bb.GetTop()):.3f},{mm(bb.GetBottom()):.3f}]', flush=True)

print('=== footprints intersecting x[65,78] y[15,32] ===', flush=True)
for fp in b.GetFootprints():
    bb = fp.GetBoundingBox()
    l, r = mm(bb.GetLeft()), mm(bb.GetRight())
    t, bo = mm(bb.GetTop()), mm(bb.GetBottom())
    if r < 65 or l > 78 or bo < 15 or t > 32:
        continue
    pos = fp.GetPosition()
    print(f'  {fp.GetReference()} centre=({mm(pos.x):.2f},{mm(pos.y):.2f}) '
          f'bbox x[{l:.2f},{r:.2f}] y[{t:.2f},{bo:.2f}]', flush=True)
print('done', flush=True)

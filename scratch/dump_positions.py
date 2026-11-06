import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
TM = pcbnew.ToMM
board = pcbnew.LoadBoard('hw/pdlvds_rx.exp16.kicad_pcb')
rows = []
for fp in board.GetFootprints():
    p = fp.GetPosition()
    bb = fp.GetBoundingBox()
    rows.append((fp.GetReference(), round(TM(p.x), 2), round(TM(p.y), 2),
                 round(TM(bb.GetWidth()), 1), round(TM(bb.GetHeight()), 1),
                 round(fp.GetOrientationDegrees(), 0),
                 fp.GetFPID().GetLibItemName()))
for r in sorted(rows, key=lambda r: r[0]):
    print(r)
print('total footprints:', len(rows))

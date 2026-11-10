import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp89.kicad_pcb')
X0, X1, Y0, Y1 = 53.5, 56.0, -16.2, -13.8
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        continue
    bb = t.GetBoundingBox()
    x0, x1 = pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetRight())
    y0, y1 = pcbnew.ToMM(bb.GetTop()), pcbnew.ToMM(bb.GetBottom())
    if x1 < X0 or x0 > X1 or y1 < Y0 or y0 > Y1:
        continue
    s, e = t.GetStart(), t.GetEnd()
    print('TRK', t.GetNetname(), 'L', t.GetLayer(), 'w', round(pcbnew.ToMM(t.GetWidth()),2),
          (round(pcbnew.ToMM(s.x),2), round(pcbnew.ToMM(s.y),2)), '->',
          (round(pcbnew.ToMM(e.x),2), round(pcbnew.ToMM(e.y),2)))

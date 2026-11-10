import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp91.kicad_pcb')
X0, X1, Y0, Y1 = 54.6, 56.2, -14.4, -12.6
for t in b.GetTracks():
    if t.GetNetname() not in ('REFCLK', 'REFCLKN'):
        continue
    bb = t.GetBoundingBox()
    x0, x1 = pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetRight())
    y0, y1 = pcbnew.ToMM(bb.GetTop()), pcbnew.ToMM(bb.GetBottom())
    if x1 < X0 or x0 > X1 or y1 < Y0 or y0 > Y1:
        continue
    if isinstance(t, pcbnew.PCB_VIA):
        p = t.GetPosition()
        print('VIA', t.GetNetname(), round(pcbnew.ToMM(p.x),2), round(pcbnew.ToMM(p.y),2))
    else:
        s, e = t.GetStart(), t.GetEnd()
        print('TRK', t.GetNetname(), 'L', t.GetLayer(),
              (round(pcbnew.ToMM(s.x),2), round(pcbnew.ToMM(s.y),2)), '->',
              (round(pcbnew.ToMM(e.x),2), round(pcbnew.ToMM(e.y),2)))

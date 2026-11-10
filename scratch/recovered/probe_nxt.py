import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp100.kicad_pcb')
for t in b.GetTracks():
    n = t.GetNetname()
    if n not in ('ULPI_NXT', 'CDR_DATP'):
        continue
    bb = t.GetBoundingBox()
    x0, x1 = pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetRight())
    y0, y1 = pcbnew.ToMM(bb.GetTop()), pcbnew.ToMM(bb.GetBottom())
    if isinstance(t, pcbnew.PCB_VIA):
        p = t.GetPosition()
        x, y = pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)
        if 70 < x < 80 and 5 < y < 20:
            print('VIA', n, round(x,2), round(y,2))
        continue
    if x1 < 70 or x0 > 80 or y1 < 5 or y0 > 20:
        continue
    s, e = t.GetStart(), t.GetEnd()
    print('TRK', n, 'L', t.GetLayer(),
          (round(pcbnew.ToMM(s.x),2), round(pcbnew.ToMM(s.y),2)), '->',
          (round(pcbnew.ToMM(e.x),2), round(pcbnew.ToMM(e.y),2)))

import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp87.kicad_pcb')
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        continue
    s, e = t.GetStart(), t.GetEnd()
    pts = [(pcbnew.ToMM(s.x), pcbnew.ToMM(s.y)), (pcbnew.ToMM(e.x), pcbnew.ToMM(e.y))]
    if any(38.0 < x < 43.0 and 55.8 < y < 57.4 for x, y in pts):
        print('TRK', t.GetNetname(), 'L', t.GetLayer(), 'w', round(pcbnew.ToMM(t.GetWidth()),2),
              tuple(round(v,2) for v in pts[0]), '->', tuple(round(v,2) for v in pts[1]))

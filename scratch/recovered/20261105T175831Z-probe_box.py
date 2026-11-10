import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp89.kicad_pcb')
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        p = t.GetPosition()
        x, y = pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)
        if 53 < x < 60 and -19 < y < -12.5:
            print('VIA', t.GetNetname(), round(x,2), round(y,2))
        continue
    if t.GetLayer() != 0:
        continue
    s, e = t.GetStart(), t.GetEnd()
    pts = [(pcbnew.ToMM(s.x), pcbnew.ToMM(s.y)), (pcbnew.ToMM(e.x), pcbnew.ToMM(e.y))]
    if any(53 < x < 60 and -19 < y < -12.5 for x, y in pts):
        print('TRK', t.GetNetname(), tuple(round(v,2) for v in pts[0]), '->', tuple(round(v,2) for v in pts[1]))

import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp83.kicad_pcb')
for t in b.GetTracks():
    if t.GetNetname() == 'NEG_RAW':
        if isinstance(t, pcbnew.PCB_VIA):
            p = t.GetPosition()
            x, y = pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)
            if 40 < x < 46 and 58 < y < 66:
                print('VIA NEG_RAW', round(x,2), round(y,2))
        else:
            s, e = t.GetStart(), t.GetEnd()
            x0 = min(pcbnew.ToMM(s.x), pcbnew.ToMM(e.x)); x1 = max(pcbnew.ToMM(s.x), pcbnew.ToMM(e.x))
            y0 = min(pcbnew.ToMM(s.y), pcbnew.ToMM(e.y)); y1 = max(pcbnew.ToMM(s.y), pcbnew.ToMM(e.y))
            if x0 < 46 and x1 > 40 and y0 < 66 and y1 > 58:
                print('TRK NEG_RAW L', t.GetLayer(), 'w', round(pcbnew.ToMM(t.GetWidth()),2),
                      (round(pcbnew.ToMM(s.x),2), round(pcbnew.ToMM(s.y),2)), '->',
                      (round(pcbnew.ToMM(e.x),2), round(pcbnew.ToMM(e.y),2)))

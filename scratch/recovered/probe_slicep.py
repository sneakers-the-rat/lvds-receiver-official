import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp82.kicad_pcb')
for t in b.GetTracks():
    if t.GetNetname() in ('SLICEP','SLICEN'):
        if t.Type() == pcbnew.PCB_VIA_T:
            p = t.GetPosition()
            print('VIA', t.GetNetname(), round(pcbnew.ToMM(p.x),3), round(pcbnew.ToMM(p.y),3))
        else:
            s, e = t.GetStart(), t.GetEnd()
            x0 = min(pcbnew.ToMM(s.x), pcbnew.ToMM(e.x))
            if x0 < 52.2:
                print('TRK', t.GetNetname(), 'layer', t.GetLayer(), 'w', round(pcbnew.ToMM(t.GetWidth()),2),
                      (round(pcbnew.ToMM(s.x),2), round(pcbnew.ToMM(s.y),2)), '->', (round(pcbnew.ToMM(e.x),2), round(pcbnew.ToMM(e.y),2)))

import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp87.kicad_pcb')
for t in b.GetTracks():
    if t.GetNetname() != 'DM_PHY':
        continue
    if isinstance(t, pcbnew.PCB_VIA):
        p = t.GetPosition()
        print('VIA DM_PHY', round(pcbnew.ToMM(p.x),2), round(pcbnew.ToMM(p.y),2))
    else:
        s, e = t.GetStart(), t.GetEnd()
        x0, x1 = sorted((pcbnew.ToMM(s.x), pcbnew.ToMM(e.x)))
        y0, y1 = sorted((pcbnew.ToMM(s.y), pcbnew.ToMM(e.y)))
        if x1 > 40 and x0 < 50 and y1 > 48 and y0 < 60:
            print('TRK DM_PHY L', t.GetLayer(),
                  (round(pcbnew.ToMM(s.x),2), round(pcbnew.ToMM(s.y),2)), '->',
                  (round(pcbnew.ToMM(e.x),2), round(pcbnew.ToMM(e.y),2)))

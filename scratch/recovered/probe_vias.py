import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp82.kicad_pcb')
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        p = t.GetPosition()
        x, y = pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)
        if 50.0 < x < 53.2 and -18.6 < y < -15.8:
            print('VIA', t.GetNetname(), round(x,3), round(y,3), 'w', round(pcbnew.ToMM(t.GetWidth()),2))

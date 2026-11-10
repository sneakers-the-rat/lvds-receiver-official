import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp91.kicad_pcb')
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() in ('REFCLK','REFCLKN'):
        p = t.GetPosition()
        print('VIA', t.GetNetname(), round(pcbnew.ToMM(p.x),3), round(pcbnew.ToMM(p.y),3))

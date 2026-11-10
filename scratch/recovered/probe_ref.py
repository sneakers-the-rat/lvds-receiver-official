import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp91.kicad_pcb')
for t in b.GetTracks():
    if t.GetNetname() != 'REFCLK' or isinstance(t, pcbnew.PCB_VIA):
        continue
    s, e = t.GetStart(), t.GetEnd()
    if max(pcbnew.ToMM(s.x), pcbnew.ToMM(e.x)) > 54.5 and t.GetLayer() in (1, 2):
        print('TRK REFCLK L', t.GetLayer(),
              (round(pcbnew.ToMM(s.x),2), round(pcbnew.ToMM(s.y),2)), '->',
              (round(pcbnew.ToMM(e.x),2), round(pcbnew.ToMM(e.y),2)))

import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp93.kicad_pcb')
for t in b.GetTracks():
    if t.GetNetname() != 'THRADJ':
        continue
    bb = t.GetBoundingBox()
    x0, x1 = pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetRight())
    y0, y1 = pcbnew.ToMM(bb.GetTop()), pcbnew.ToMM(bb.GetBottom())
    if x1 < 52.0 or x0 > 55.0 or y1 < -17.0 or y0 > -12.0:
        continue
    if isinstance(t, pcbnew.PCB_VIA):
        p = t.GetPosition()
        print('VIA THRADJ', round(pcbnew.ToMM(p.x),3), round(pcbnew.ToMM(p.y),3))
    else:
        s, e = t.GetStart(), t.GetEnd()
        print('TRK THRADJ L', t.GetLayer(),
              (round(pcbnew.ToMM(s.x),2), round(pcbnew.ToMM(s.y),2)), '->',
              (round(pcbnew.ToMM(e.x),2), round(pcbnew.ToMM(e.y),2)))

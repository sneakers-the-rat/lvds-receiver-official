import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp87.kicad_pcb')
cx, cy = 42.30, 56.50
for fp in b.GetFootprints():
    for pad in fp.Pads():
        p = pad.GetPosition()
        x, y = pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)
        if abs(x-cx) < 5 and abs(y-cy) < 5:
            print('PAD', pad.GetNetname(), f"{fp.GetReference()}.{pad.GetNumber()}", round(x,2), round(y,2))
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        p = t.GetPosition()
        x, y = pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)
        if abs(x-cx) < 5 and abs(y-cy) < 5:
            print('VIA', t.GetNetname(), round(x,2), round(y,2))
    else:
        s, e = t.GetStart(), t.GetEnd()
        for (x, y) in ((pcbnew.ToMM(s.x), pcbnew.ToMM(s.y)), (pcbnew.ToMM(e.x), pcbnew.ToMM(e.y))):
            if abs(x-cx) < 5 and abs(y-cy) < 5:
                print('TRK', t.GetNetname(), 'L', t.GetLayer(),
                      (round(pcbnew.ToMM(s.x),2), round(pcbnew.ToMM(s.y),2)), '->',
                      (round(pcbnew.ToMM(e.x),2), round(pcbnew.ToMM(e.y),2)))
                break

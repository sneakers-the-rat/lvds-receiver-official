import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp99.kicad_pcb')
print('--- U7 pads ---')
for fp in b.GetFootprints():
    if fp.GetReference() != 'U7':
        continue
    for pad in fp.Pads():
        p = pad.GetPosition()
        print('PAD', pad.GetNetname(), f"U7.{pad.GetNumber()}",
              round(pcbnew.ToMM(p.x),2), round(pcbnew.ToMM(p.y),2),
              round(pcbnew.ToMM(pad.GetSize().x),2), round(pcbnew.ToMM(pad.GetSize().y),2))
print('--- F tracks x 68..80, y 6..24 ---')
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA) or t.GetLayer() != 0:
        continue
    bb = t.GetBoundingBox()
    x0, x1 = pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetRight())
    y0, y1 = pcbnew.ToMM(bb.GetTop()), pcbnew.ToMM(bb.GetBottom())
    if x1 < 68 or x0 > 80 or y1 < 6 or y0 > 24:
        continue
    s, e = t.GetStart(), t.GetEnd()
    print('TRK', t.GetNetname(),
          (round(pcbnew.ToMM(s.x),2), round(pcbnew.ToMM(s.y),2)), '->',
          (round(pcbnew.ToMM(e.x),2), round(pcbnew.ToMM(e.y),2)))

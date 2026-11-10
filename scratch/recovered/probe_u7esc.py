import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp99.kicad_pcb')
want = {'ULPI_NXT', 'ULPI_DIR', 'ULPI_D4', 'ULPI_CLK', 'VBUS', 'ID'}
for fp in b.GetFootprints():
    if fp.GetReference() != 'U7':
        continue
    for pad in fp.Pads():
        if pad.GetNetname() in want:
            p = pad.GetPosition()
            print('PAD', pad.GetNetname(), f"U7.{pad.GetNumber()}",
                  round(pcbnew.ToMM(p.x),2), round(pcbnew.ToMM(p.y),2),
                  round(pcbnew.ToMM(pad.GetSize().x),2), round(pcbnew.ToMM(pad.GetSize().y),2))
for t in b.GetTracks():
    if t.GetNetname() not in want:
        continue
    bb = t.GetBoundingBox()
    x0, x1 = pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetRight())
    y0, y1 = pcbnew.ToMM(bb.GetTop()), pcbnew.ToMM(bb.GetBottom())
    if x1 < 70 or x0 > 84 or y1 < 6 or y0 > 22:
        continue
    if isinstance(t, pcbnew.PCB_VIA):
        p = t.GetPosition()
        print('VIA', t.GetNetname(), round(pcbnew.ToMM(p.x),2), round(pcbnew.ToMM(p.y),2))
    else:
        s, e = t.GetStart(), t.GetEnd()
        print('TRK', t.GetNetname(), 'L', t.GetLayer(),
              (round(pcbnew.ToMM(s.x),2), round(pcbnew.ToMM(s.y),2)), '->',
              (round(pcbnew.ToMM(e.x),2), round(pcbnew.ToMM(e.y),2)))

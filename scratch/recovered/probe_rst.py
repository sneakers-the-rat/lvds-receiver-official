import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp101.kicad_pcb')
print('--- U6 residue pads ---')
for fp in b.GetFootprints():
    if fp.GetReference() != 'U6':
        continue
    for pad in fp.Pads():
        if pad.GetNetname() in ('CAP_CLK', 'CDR_LOL', 'USB_RST', 'VCAP2',
                                'CDR_SQUELCH', 'HV_EN', 'SWDIO', 'VCAP1'):
            p = pad.GetPosition()
            print('PAD', pad.GetNetname(), f"U6.{pad.GetNumber()}",
                  round(pcbnew.ToMM(p.x),2), round(pcbnew.ToMM(p.y),2),
                  round(pcbnew.ToMM(pad.GetSize().x),2), round(pcbnew.ToMM(pad.GetSize().y),2))
print('--- tracks x 73..77.5, y 3..17 ---')
for t in b.GetTracks():
    bb = t.GetBoundingBox()
    x0, x1 = pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetRight())
    y0, y1 = pcbnew.ToMM(bb.GetTop()), pcbnew.ToMM(bb.GetBottom())
    if x1 < 73 or x0 > 77.5 or y1 < 3 or y0 > 17:
        continue
    if isinstance(t, pcbnew.PCB_VIA):
        p = t.GetPosition()
        print('VIA', t.GetNetname(), round(pcbnew.ToMM(p.x),2), round(pcbnew.ToMM(p.y),2))
    else:
        s, e = t.GetStart(), t.GetEnd()
        print('TRK', t.GetNetname(), 'L', t.GetLayer(),
              (round(pcbnew.ToMM(s.x),2), round(pcbnew.ToMM(s.y),2)), '->',
              (round(pcbnew.ToMM(e.x),2), round(pcbnew.ToMM(e.y),2)))

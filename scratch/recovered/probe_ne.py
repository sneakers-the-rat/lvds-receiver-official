import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp89.kicad_pcb')
print('--- U4 pads x>53.5 or y>-17 ---')
for fp in b.GetFootprints():
    if fp.GetReference() != 'U4':
        continue
    for pad in fp.Pads():
        p = pad.GetPosition()
        x, y = pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)
        if x > 53.4 or y > -17.2:
            print('PAD', pad.GetNetname(), f"U4.{pad.GetNumber()}", round(x,2), round(y,2),
                  round(pcbnew.ToMM(pad.GetSize().x),2), round(pcbnew.ToMM(pad.GetSize().y),2))
print('--- +3V3D_CDR tracks x>49.5 ---')
for t in b.GetTracks():
    if t.GetNetname() != '+3V3D_CDR' or isinstance(t, pcbnew.PCB_VIA):
        continue
    s, e = t.GetStart(), t.GetEnd()
    if max(pcbnew.ToMM(s.x), pcbnew.ToMM(e.x)) > 49.5:
        print('TRK L', t.GetLayer(), (round(pcbnew.ToMM(s.x),2), round(pcbnew.ToMM(s.y),2)), '->',
              (round(pcbnew.ToMM(e.x),2), round(pcbnew.ToMM(e.y),2)))
print('--- all F tracks in box x 53..59.5, y -19..-13 ---')
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA) or t.GetLayer() != 0:
        continue
    s, e = t.GetStart(), t.GetEnd()
    pts = [(pcbnew.ToMM(s.x), pcbnew.ToMM(s.y)), (pcbnew.ToMM(e.x), pcbnew.ToMM(e.y))]
    if any(53 < x < 59.5 and -19 < y < -13 for x, y in pts):
        print('TRK', t.GetNetname(), tuple(round(v,2) for v in pts[0]), '->', tuple(round(v,2) for v in pts[1]))

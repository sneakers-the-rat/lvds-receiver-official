import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp89.kicad_pcb')
for t in b.GetTracks():
    if t.GetNetname() != '+3V3D_CDR':
        continue
    if isinstance(t, pcbnew.PCB_VIA):
        p = t.GetPosition()
        print('VIA +3V3D_CDR', round(pcbnew.ToMM(p.x),2), round(pcbnew.ToMM(p.y),2))
    else:
        s, e = t.GetStart(), t.GetEnd()
        x0, x1 = sorted((pcbnew.ToMM(s.x), pcbnew.ToMM(e.x)))
        y0, y1 = sorted((pcbnew.ToMM(s.y), pcbnew.ToMM(e.y)))
        if x1 > 44 and y0 < -6:
            print('TRK +3V3D_CDR L', t.GetLayer(),
                  (round(pcbnew.ToMM(s.x),2), round(pcbnew.ToMM(s.y),2)), '->',
                  (round(pcbnew.ToMM(e.x),2), round(pcbnew.ToMM(e.y),2)))
for fp in b.GetFootprints():
    for pad in fp.Pads():
        if pad.GetNetname() == '+3V3D_CDR':
            p = pad.GetPosition()
            print('PAD +3V3D_CDR', f"{fp.GetReference()}.{pad.GetNumber()}", round(pcbnew.ToMM(p.x),2), round(pcbnew.ToMM(p.y),2))

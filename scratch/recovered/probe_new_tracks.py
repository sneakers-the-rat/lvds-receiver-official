import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
TM = pcbnew.ToMM

def sig(t):
    if t.Type() == pcbnew.PCB_VIA_T:
        p = t.GetPosition()
        return ('via', t.GetNetname(), round(TM(p.x), 3), round(TM(p.y), 3))
    s, e = t.GetStart(), t.GetEnd()
    return ('trk', t.GetNetname(), t.GetLayer(),
            round(TM(s.x), 3), round(TM(s.y), 3),
            round(TM(e.x), 3), round(TM(e.y), 3), round(TM(t.GetWidth()), 3))

b12 = pcbnew.LoadBoard('hw/pdlvds_rx.exp12.kicad_pcb')
old = {sig(t) for t in b12.GetTracks()}
b13 = pcbnew.LoadBoard('hw/pdlvds_rx.exp13.kicad_pcb')
for t in b13.GetTracks():
    s = sig(t)
    if s[1] in ('HV_GATE', 'HV_SS') and s not in old:
        print('NEW', s)
# also: pads near the violations
for fp in b13.GetFootprints():
    if fp.GetReference() in ('R27', 'U10'):
        for p in fp.Pads():
            pos = p.GetPosition()
            print('PAD', fp.GetReference() + '.' + p.GetNumber(),
                  p.GetNetname(), round(TM(pos.x), 3), round(TM(pos.y), 3))

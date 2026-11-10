import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp265.kicad_pcb')
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        p = t.GetPosition()
        if 62.5 < p.x/1e6 < 66.0 and 15.8 < p.y/1e6 < 19.0:
            print('VIA', b.FindNet(t.GetNetCode()).GetNetname() if t.GetNetCode() else '?', p.x/1e6, p.y/1e6, t.GetWidth()/1e6)
n = 0
for fp in b.GetFootprints():
    for p in fp.Pads():
        pp = p.GetPosition()
        if 62.5 < pp.x/1e6 < 66.0 and 15.8 < pp.y/1e6 < 19.0:
            print('PAD', fp.GetReference(), p.GetPadName(), pp.x/1e6, pp.y/1e6)
            n += 1
print('pads found:', n)
fp = b.FindFootprintByReference('C22')
r = fp.Reference()
print('ref size', r.GetTextWidth()/1e6, r.GetTextHeight()/1e6, 'angle', r.GetTextAngle()/10)
bb = r.GetBoundingBox()
print('ref bbox mm', bb.GetX()/1e6, bb.GetY()/1e6, bb.GetWidth()/1e6, bb.GetHeight()/1e6)

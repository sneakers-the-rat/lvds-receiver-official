#!/usr/bin/env python3
"""D8 footprint swap: LED_1206_3216Metric -> SMT740_3227 (Ushio SMT740
is a 3.2x2.7 PLCC-style package, NOT a 1206 - datasheet outline p.1).
Same position/rotation; pad centres move 0.05 mm; existing F.Cu stubs
land inside the new pads. Field (refdes/value) positions copied."""
import pcbnew, sys, wx

SRC, DST = sys.argv[1], sys.argv[2]
_app = wx.App(False)
b = pcbnew.LoadBoard(SRC)
old = b.FindFootprintByReference('D8')
assert old is not None
pos = old.GetPosition(); rot = old.GetOrientation()
refpos = old.Reference().GetPosition(); refang = old.Reference().GetTextAngle()
valpos = old.Value().GetPosition(); valang = old.Value().GetTextAngle()
padnets = {p.GetNumber(): p.GetNetname() for p in old.Pads()}
print('old pads:', padnets)
b.Remove(old)
new = pcbnew.FootprintLoad('hw/pdlvds.pretty', 'SMT740_3227')
assert new is not None, 'footprint load failed'
new.SetReference('D8')
new.SetValue('SMT740 740nm LED BIST source')
new.SetPosition(pos); new.SetOrientation(rot)
b.Add(new)
for p in new.Pads():
    nn = padnets[p.GetNumber()]
    p.SetNet(b.FindNet(nn))
    pp = p.GetPosition()
    print('new pad %s -> %s at (%.2f, %.2f) size %.2f x %.2f' % (
        p.GetNumber(), nn, pp.x/1e6, pp.y/1e6, p.GetSize().x/1e6, p.GetSize().y/1e6))
new.Reference().SetPosition(refpos); new.Reference().SetTextAngle(refang)
new.Value().SetPosition(valpos); new.Value().SetTextAngle(valang)
b.Save(DST)
print('saved', DST)

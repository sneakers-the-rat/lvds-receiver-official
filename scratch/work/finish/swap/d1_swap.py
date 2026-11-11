#!/usr/bin/env python3
"""Swap D1's board footprint for the corrected C30737LH_LCC6
library footprint (docs/07 condition (a) proof: pads 0.70x0.60
at +/-1.00, pad 1 elongated 1.35 long). Field positions are
copied from the old footprint; pad nets by pad number.
"""
import wx
_app = wx.App(False)
import pcbnew
from pcbnew import VECTOR2I

BOARD = 'hw/pdlvds_rx.exp274.kicad_pcb'
board = pcbnew.LoadBoard(BOARD)

old = [f for f in board.GetFootprints() if f.GetReference() == 'D1'][0]
pos = old.GetPosition()
ori = old.GetOrientation()
ref_pos = old.Reference().GetPosition()
ref_ori = old.Reference().GetTextAngle()
val_pos = old.Value().GetPosition()
val_ori = old.Value().GetTextAngle()
padnets = {p.GetNumber(): p.GetNetCode() for p in old.Pads()}
print('old D1 at', pos.x / 1e6, pos.y / 1e6, 'pads',
      {n: board.FindNet(c).GetNetname() if c else None
       for n, c in padnets.items()})

new = pcbnew.FootprintLoad('hw/pdlvds.pretty', 'C30737LH_LCC6')
assert new is not None
new.SetPosition(pos)
new.SetOrientation(ori)
new.SetReference('D1')
new.Reference().SetPosition(ref_pos)
new.Reference().SetTextAngle(ref_ori)
new.Value().SetPosition(val_pos)
new.Value().SetTextAngle(val_ori)

board.Remove(old)
board.Add(new)
for p in new.Pads():
    if p.GetNumber() in padnets and padnets[p.GetNumber()]:
        p.SetNetCode(padnets[p.GetNumber()])
    c = p.GetPosition()
    print('new pad', p.GetNumber(), p.GetNetname(),
          round(c.x / 1e6, 3), round(c.y / 1e6, 3),
          'size', round(p.GetSize().x / 1e6, 2), 'x',
          round(p.GetSize().y / 1e6, 2))

filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(BOARD)
print('saved')

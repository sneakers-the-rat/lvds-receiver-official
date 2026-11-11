#!/usr/bin/env python3
"""Stage 7: clear the two new surface HV clearance items.

- HV_M2's west via (34.48,-13.1) sat 0.83 from the HV_RAW hop
  via -> via moves to (34.2,-16.6), right beside its own C53.1
  pad; In2 run and F stubs re-laid.
- C53 west 0.4 to (33.1,-15.4): its HV_M2 pad was 0.70 from
  D12's GND pad; now 1.10. GND stitch re-laid to the moved pad.
"""
import wx
_app = wx.App(False)
import pcbnew
from pcbnew import VECTOR2I, FromMM

BOARD = 'hw/pdlvds_rx.exp274.kicad_pcb'
board = pcbnew.LoadBoard(BOARD)

def P(t):
    a, b = t.GetStart(), t.GetEnd()
    return ((round(a.x / 1e6, 2), round(a.y / 1e6, 2)),
            (round(b.x / 1e6, 2), round(b.y / 1e6, 2)))

RIP = {
    ('HV_M2', ((49.3, -13.1), (34.48, -13.1))),
    ('HV_M2', ((34.48, -13.1), (37.5, -13.1))),
    ('HV_M2', ((34.48, -13.1), (34.98, -15.4))),
    ('GND', ((32.02, -15.4), (30.9, -15.4))),
    ('GND', ((30.9, -15.4), (30.9, -16.9))),
}
RIP_VIAS = {('HV_M2', (34.48, -13.1)), ('GND', (30.9, -16.9))}

victims = []
for t in board.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        c = t.GetPosition()
        key = (t.GetNetname(), (round(c.x / 1e6, 2), round(c.y / 1e6, 2)))
        if key in RIP_VIAS:
            victims.append(t)
    else:
        a, b = P(t)
        if (t.GetNetname(), (a, b)) in RIP or (t.GetNetname(), (b, a)) in RIP:
            victims.append(t)
print('ripping', len(victims), 'items')
for t in victims:
    board.Remove(t)

fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
c53 = fps['C53']
c53.SetPosition(VECTOR2I(FromMM(33.1), FromMM(-15.4)))
c53.Reference().SetPosition(VECTOR2I(FromMM(33.1), FromMM(-18.0)))
c53.Value().SetPosition(VECTOR2I(FromMM(33.1), FromMM(-12.8)))
print('C53 -> (33.1,-15.4)')

netcodes = {}
def nc(name):
    if name not in netcodes:
        netcodes[name] = board.FindNet(name).GetNetCode()
    return netcodes[name]

def trk(net, layer, a, b, w):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(VECTOR2I(FromMM(a[0]), FromMM(a[1])))
    t.SetEnd(VECTOR2I(FromMM(b[0]), FromMM(b[1])))
    t.SetWidth(FromMM(w))
    t.SetLayer(layer)
    t.SetNetCode(nc(net))
    board.Add(t)

def via(net, x, y):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(VECTOR2I(FromMM(x), FromMM(y)))
    v.SetWidth(FromMM(0.5))
    v.SetDrill(FromMM(0.3))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNetCode(nc(net))
    board.Add(v)

F, IN2 = pcbnew.F_Cu, pcbnew.In2_Cu

via('HV_M2', 34.2, -16.6)
trk('HV_M2', IN2, (49.3, -13.1), (34.2, -16.6), 0.4)
trk('HV_M2', F, (34.2, -16.6), (34.58, -15.4), 0.4)
trk('HV_M2', F, (34.2, -16.6), (37.5, -12.6), 0.4)
# C53.2 GND stitch at the moved pad (31.62,-15.4)
trk('GND', F, (31.62, -15.4), (30.5, -15.4), 0.4)
trk('GND', F, (30.5, -15.4), (30.5, -16.9), 0.4)
via('GND', 30.5, -16.9)

filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(BOARD)
print('saved')

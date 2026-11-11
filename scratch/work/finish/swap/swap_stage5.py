#!/usr/bin/env python3
"""Stage 5: fix the stage-4 leftovers on exp274.

- D11 back to (15.9,-20.25) (the west shift put its pad on the
  HV_RAW corridor); T1 instead moves east 0.2 to (34.7,-31.4) so
  the courtyards clear, and its ten attached stubs are re-laid.
- OVP2 stub: vertical at x=15.1 (lands on D10.2's pad), jog west
  at y=-20.25 into D11.1.
- T1.3 GND: stub east then south, via at (24.6,-28.6) INSIDE the
  GND zones' y>=-29.7 outline (the old via dangled outside it).
- D11.2 GND stitch follows D11 back to x=18.05.
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
    ('HV_OVP2', ((14.4, -24.75), (14.4, -21.75))),
    ('HV_OVP2', ((14.4, -21.75), (15.1, -21.75))),
    ('GND', ((17.75, -20.25), (17.75, -18.4))),
    ('HV_S1', ((21.4, -29.9), (21.4, -26.9))),
    ('HV_S2', ((21.4, -23.9), (19.6, -23.9))),
    ('GND', ((21.4, -32.9), (24.3, -32.9))),
    ('+5V', ((21.4, -38.9), (17.3, -38.9))),
    ('FLY_PRI', ((26.0, -35.9), (21.4, -35.9))),
    ('HV_S3', ((47.6, -35.9), (47.6, -32.9))),
    ('HV_S4', ((47.6, -29.9), (47.6, -26.9))),
    ('HV_SEC', ((47.6, -23.9), (47.6, -16.5))),
    ('HV_SEC', ((47.6, -16.5), (46.98, -16.5))),
    ('HV_S2', ((44.0, -38.9), (47.6, -38.9))),
}
RIP_VIAS = {('GND', (17.75, -18.4)), ('GND', (24.3, -32.9))}

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
t1 = fps['T1']
t1.SetPosition(VECTOR2I(FromMM(34.7), FromMM(-31.4)))
d11 = fps['D11']
d11.SetPosition(VECTOR2I(FromMM(15.9), FromMM(-20.25)))
d11.Reference().SetPosition(VECTOR2I(FromMM(15.9), FromMM(-16.8)))
d11.Value().SetPosition(VECTOR2I(FromMM(15.9), FromMM(-22.6)))
print('T1 -> (34.7,-31.4); D11 -> (15.9,-20.25)')

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

F = pcbnew.F_Cu

# T1 stubs at the shifted pads
trk('HV_S1', F, (21.6, -29.9), (21.6, -26.9), 0.25)
trk('HV_S2', F, (21.6, -23.9), (19.6, -23.9), 0.25)
trk('GND', F, (21.6, -32.9), (24.6, -32.9), 0.4)
trk('GND', F, (24.6, -32.9), (24.6, -28.6), 0.4)
via('GND', 24.6, -28.6)
trk('+5V', F, (21.6, -38.9), (17.3, -38.9), 0.6)
trk('FLY_PRI', F, (26.0, -35.9), (21.6, -35.9), 0.4)
trk('HV_S3', F, (47.8, -35.9), (47.8, -32.9), 0.25)
trk('HV_S4', F, (47.8, -29.9), (47.8, -26.9), 0.25)
trk('HV_SEC', F, (47.8, -23.9), (47.8, -16.5), 0.4)
trk('HV_SEC', F, (47.8, -16.5), (46.98, -16.5), 0.4)
trk('HV_S2', F, (44.0, -38.9), (47.8, -38.9), 0.25)
# OVP2: vertical on D10.2's pad column, jog into D11.1
trk('HV_OVP2', F, (15.1, -24.75), (15.1, -20.25), 0.4)
trk('HV_OVP2', F, (15.1, -20.25), (13.75, -20.25), 0.4)
# D11.2 GND stitch at the reverted position
trk('GND', F, (18.05, -20.25), (18.05, -18.4), 0.4)
via('GND', 18.05, -18.4)

filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(BOARD)
print('saved')

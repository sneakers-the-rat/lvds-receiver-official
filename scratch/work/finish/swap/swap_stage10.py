#!/usr/bin/env python3
"""Stage 10: undo the D11 displacement properly.

Root cause found by diffing against canonical: D11's canonical
centre is (17.25,-20.25), where its pad 1 clears the copied
HV_RAW corridor by ~1.1 mm. Stage 2b moved it west to clear the
NEW T1 footprint's wider courtyard, which put pad 1 at 0.15-0.93
from the corridor (9 new census pairs). Instead of displacing
D11, move T1 east: T1 -> (36.2,-31.4) puts its courtyard west
edge at 21.1, clearing canonical D11's courtyard (east edge
20.8). D11 goes home to (17.25,-20.25); its OVP2 vertical at
x=15.1 then lands on pad 1 exactly as in the original design,
and its GND stitch is re-laid at x=19.4. All T1 stubs re-laid
at the shifted pad columns (23.1 / 49.3); the GND via moves to
(26.1,-28.6), east of the shifted pads, still inside the GND
zone outline (y >= -29.7).
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
    ('HV_S1', ((21.6, -29.9), (21.6, -26.9))),
    ('HV_S2', ((21.6, -23.9), (19.6, -23.9))),
    ('GND', ((21.6, -32.9), (24.6, -32.9))),
    ('GND', ((24.6, -32.9), (24.6, -28.6))),
    ('+5V', ((21.6, -38.9), (17.3, -38.9))),
    ('FLY_PRI', ((26.0, -35.9), (21.6, -35.9))),
    ('HV_S3', ((47.8, -35.9), (47.8, -32.9))),
    ('HV_S4', ((47.8, -29.9), (47.8, -26.9))),
    ('HV_SEC', ((47.8, -23.9), (47.8, -16.5))),
    ('HV_SEC', ((47.8, -16.5), (46.98, -16.5))),
    ('HV_S2', ((44.0, -38.9), (47.8, -38.9))),
    ('HV_OVP2', ((15.1, -20.25), (13.75, -20.25))),
    ('GND', ((18.05, -20.25), (18.05, -18.4))),
}
RIP_VIAS = {('GND', (24.6, -28.6)), ('GND', (18.05, -18.4))}

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
fps['T1'].SetPosition(VECTOR2I(FromMM(36.2), FromMM(-31.4)))
d11 = fps['D11']
d11.SetPosition(VECTOR2I(FromMM(17.25), FromMM(-20.25)))
d11.Reference().SetPosition(VECTOR2I(FromMM(18.6), FromMM(-16.9)))
d11.Value().SetPosition(VECTOR2I(FromMM(17.25), FromMM(-22.6)))
print('T1 -> (36.2,-31.4); D11 -> (17.25,-20.25)')

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
trk('HV_S1', F, (23.1, -29.9), (23.1, -26.9), 0.25)
trk('HV_S2', F, (23.1, -23.9), (19.6, -23.9), 0.25)
trk('GND', F, (23.1, -32.9), (26.1, -32.9), 0.4)
trk('GND', F, (26.1, -32.9), (26.1, -28.6), 0.4)
via('GND', 26.1, -28.6)
trk('+5V', F, (23.1, -38.9), (17.3, -38.9), 0.6)
trk('FLY_PRI', F, (26.0, -35.9), (23.1, -35.9), 0.4)
trk('HV_S3', F, (49.3, -35.9), (49.3, -32.9), 0.25)
trk('HV_S4', F, (49.3, -29.9), (49.3, -26.9), 0.25)
trk('HV_SEC', F, (49.3, -23.9), (49.3, -16.5), 0.4)
trk('HV_SEC', F, (49.3, -16.5), (46.98, -16.5), 0.4)
trk('HV_S2', F, (44.0, -38.9), (49.3, -38.9), 0.25)
trk('GND', F, (19.4, -20.25), (19.4, -18.4), 0.4)
via('GND', 19.4, -18.4)

filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(BOARD)
print('saved')

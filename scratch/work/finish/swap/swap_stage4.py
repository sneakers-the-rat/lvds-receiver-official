#!/usr/bin/env python3
"""Stage 4: fix the six stage-3 DRC defects on exp274.

1. C53 (33,-13.8) sat on the +5V diagonal chain -> move to
   (33.5,-15.4); its M2 feed becomes a short diagonal from the
   (34.48,-13.1) via.
2. GND via at (18.8,-32.9) shorted HV_S2's In2 run -> T1.3's stub
   now runs east under the body, via at (24.3,-32.9).
3. +5V In2 diagonal crossed FLY_PRI's In2 vertical -> via up at
   (24.6,-18.2), west of the FLY_PRI column.
4. HV_M2's west run crossed HV_M1's vertical on F.Cu -> the run
   moves to In2 between vias at (49.3,-13.1) and (34.48,-13.1).
5. HV_RAW's D15 feed corner grazed D13.1 -> feed via (35.2,-9.4).
6. D11 touched T1's courtyard -> D11 west 0.3 to (15.6,-20.25),
   OVP2 stub re-laid at x=14.4, refdes moved clear of silk.
Plus GND stitch vias for D12.2, C53.2, D11.2 (pour islands).
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
    ('+5V', ((24.0, -20.5), (26.6, -17.6))),
    ('+5V', ((26.6, -17.6), (27.12, -17.12))),
    ('GND', ((21.4, -32.9), (18.8, -32.9))),
    ('HV_M2', ((49.3, -13.1), (34.48, -13.1))),
    ('HV_M2', ((34.48, -13.1), (34.48, -13.8))),
    ('HV_RAW', ((34.38, -11.62), (36.6, -8.3))),
    ('HV_RAW', ((36.6, -8.3), (36.6, -5.0))),
    ('HV_RAW', ((36.6, -5.0), (36.0, -5.0))),
    ('HV_OVP2', ((14.6, -24.75), (14.6, -21.75))),
    ('HV_OVP2', ((14.6, -21.75), (15.1, -21.75))),
}
RIP_VIAS = {('+5V', (26.6, -17.6)), ('GND', (18.8, -32.9))}

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
c53.SetPosition(VECTOR2I(FromMM(33.5), FromMM(-15.4)))
c53.Reference().SetPosition(VECTOR2I(FromMM(33.5), FromMM(-18.0)))
c53.Value().SetPosition(VECTOR2I(FromMM(33.5), FromMM(-12.8)))
d11 = fps['D11']
d11.SetPosition(VECTOR2I(FromMM(15.6), FromMM(-20.25)))
d11.Reference().SetPosition(VECTOR2I(FromMM(15.6), FromMM(-17.9)))
d11.Value().SetPosition(VECTOR2I(FromMM(15.6), FromMM(-22.6)))
print('C53 -> (33.5,-15.4); D11 -> (15.6,-20.25)')

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

# +5V: via up west of the FLY_PRI column
trk('+5V', IN2, (24.0, -20.5), (24.6, -18.2), 0.6)
via('+5V', 24.6, -18.2)
trk('+5V', F, (24.6, -18.2), (27.12, -17.12), 0.6)
# T1.3 GND: stub east under the body, via clear of both In2 runs
trk('GND', F, (21.4, -32.9), (24.3, -32.9), 0.4)
via('GND', 24.3, -32.9)
# HV_M2: west run buried on In2
via('HV_M2', 49.3, -13.1)
trk('HV_M2', IN2, (49.3, -13.1), (34.48, -13.1), 0.4)
via('HV_M2', 34.48, -13.1)
trk('HV_M2', F, (34.48, -13.1), (37.5, -13.1), 0.4)
trk('HV_M2', F, (34.48, -13.1), (34.98, -15.4), 0.4)
# HV_RAW: D15.1 feed via (35.2,-9.4)
trk('HV_RAW', F, (34.38, -11.62), (35.2, -9.4), 0.4)
trk('HV_RAW', F, (35.2, -9.4), (35.2, -5.0), 0.4)
# GND stitches for the pour-island pads
trk('GND', F, (37.5, -16.5), (37.5, -19.6), 0.4)
via('GND', 37.5, -19.6)
trk('GND', F, (32.02, -15.4), (30.9, -15.4), 0.4)
trk('GND', F, (30.9, -15.4), (30.9, -16.9), 0.4)
via('GND', 30.9, -16.9)
trk('GND', F, (17.75, -20.25), (17.75, -18.4), 0.4)
via('GND', 17.75, -18.4)
# OVP2 stub re-laid for the moved D11
trk('HV_OVP2', F, (14.4, -24.75), (14.4, -21.75), 0.4)
trk('HV_OVP2', F, (14.4, -21.75), (15.1, -21.75), 0.4)

filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(BOARD)
print('saved')

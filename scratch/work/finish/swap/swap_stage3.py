#!/usr/bin/env python3
"""Stage 3: route the swap district on exp274.

- C53 shifts south to (33,-13.8) so the copied HV_RAW In2-hop via
  at (34.38,-11.62) clears its pad.
- HV_RAW's ripped middle is re-laid with the ORIGINAL board's own
  geometry copied from hw/pdlvds_rx.kicad_pcb (corridor chain,
  R29 branch, In2 hop, C32 stub; the old D5 stub is excluded) and
  D15.1 is fed from that hop via.
- Everything else is new routing per the v4 plan (see commit msg).
- Zones are refilled at the end so the GND pour re-cuts around the
  new pads.
"""
import wx
_app = wx.App(False)
import pcbnew
from pcbnew import VECTOR2I, FromMM

BOARD = 'hw/pdlvds_rx.exp274.kicad_pcb'
CANON = 'hw/pdlvds_rx.kicad_pcb'
board = pcbnew.LoadBoard(BOARD)

# C53 south
fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
c53 = fps['C53']
c53.SetPosition(VECTOR2I(FromMM(33.0), FromMM(-13.8)))
c53.Reference().SetPosition(VECTOR2I(FromMM(33.0), FromMM(-16.4)))
c53.Value().SetPosition(VECTOR2I(FromMM(33.0), FromMM(-11.2)))
print('C53 -> (33,-13.8)')

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

# --- transformer string links (F.Cu, 0.25) ---
trk('HV_S1', F, (21.4, -29.9), (21.4, -26.9), 0.25)
trk('HV_S3', F, (47.6, -35.9), (47.6, -32.9), 0.25)
trk('HV_S4', F, (47.6, -29.9), (47.6, -26.9), 0.25)
# --- HV_S2: west stub, In2 south+east, east stub ---
trk('HV_S2', F, (21.4, -23.9), (19.6, -23.9), 0.25)
trk('HV_S2', F, (19.6, -23.9), (18.6, -22.9), 0.25)
via('HV_S2', 18.6, -22.9)
trk('HV_S2', IN2, (18.6, -22.9), (18.6, -38.9), 0.25)
trk('HV_S2', IN2, (18.6, -38.9), (44.0, -38.9), 0.25)
via('HV_S2', 44.0, -38.9)
trk('HV_S2', F, (44.0, -38.9), (47.6, -38.9), 0.25)
# --- T1.3 GND stub + via to the In1 plane ---
trk('GND', F, (21.4, -32.9), (18.8, -32.9), 0.4)
via('GND', 18.8, -32.9)
# --- +5V: west stub, In2 around, join the surviving chain end ---
trk('+5V', F, (21.4, -38.9), (17.3, -38.9), 0.6)
via('+5V', 17.3, -38.9)
trk('+5V', IN2, (17.3, -38.9), (17.3, -20.5), 0.6)
trk('+5V', IN2, (17.3, -20.5), (24.0, -20.5), 0.6)
trk('+5V', IN2, (24.0, -20.5), (26.6, -17.6), 0.6)
via('+5V', 26.6, -17.6)
trk('+5V', F, (26.6, -17.6), (27.12, -17.12), 0.6)
# --- FLY_PRI: Q1.3 east, In2 north, west stub into T1.2 ---
trk('FLY_PRI', F, (22.94, -16.0), (26.0, -16.0), 0.4)
via('FLY_PRI', 26.0, -16.0)
trk('FLY_PRI', IN2, (26.0, -16.0), (26.0, -35.9), 0.4)
via('FLY_PRI', 26.0, -35.9)
trk('FLY_PRI', F, (26.0, -35.9), (21.4, -35.9), 0.4)
# --- HV_SEC: T1.7 south into C52.1 ---
trk('HV_SEC', F, (47.6, -23.9), (47.6, -16.5), 0.4)
trk('HV_SEC', F, (47.6, -16.5), (46.98, -16.5), 0.4)
# --- HV_M1 web ---
trk('HV_M1', F, (44.02, -16.5), (41.5, -16.5), 0.4)
trk('HV_M1', F, (41.5, -16.5), (41.5, -11.0), 0.4)
trk('HV_M1', F, (41.5, -11.0), (44.02, -11.0), 0.4)
# --- HV_M2 web: D14.2 east, south, long west run, two risers ---
trk('HV_M2', F, (47.5, -5.0), (49.3, -5.0), 0.4)
trk('HV_M2', F, (49.3, -5.0), (49.3, -13.1), 0.4)
trk('HV_M2', F, (49.3, -13.1), (34.48, -13.1), 0.4)
trk('HV_M2', F, (37.5, -13.1), (37.5, -11.0), 0.4)
trk('HV_M2', F, (34.48, -13.1), (34.48, -13.8), 0.4)
# --- HV_M3 web ---
trk('HV_M3', F, (40.0, -5.0), (43.5, -5.0), 0.4)
trk('HV_M3', F, (46.98, -11.0), (46.98, -7.1), 0.4)
trk('HV_M3', F, (46.98, -7.1), (43.5, -7.1), 0.4)
trk('HV_M3', F, (43.5, -7.1), (43.5, -5.0), 0.4)
# --- HV_RAW: copy the original board's ripped geometry ---
canon = pcbnew.LoadBoard(CANON)
skip_pts = {(35.0, -12.0), (35.5, -12.0)}
copied = 0
for t in canon.GetTracks():
    if t.GetNetname() != 'HV_RAW':
        continue
    a, b = t.GetStart(), t.GetEnd()
    pa = (round(a.x / 1e6, 2), round(a.y / 1e6, 2))
    pb = (round(b.x / 1e6, 2), round(b.y / 1e6, 2))
    if not all(9.8 <= x <= 36.5 and -22.5 <= y <= 0 for x, y in (pa, pb)):
        continue
    if pa in skip_pts or pb in skip_pts:
        continue
    if t.Type() == pcbnew.PCB_VIA_T:
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(a)
        v.SetWidth(t.GetWidth())
        v.SetDrill(t.GetDrillValue())
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNetCode(nc('HV_RAW'))
        board.Add(v)
    else:
        nt = pcbnew.PCB_TRACK(board)
        nt.SetStart(a)
        nt.SetEnd(b)
        nt.SetWidth(t.GetWidth())
        nt.SetLayer(t.GetLayer())
        nt.SetNetCode(nc('HV_RAW'))
        board.Add(nt)
    copied += 1
print('HV_RAW copied originals:', copied)
# --- HV_RAW: feed D15.1 from the hop via ---
trk('HV_RAW', F, (34.38, -11.62), (36.6, -8.3), 0.4)
trk('HV_RAW', F, (36.6, -8.3), (36.6, -5.0), 0.4)
trk('HV_RAW', F, (36.6, -5.0), (36.0, -5.0), 0.4)

# --- refill zones ---
filler = pcbnew.ZONE_FILLER(board)
zones = board.Zones()
filler.Fill(zones)
board.Save(BOARD)
print('saved with refilled zones')

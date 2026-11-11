#!/usr/bin/env python3
"""Stage 1 of the T1 swap (docs/11, docs/12): on exp274, rip the HV
district copper that the swap invalidates, remove D5, replace T1's
footprint with WEFLEXHV_EFD20_12 at the same centre/rotation, and
place the CW ladder parts (D12-D15, C52-C54) unrouted.

Rip rules (district box x[10,56] y[-46,-4]):
  * any track/via on FLY_PRI / HV_SEC / HV_RAW inside the box;
  * any track/via intersecting the new T1 courtyard + 0.6 mm;
  * any track/via touching an old T1 or D5 pad (+0.3 mm).
Removals follow the house law: find everything, then remove
everything, then add everything. Netcodes are captured before any
removal. Field (reference/value) positions are copied from the old
T1 footprint to the new one.
"""
import sys
import wx
_app = wx.App(False)
import pcbnew
from pcbnew import VECTOR2I, FromMM

BOARD = 'hw/pdlvds_rx.exp274.kicad_pcb'
MM = 1e6

def mm(v):
    return v / MM

def seg_bbox(t):
    a, b = t.GetStart(), t.GetEnd()
    return (min(mm(a.x), mm(b.x)), min(mm(a.y), mm(b.y)),
            max(mm(a.x), mm(b.x)), max(mm(a.y), mm(b.y)))

def hit(b1, b2):
    return not (b1[2] < b2[0] or b2[2] < b1[0] or b1[3] < b2[1] or b2[3] < b1[1])

board = pcbnew.LoadBoard(BOARD)

# ---- capture netcodes first -------------------------------------------
NETS = ['+5V', 'FLY_PRI', 'GND', 'HV_S1', 'HV_S2', 'HV_S3', 'HV_S4',
        'HV_SEC', 'HV_M1', 'HV_M2', 'HV_M3', 'HV_RAW']
netinfo = {}
for n in NETS:
    ni = board.FindNet(n)
    if ni is None:
        # new nets do not exist on the board yet; create them
        ni = pcbnew.NETINFO_ITEM(board, n)
        board.Add(ni)
    netinfo[n] = ni.GetNetCode()
print('netcodes:', {n: netinfo[n] for n in NETS})

fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
t1_old, d5_old = fps['T1'], fps['D5']
t1_pos = t1_old.GetPosition()
t1_rot = t1_old.GetOrientationDegrees()
print('old T1 at', mm(t1_pos.x), mm(t1_pos.y), 'rot', t1_rot)
ref_field_pos = t1_old.Reference().GetPosition()
val_field_pos = t1_old.Value().GetPosition()

# ---- collect removals --------------------------------------------------
BOX = (10.0, -46.0, 56.0, -4.0)
NEWCT = (32.90 - 15.10 - 0.6, -31.40 - 11.00 - 0.6,
         32.90 + 15.10 + 0.6, -31.40 + 11.00 + 0.6)
pad_boxes = []
for fp in (t1_old, d5_old):
    for pad in fp.Pads():
        c = pad.GetPosition()
        s = pad.GetSize()
        pad_boxes.append((mm(c.x) - mm(s.x) / 2 - 0.3, mm(c.y) - mm(s.y) / 2 - 0.3,
                          mm(c.x) + mm(s.x) / 2 + 0.3, mm(c.y) + mm(s.y) / 2 + 0.3))

rip = []
for t in board.GetTracks():
    net = t.GetNetname()
    b = seg_bbox(t)
    why = None
    if net in ('FLY_PRI', 'HV_SEC', 'HV_RAW') and hit(b, BOX):
        why = 'district net ' + net
    elif hit(b, NEWCT):
        why = 'under new T1'
    elif any(hit(b, pb) for pb in pad_boxes):
        why = 'touches old T1/D5 pad'
    if why:
        rip.append((t, net, why))
print('ripping', len(rip), 'tracks/vias')
for t, net, why in rip:
    print('  rip', net, why, [round(v, 2) for v in seg_bbox(t)])
    board.Remove(t)
board.Remove(d5_old)
board.Remove(t1_old)

# ---- add new T1 ---------------------------------------------------------
t1 = pcbnew.FootprintLoad('hw/pdlvds.pretty', 'WEFLEXHV_EFD20_12')
t1.SetReference('T1')
t1.SetValue('Wurth WE-FLEX HV 749196518 1:5 (N1 pri, N2-N6 sec series)')
t1.SetPosition(t1_pos)
t1.SetOrientationDegrees(t1_rot)
t1.Reference().SetPosition(ref_field_pos)
t1.Value().SetPosition(val_field_pos)
board.Add(t1)
T1_PINS = {'1': '+5V', '2': 'FLY_PRI', '3': 'GND', '4': 'HV_S1',
           '5': 'HV_S1', '6': 'HV_S2', '12': 'HV_S2', '11': 'HV_S3',
           '10': 'HV_S3', '9': 'HV_S4', '8': 'HV_S4', '7': 'HV_SEC'}
for pad in t1.Pads():
    pad.SetNetCode(netinfo[T1_PINS[pad.GetNumber()]])
print('T1 placed; pads:')
for pad in t1.Pads():
    c = pad.GetPosition()
    print('  ', pad.GetNumber(), pad.GetNetname(), round(mm(c.x), 2), round(mm(c.y), 2))

# ---- add ladder parts ---------------------------------------------------
DIODE_LIB = '/usr/share/kicad/footprints/Diode_SMD.pretty'
CAP_LIB = '/usr/share/kicad/footprints/Capacitor_SMD.pretty'

def place(ref, lib, name, value, x, y, pin1_side, pinmap):
    """pin1_side: 'E' or 'W' — the side pin 1 must end up on (rot 0/180)."""
    fp = pcbnew.FootprintLoad(lib, name)
    fp.SetReference(ref)
    fp.SetValue(value)
    p1 = [p for p in fp.Pads() if p.GetNumber() == '1'][0]
    off = p1.GetPosition()  # relative to origin before placement
    rot = 0 if (off.x < 0) == (pin1_side == 'W') else 180
    fp.SetOrientationDegrees(rot)
    fp.SetPosition(VECTOR2I(FromMM(x), FromMM(y)))
    fp.Reference().SetPosition(VECTOR2I(FromMM(x), FromMM(y - 2.6)))
    fp.Value().SetPosition(VECTOR2I(FromMM(x), FromMM(y + 2.6)))
    board.Add(fp)
    for pad in fp.Pads():
        pad.SetNetCode(netinfo[pinmap[pad.GetNumber()]])
    print(ref, 'rot', rot, 'at', x, y)
    for pad in fp.Pads():
        c = pad.GetPosition()
        print('   ', pad.GetNumber(), pad.GetNetname(), round(mm(c.x), 2), round(mm(c.y), 2))
    return fp

# diodes: pin 1 = K. Want: D12 K east, D13 K west, D14 K west, D15 K west.
place('D12', DIODE_LIB, 'D_SMA', 'ES1J', 40.5, -17.0, 'E', {'1': 'HV_M1', '2': 'GND'})
place('D13', DIODE_LIB, 'D_SMA', 'ES1J', 40.5, -12.5, 'W', {'1': 'HV_M2', '2': 'HV_M1'})
place('D14', DIODE_LIB, 'D_SMA', 'ES1J', 36.5, -21.5, 'W', {'1': 'HV_M3', '2': 'HV_M2'})
place('D15', DIODE_LIB, 'D_SMA', 'ES1J', 32.0, -21.5, 'W', {'1': 'HV_RAW', '2': 'HV_M3'})
# caps: pin 1 side per plan: C52 p1 east, C53 p1 east, C54 p1 west.
place('C52', CAP_LIB, 'C_1206_3216Metric', '100nF 630V', 44.0, -17.0, 'E', {'1': 'HV_SEC', '2': 'HV_M1'})
place('C53', CAP_LIB, 'C_1206_3216Metric', '100nF 630V', 36.5, -12.5, 'E', {'1': 'HV_M2', '2': 'GND'})
place('C54', CAP_LIB, 'C_1206_3216Metric', '100nF 630V', 40.5, -21.5, 'W', {'1': 'HV_M1', '2': 'HV_M3'})

board.Save(BOARD)
print('saved', BOARD)

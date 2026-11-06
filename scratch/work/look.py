"""Look at a board window: pads, tracks, vias, footprints.
Usage: look.py BOARD X0 X1 Y0 Y1 [NETFILTER]
Coords in mm, KiCad native orientation (y down-positive as stored).
"""
import sys
sys.path.insert(0, 'hw')
import pcbnew

MM = pcbnew.ToMM
board = pcbnew.LoadBoard(sys.argv[1])
X0, X1, Y0, Y1 = map(float, sys.argv[2:6])
netf = sys.argv[6] if len(sys.argv) > 6 else None

def inwin(x, y, pad=0.0):
    return X0 - pad <= x <= X1 + pad and Y0 - pad <= y <= Y1 + pad

print('== FOOTPRINTS ==')
for fp in board.GetFootprints():
    p = fp.GetPosition()
    x, y = MM(p.x), MM(p.y)
    if inwin(x, y, 6):
        print(f"{fp.GetReference()} at ({x:.2f},{y:.2f}) rot {fp.GetOrientationDegrees():.0f}")

print('== PADS ==')
for fp in board.GetFootprints():
    ref = fp.GetReference()
    for pad in fp.Pads():
        p = pad.GetPosition()
        x, y = MM(p.x), MM(p.y)
        if not inwin(x, y):
            continue
        net = pad.GetNetname()
        if netf and net != netf:
            continue
        sz = pad.GetSize()
        print(f"{ref}.{pad.GetNumber()} [{net}] ({x:.3f},{y:.3f}) size {MM(sz.x):.2f}x{MM(sz.y):.2f} layers {pad.GetLayerSet().FmtHex()} drill {MM(pad.GetDrillSize().x):.2f}")

print('== TRACKS/VIAS ==')
for t in board.GetTracks():
    net = t.GetNetname()
    if netf and net != netf:
        continue
    s, e = t.GetStart(), t.GetEnd()
    x1, y1, x2, y2 = MM(s.x), MM(s.y), MM(e.x), MM(e.y)
    if not (inwin(x1, y1, 1) or inwin(x2, y2, 1)):
        continue
    lay = board.GetLayerName(t.GetLayer())
    if t.Type() == pcbnew.PCB_VIA_T:
        print(f"VIA [{net}] ({x1:.3f},{y1:.3f}) d {MM(t.GetWidth()):.2f} drill {MM(t.GetDrillValue()):.2f}")
    else:
        print(f"TRK [{net}] {lay} ({x1:.3f},{y1:.3f})->({x2:.3f},{y2:.3f}) w {MM(t.GetWidth()):.2f}")

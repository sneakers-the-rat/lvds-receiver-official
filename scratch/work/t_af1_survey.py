"""t_af1: full survey of the U7 east-face ULPI district on exp216.

Dumps every pad/track/via intersecting a box, plus the COMPLETE
track lists for ULPI_D2..D7 (anchors and staircase templates).
Usage: xvfb-run -a python3 scratch/work/t_af1_survey.py BOARD X0 X1 Y0 Y1
"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew

src = sys.argv[1]
X0, X1, Y0, Y1 = map(float, sys.argv[2:6])
board = pcbnew.LoadBoard(src)
LN = {pcbnew.F_Cu: 'F', pcbnew.In1_Cu: 'In1', pcbnew.In2_Cu: 'In2',
      pcbnew.B_Cu: 'B'}

def mm(v):
    return pcbnew.ToMM(v)

print('=== PADS in box ===')
for fp in board.GetFootprints():
    ref = fp.GetReference()
    for pad in fp.Pads():
        x, y = mm(pad.GetPosition())
        if X0 <= x <= X1 and Y0 <= y <= Y1:
            sx, sy = mm(pad.GetSize())
            print(f"pad {ref}.{pad.GetNumber()} [{pad.GetNetname()}] "
                  f"@({x:.3f},{y:.3f}) size {sx:.2f}x{sy:.2f} "
                  f"rot {pad.GetOrientationDegrees():.0f}")

print('=== TRACKS/VIAS intersecting box ===')
for t in board.GetTracks():
    net = t.GetNetname()
    if isinstance(t, pcbnew.PCB_VIA):
        x, y = mm(t.GetPosition())
        if X0 <= x <= X1 and Y0 <= y <= Y1:
            print(f"via [{net}] @({x:.3f},{y:.3f}) d{mm(t.GetWidth()):.2f}")
    else:
        a = mm(t.GetStart()); b = mm(t.GetEnd())
        if (X0 <= a[0] <= X1 and Y0 <= a[1] <= Y1) or \
           (X0 <= b[0] <= X1 and Y0 <= b[1] <= Y1):
            print(f"seg [{net}] {LN[t.GetLayer()]} "
                  f"({a[0]:.3f},{a[1]:.3f})->({b[0]:.3f},{b[1]:.3f}) "
                  f"w{mm(t.GetWidth()):.2f}")

for want in ('ULPI_D2', 'ULPI_D3', 'ULPI_D4', 'ULPI_D5', 'ULPI_D6',
             'ULPI_D7'):
    print(f'=== ALL items [{want}] ===')
    for t in board.GetTracks():
        if t.GetNetname() != want:
            continue
        if isinstance(t, pcbnew.PCB_VIA):
            x, y = mm(t.GetPosition())
            print(f"via @({x:.3f},{y:.3f}) d{mm(t.GetWidth()):.2f}")
        else:
            a = mm(t.GetStart()); b = mm(t.GetEnd())
            print(f"seg {LN[t.GetLayer()]} "
                  f"({a[0]:.3f},{a[1]:.3f})->({b[0]:.3f},{b[1]:.3f}) "
                  f"w{mm(t.GetWidth()):.2f}")
print('done')

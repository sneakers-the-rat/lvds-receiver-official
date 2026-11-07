"""t_ac0: full track-dump survey of a box on a saved board.

Usage: xvfb-run -a python3 scratch/work/t_ac0_survey.py BOARD X0 X1 Y0 Y1 [NET ...]
Prints pads, tracks, vias whose geometry intersects the box.
If NETs given, additionally prints the complete copper of those nets
board-wide (the template journey).
"""
import sys
sys.path.insert(0, 'hw')
import wx
import pcbnew

_app = wx.App(False)
src = sys.argv[1]
X0, X1, Y0, Y1 = map(float, sys.argv[2:6])
nets = set(sys.argv[6:])
board = pcbnew.LoadBoard(src)
LAY = {pcbnew.F_Cu: 'F', pcbnew.In1_Cu: 'In1', pcbnew.In2_Cu: 'In2',
       pcbnew.B_Cu: 'B'}

def mm(v):
    return pcbnew.ToMM(v)

def inb(x, y):
    return X0 - 1 <= x <= X1 + 1 and Y0 - 1 <= y <= Y1 + 1

print('=== PADS in box ===')
for fp in board.GetFootprints():
    ref = fp.GetReference()
    for pad in fp.Pads():
        p = mm(pad.GetPosition())
        if inb(p[0], p[1]):
            s = mm(pad.GetSize())
            print(f'pad {ref}.{pad.GetNumber()} [{pad.GetNetname()}] '
                  f'@({p[0]:.3f},{p[1]:.3f}) size {s[0]:.2f}x{s[1]:.2f} '
                  f'rot {pad.GetOrientationDegrees():.0f}')

print('=== TRACKS/VIAS intersecting box ===')
for t in board.GetTracks():
    net = t.GetNetname()
    if t.Type() == pcbnew.PCB_VIA_T:
        p = mm(t.GetPosition())
        if inb(p[0], p[1]):
            print(f'via [{net}] @({p[0]:.3f},{p[1]:.3f}) d{mm(t.GetWidth()):.2f}')
    else:
        a = mm(t.GetStart()); b = mm(t.GetEnd())
        if inb(*a) or inb(*b):
            print(f'seg [{net}] {LAY.get(t.GetLayer(), t.GetLayer())} '
                  f'({a[0]:.3f},{a[1]:.3f})->({b[0]:.3f},{b[1]:.3f}) '
                  f'w{mm(t.GetWidth()):.2f}')

if nets:
    print('=== FULL COPPER of named nets ===')
    for t in board.GetTracks():
        net = t.GetNetname()
        if net not in nets:
            continue
        if t.Type() == pcbnew.PCB_VIA_T:
            p = mm(t.GetPosition())
            print(f'via [{net}] @({p[0]:.3f},{p[1]:.3f}) d{mm(t.GetWidth()):.2f}')
        else:
            a = mm(t.GetStart()); b = mm(t.GetEnd())
            print(f'seg [{net}] {LAY.get(t.GetLayer(), t.GetLayer())} '
                  f'({a[0]:.3f},{a[1]:.3f})->({b[0]:.3f},{b[1]:.3f}) '
                  f'w{mm(t.GetWidth()):.2f}')
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        for pad in fp.Pads():
            if pad.GetNetname() in nets:
                p = mm(pad.GetPosition())
                print(f'pad {ref}.{pad.GetNumber()} [{pad.GetNetname()}] '
                      f'@({p[0]:.3f},{p[1]:.3f})')

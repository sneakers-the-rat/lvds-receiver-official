"""t_ai1: full dump of pads + tracks + vias in a box on a given board,
plus global positions of named pads. Usage:
  t_ai1_dump.py board X0 X1 Y0 Y1 [ref.pad ...]"""
import math, sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew

SRC = sys.argv[1]
X0, X1, Y0, Y1 = map(float, sys.argv[2:6])
WANT = set(sys.argv[6:])
LN = {pcbnew.F_Cu: 'F', pcbnew.In1_Cu: 'In1', pcbnew.In2_Cu: 'In2',
      pcbnew.B_Cu: 'B'}
board = pcbnew.LoadBoard(SRC)

def inbox(x, y):
    return X0 <= x <= X1 and Y0 <= y <= Y1

print('=== PADS in box ===')
for fp in board.GetFootprints():
    for pad in fp.Pads():
        p = pcbnew.ToMM(pad.GetPosition())
        desc = f'{fp.GetReference()}.{pad.GetNumber()}'
        if inbox(*p) or desc in WANT:
            s = pcbnew.ToMM(pad.GetSize())
            print(f'  {desc} [{pad.GetNetname()}] ({p[0]:.3f},{p[1]:.3f}) '
                  f'{s[0]:.2f}x{s[1]:.2f} rot{pad.GetOrientationDegrees():.0f}')
print('=== TRACKS/VIAS in box ===')
for t in board.GetTracks():
    net = t.GetNetname()
    if isinstance(t, pcbnew.PCB_VIA):
        p = pcbnew.ToMM(t.GetPosition())
        if inbox(*p):
            try:
                w = pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu))
            except Exception:
                w = pcbnew.ToMM(t.GetWidth())
            print(f'  VIA [{net}] ({p[0]:.3f},{p[1]:.3f}) d{w:.2f} '
                  f'drill{pcbnew.ToMM(t.GetDrillValue()):.2f}')
    else:
        a = pcbnew.ToMM(t.GetStart())
        b = pcbnew.ToMM(t.GetEnd())
        if inbox(*a) or inbox(*b):
            print(f'  SEG {LN.get(t.GetLayer(), "?")} [{net}] '
                  f'({a[0]:.3f},{a[1]:.3f})->({b[0]:.3f},{b[1]:.3f}) '
                  f'w{pcbnew.ToMM(t.GetWidth()):.2f}')

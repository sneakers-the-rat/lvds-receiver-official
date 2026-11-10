"""t_az2: full track/via inventory intersecting the quadrant box
x[69,81], y[3,22], grouped by layer. Read-only."""
import sys
sys.path.insert(0, 'hw')
import pcbnew
import wx
_app = wx.App(False)

B = pcbnew.LoadBoard('hw/pdlvds_rx.exp251.kicad_pcb')
MM = 1e6
LAY = {pcbnew.F_Cu: 'F', pcbnew.In1_Cu: 'In1', pcbnew.In2_Cu: 'In2',
       pcbnew.B_Cu: 'B'}
X0, X1, Y0, Y1 = 69.0, 81.0, 3.0, 22.0

def mm(v):
    return (v.x / MM, v.y / MM)

for layname in ('F', 'In2', 'B'):
    print(f'=== {layname} ===')
    out = []
    for t in B.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            x, y = mm(t.GetPosition())
            if X0 - 1 <= x <= X1 + 1 and Y0 - 1 <= y <= Y1 + 1:
                out.append((y, x, f'VIA {t.GetNetname()} ({x:.3f},{y:.3f}) '
                                  f'd={pcbnew.ToMM(t.GetWidth()):.2f}'))
        else:
            if LAY.get(t.GetLayer()) != layname:
                continue
            a, b = mm(t.GetStart()), mm(t.GetEnd())
            if (min(a[0], b[0]) <= X1 and max(a[0], b[0]) >= X0
                    and min(a[1], b[1]) <= Y1 and max(a[1], b[1]) >= Y0):
                out.append((min(a[1], b[1]), min(a[0], b[0]),
                            f'SEG {t.GetNetname()} ({a[0]:.3f},{a[1]:.3f})'
                            f'->({b[0]:.3f},{b[1]:.3f}) '
                            f'w={pcbnew.ToMM(t.GetWidth()):.3f}'))
    for _, _, s in sorted(out):
        print(s)
print('=== done ===')

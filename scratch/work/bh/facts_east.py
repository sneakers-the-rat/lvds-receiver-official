#!/usr/bin/env python3
"""bh facts east: items in box x[76.2,78.8] y[4.5,17.8] of exp257 (In2/B/vias + F)."""
import wx
_app = wx.App(False)
import pcbnew

B = '/home/hatch/workspace/pdlvds-route/hw/pdlvds_rx.exp257.kicad_pcb'
OUT = '/home/hatch/workspace/pdlvds-route/scratch/work/bh/facts_east_out.txt'
IU = 1e6
b = pcbnew.LoadBoard(B)
LN = {pcbnew.F_Cu: 'F', pcbnew.In1_Cu: 'In1', pcbnew.In2_Cu: 'In2', pcbnew.B_Cu: 'B'}
BOX = (76.2, 4.5, 78.8, 17.8)
lines = []
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        p = t.GetPosition()
        x, y = p.x / IU, p.y / IU
        if BOX[0] - 0.4 <= x <= BOX[2] + 0.4 and BOX[1] - 0.4 <= y <= BOX[3] + 0.4:
            lines.append(f"VIA {t.GetNetname()} @({x:.3f},{y:.3f}) d{t.GetWidth()/IU:.2f}")
    else:
        s, e = t.GetStart(), t.GetEnd()
        pts = [(s.x / IU, s.y / IU), (e.x / IU, e.y / IU)]
        if max(p[0] for p in pts) >= BOX[0] - 0.4 and min(p[0] for p in pts) <= BOX[2] + 0.4 and \
           max(p[1] for p in pts) >= BOX[1] - 0.4 and min(p[1] for p in pts) <= BOX[3] + 0.4:
            lines.append(f"{LN[t.GetLayer()]} {t.GetNetname()} "
                         f"({pts[0][0]:.3f},{pts[0][1]:.3f})->({pts[1][0]:.3f},{pts[1][1]:.3f}) "
                         f"w{t.GetWidth()/IU:.2f}")
with open(OUT, 'w') as f:
    f.write('\n'.join(lines) + '\n')
print('wrote', OUT, len(lines), 'lines')

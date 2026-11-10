#!/usr/bin/env python3
"""bh facts: B-layer items + all vias in box x[66.5,74.6] y[3.8,17.2] of exp257."""
import wx
_app = wx.App(False)
import pcbnew

B = '/home/hatch/workspace/pdlvds-route/hw/pdlvds_rx.exp257.kicad_pcb'
OUT = '/home/hatch/workspace/pdlvds-route/scratch/work/bh/facts_west_b_out.txt'
IU = 1e6
b = pcbnew.LoadBoard(B)
BOX = (66.5, 3.8, 74.6, 17.2)
L = []
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        p = t.GetPosition()
        x, y = p.x / IU, p.y / IU
        if BOX[0] - 0.4 <= x <= BOX[2] + 0.4 and BOX[1] - 0.4 <= y <= BOX[3] + 0.4:
            L.append(f"VIA {t.GetNetname()} @({x:.3f},{y:.3f}) d{t.GetWidth()/IU:.2f}")
    elif t.GetLayer() == pcbnew.B_Cu:
        s, e = t.GetStart(), t.GetEnd()
        pts = [(s.x / IU, s.y / IU), (e.x / IU, e.y / IU)]
        if max(p[0] for p in pts) >= BOX[0] - 0.4 and min(p[0] for p in pts) <= BOX[2] + 0.4 and \
           max(p[1] for p in pts) >= BOX[1] - 0.4 and min(p[1] for p in pts) <= BOX[3] + 0.4:
            L.append(f"B {t.GetNetname()} ({pts[0][0]:.3f},{pts[0][1]:.3f})->"
                     f"({pts[1][0]:.3f},{pts[1][1]:.3f}) w{t.GetWidth()/IU:.2f}")
with open(OUT, 'w') as f:
    f.write('\n'.join(L) + '\n')
print('wrote', len(L), 'lines')

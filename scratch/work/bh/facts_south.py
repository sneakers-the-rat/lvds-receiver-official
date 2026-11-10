#!/usr/bin/env python3
"""bh facts south: ULPI_NXT/ULPI_DIR F geometry + B items x[68,75.6] y[16.8,20.6]."""
import wx
_app = wx.App(False)
import pcbnew

B = '/home/hatch/workspace/pdlvds-route/hw/pdlvds_rx.exp257.kicad_pcb'
OUT = '/home/hatch/workspace/pdlvds-route/scratch/work/bh/facts_south_out.txt'
IU = 1e6
b = pcbnew.LoadBoard(B)
LN = {pcbnew.F_Cu: 'F', pcbnew.In1_Cu: 'In1', pcbnew.In2_Cu: 'In2', pcbnew.B_Cu: 'B'}
L = ['== ULPI_NXT / ULPI_DIR all tracks+vias:']
for t in b.GetTracks():
    if t.GetNetname() not in ('ULPI_NXT', 'ULPI_DIR'):
        continue
    if isinstance(t, pcbnew.PCB_VIA):
        p = t.GetPosition()
        L.append(f"  VIA {t.GetNetname()} @({p.x/IU:.3f},{p.y/IU:.3f}) d{t.GetWidth()/IU:.2f}")
    else:
        s, e = t.GetStart(), t.GetEnd()
        L.append(f"  {LN[t.GetLayer()]} {t.GetNetname()} ({s.x/IU:.3f},{s.y/IU:.3f})->"
                 f"({e.x/IU:.3f},{e.y/IU:.3f}) w{t.GetWidth()/IU:.2f}")
L.append('== B items + vias in x[68,75.6] y[16.8,20.6]:')
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        p = t.GetPosition()
        x, y = p.x / IU, p.y / IU
        if 67.6 <= x <= 76.0 and 16.4 <= y <= 21.0:
            L.append(f"  VIA {t.GetNetname()} @({x:.3f},{y:.3f}) d{t.GetWidth()/IU:.2f}")
    elif t.GetLayer() == pcbnew.B_Cu:
        s, e = t.GetStart(), t.GetEnd()
        pts = [(s.x / IU, s.y / IU), (e.x / IU, e.y / IU)]
        if max(p[0] for p in pts) >= 67.6 and min(p[0] for p in pts) <= 76.0 and \
           max(p[1] for p in pts) >= 16.4 and min(p[1] for p in pts) <= 21.0:
            L.append(f"  B {t.GetNetname()} ({pts[0][0]:.3f},{pts[0][1]:.3f})->"
                     f"({pts[1][0]:.3f},{pts[1][1]:.3f}) w{t.GetWidth()/IU:.2f}")
with open(OUT, 'w') as f:
    f.write('\n'.join(L) + '\n')
print('wrote', len(L), 'lines')

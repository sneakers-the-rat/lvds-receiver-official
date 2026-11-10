#!/usr/bin/env python3
"""bh questions: RBIAS south termination; pad at (74.97,14.0); XI B ride."""
import wx
_app = wx.App(False)
import pcbnew

B = '/home/hatch/workspace/pdlvds-route/hw/pdlvds_rx.exp257.kicad_pcb'
OUT = '/home/hatch/workspace/pdlvds-route/scratch/work/bh/facts_q_out.txt'
IU = 1e6
b = pcbnew.LoadBoard(B)
LN = {pcbnew.F_Cu: 'F', pcbnew.In1_Cu: 'In1', pcbnew.In2_Cu: 'In2', pcbnew.B_Cu: 'B'}
L = []
L.append('== footprint pads with bbox near (74.97,14.0) ( +-1.2 ):')
for fp in b.GetFootprints():
    for p in fp.Pads():
        bb = p.GetBoundingBox()
        cx, cy = (bb.GetLeft() + bb.GetRight()) / 2 / IU, (bb.GetTop() + bb.GetBottom()) / 2 / IU
        if abs(cx - 74.97) < 1.2 and abs(cy - 14.0) < 1.2:
            L.append(f"  {fp.GetReference()}.{p.GetNumber()} net='{p.GetNetname()}' "
                     f"bbox ({bb.GetLeft()/IU:.3f},{bb.GetTop()/IU:.3f})-"
                     f"({bb.GetRight()/IU:.3f},{bb.GetBottom()/IU:.3f})")
L.append('== RBIAS items with any point in x[73.2,74.6] y[10.6,12.6]:')
for t in b.GetTracks():
    if t.GetNetname() != 'RBIAS':
        continue
    if isinstance(t, pcbnew.PCB_VIA):
        p = t.GetPosition()
        if 73.2 <= p.x / IU <= 74.6 and 10.6 <= p.y / IU <= 12.6:
            L.append(f"  VIA @({p.x/IU:.3f},{p.y/IU:.3f}) d{t.GetWidth()/IU:.2f}")
    else:
        s, e = t.GetStart(), t.GetEnd()
        pts = [(s.x / IU, s.y / IU), (e.x / IU, e.y / IU)]
        if any(73.2 <= p[0] <= 74.6 and 10.6 <= p[1] <= 12.6 for p in pts):
            L.append(f"  {LN[t.GetLayer()]} ({pts[0][0]:.3f},{pts[0][1]:.3f})->"
                     f"({pts[1][0]:.3f},{pts[1][1]:.3f}) w{t.GetWidth()/IU:.2f}")
L.append('== RBIAS vias anywhere:')
for t in b.GetTracks():
    if t.GetNetname() == 'RBIAS' and isinstance(t, pcbnew.PCB_VIA):
        p = t.GetPosition()
        L.append(f"  VIA @({p.x/IU:.3f},{p.y/IU:.3f}) d{t.GetWidth()/IU:.2f}")
L.append('== XI tracks on B (all):')
for t in b.GetTracks():
    if t.GetNetname() == 'XI' and not isinstance(t, pcbnew.PCB_VIA) and t.GetLayer() == pcbnew.B_Cu:
        s, e = t.GetStart(), t.GetEnd()
        L.append(f"  B ({s.x/IU:.3f},{s.y/IU:.3f})->({e.x/IU:.3f},{e.y/IU:.3f}) w{t.GetWidth()/IU:.2f}")
with open(OUT, 'w') as f:
    f.write('\n'.join(L) + '\n')
print('wrote', len(L), 'lines')

#!/usr/bin/env python3
"""bl facts2: +3V3A / RBIAS / XO copper + footprint census near U7 on exp257."""
import wx
_app = wx.App(False)
import pcbnew

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp257.kicad_pcb')
IU = 1e6
LN = {pcbnew.F_Cu: 'F', pcbnew.In1_Cu: 'In1', pcbnew.In2_Cu: 'In2', pcbnew.B_Cu: 'B'}

def dump(net, box):
    x0, y0, x1, y1 = box
    print(f'== {net} in x[{x0},{x1}] y[{y0},{y1}]:')
    for t in b.GetTracks():
        if t.GetNetname() != net:
            continue
        if t.Type() == pcbnew.PCB_VIA_T:
            q = t.GetPosition()
            if x0 <= q.x / IU <= x1 and y0 <= q.y / IU <= y1:
                print(f'  VIA ({q.x/IU:.3f},{q.y/IU:.3f}) d{t.GetWidth()/IU:.2f} drill{t.GetDrillValue()/IU:.2f}')
        else:
            s, e = t.GetStart(), t.GetEnd()
            mx, my = (s.x + e.x) / 2 / IU, (s.y + e.y) / 2 / IU
            if x0 <= mx <= x1 and y0 <= my <= y1:
                print(f'  {LN[t.GetLayer()]:<3} ({s.x/IU:.3f},{s.y/IU:.3f})->({e.x/IU:.3f},{e.y/IU:.3f}) w{t.GetWidth()/IU:.3f}')

dump('+3V3A', (70, 8, 80, 18))
dump('RBIAS', (70, 9, 76, 18))
print('== footprints intersecting x[69,84] y[7,21]:')
for fp in b.GetFootprints():
    bb = fp.GetBoundingBox()
    cx, cy = (bb.GetLeft() + bb.GetRight()) / 2 / IU, (bb.GetTop() + bb.GetBottom()) / 2 / IU
    if 69 <= cx <= 84 and 7 <= cy <= 21:
        p = fp.GetPosition()
        print(f'  {fp.GetReference():<6} at ({p.x/IU:.2f},{p.y/IU:.2f}) bbox x[{bb.GetLeft()/IU:.2f},{bb.GetRight()/IU:.2f}] y[{bb.GetTop()/IU:.2f},{bb.GetBottom()/IU:.2f}]')

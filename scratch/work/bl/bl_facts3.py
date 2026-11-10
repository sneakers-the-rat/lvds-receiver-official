#!/usr/bin/env python3
"""bl facts3: item dump in fix boxes on exp259."""
import sys
import wx
_app = wx.App(False)
import pcbnew

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp259.kicad_pcb')
IU = 1e6
LN = {pcbnew.F_Cu: 'F', pcbnew.In1_Cu: 'In1', pcbnew.In2_Cu: 'In2', pcbnew.B_Cu: 'B'}
box = tuple(float(v) for v in sys.argv[1:5])

def dump(net):
    print(f'== {net}:')
    for t in b.GetTracks():
        if t.GetNetname() != net:
            continue
        if t.Type() == pcbnew.PCB_VIA_T:
            q = t.GetPosition()
            if box[0] <= q.x / IU <= box[2] and box[1] <= q.y / IU <= box[3]:
                print(f'  VIA ({q.x/IU:.3f},{q.y/IU:.3f}) d{t.GetWidth()/IU:.2f}')
        else:
            s, e = t.GetStart(), t.GetEnd()
            mx, my = (s.x + e.x) / 2 / IU, (s.y + e.y) / 2 / IU
            if box[0] <= mx <= box[2] and box[1] <= my <= box[3]:
                print(f'  {LN[t.GetLayer()]:<3} ({s.x/IU:.3f},{s.y/IU:.3f})->({e.x/IU:.3f},{e.y/IU:.3f}) w{t.GetWidth()/IU:.2f}')

for n in sys.argv[5:]:
    dump(n)

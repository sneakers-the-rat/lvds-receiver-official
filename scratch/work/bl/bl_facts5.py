#!/usr/bin/env python3
"""bl facts5: SCL In2 path, +3V3A north F feed, C19/U7 courtyards."""
import wx
_app = wx.App(False)
import pcbnew

IU = 1e6
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp260.kicad_pcb')
LN = {pcbnew.F_Cu: 'F', pcbnew.In1_Cu: 'In1', pcbnew.In2_Cu: 'In2', pcbnew.B_Cu: 'B'}

def dump(label, nets, box):
    print(f'--- {label}')
    for t in b.GetTracks():
        n = t.GetNetname()
        if n not in nets:
            continue
        p = t.GetPosition()
        x, y = p.x / IU, p.y / IU
        if not (box[0] <= x <= box[2] and box[1] <= y <= box[3]):
            continue
        if t.Type() == pcbnew.PCB_VIA_T:
            print(f'  VIA {n} ({x:.3f},{y:.3f}) d{t.GetWidth()/IU:.2f}')
        else:
            s, e = t.GetStart(), t.GetEnd()
            print(f'  {LN.get(t.GetLayer(),"?")} {n} ({s.x/IU:.3f},{s.y/IU:.3f})->({e.x/IU:.3f},{e.y/IU:.3f}) w{t.GetWidth()/IU:.2f}')

dump('SCL all layers NE', {'I2C_SCL'}, (76.0, 9.0, 80.5, 13.5))
dump('+3V3A F north feed', {'+3V3A'}, (73.0, 9.8, 78.6, 12.3))
# restrict printout: only F layer lines are wanted but dump prints all in box;
# second pass for +3V3A In2 web east end
dump('+3V3A In2 east', {'+3V3A'}, (76.5, 10.0, 79.5, 12.6))
for fp in b.GetFootprints():
    if fp.GetReference() in ('C19', 'U7', 'C48'):
        bb = None
        for sh in fp.GetCourtyard(pcbnew.F_CrtYd):
            b2 = sh.GetBoundingBox()
            print(f'CY {fp.GetReference()} shape bbox x[{b2.GetX()/IU:.3f},{(b2.GetX()+b2.GetWidth())/IU:.3f}] '
                  f'y[{b2.GetY()/IU:.3f},{(b2.GetY()+b2.GetHeight())/IU:.3f}]')
        pos = fp.GetPosition()
        print(f'FP {fp.GetReference()} at ({pos.x/IU:.3f},{pos.y/IU:.3f})')

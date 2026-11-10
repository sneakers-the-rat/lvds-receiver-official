#!/usr/bin/env python3
"""bl facts4: exp260 cluster dumps — south fanout, east row, XO/GND."""
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
            print(f'  VIA {n} ({x:.3f},{y:.3f}) d{t.GetWidth()/IU:.2f} drill{t.GetDrill()/IU:.2f}')
        else:
            s, e = t.GetStart(), t.GetEnd()
            print(f'  {LN.get(t.GetLayer(),"?")} {n} ({s.x/IU:.3f},{s.y/IU:.3f})->({e.x/IU:.3f},{e.y/IU:.3f}) w{t.GetWidth()/IU:.2f}')

dump('south fanout F+In2+B', {'ULPI_CK', 'ULPI_STP', 'ULPI_DIR', 'ULPI_NXT', 'DM_PHY'},
     (73.5, 15.9, 78.6, 19.8))
dump('east row', {'ULPI_D0', 'ULPI_D1', 'ULPI_D2', 'ULPI_D3', 'ULPI_D4', 'ULPI_D5',
                  'ULPI_D6', 'ULPI_D7'}, (78.0, 8.8, 81.2, 17.6))
dump('XO vs GND via area', {'XO', 'GND'}, (75.4, 9.0, 78.3, 11.8))
for fp in b.GetFootprints():
    if fp.GetReference() in ('C19', 'U7'):
        print(f'--- courtyard {fp.GetReference()}')
        for sh in fp.Courtyard(pcbnew.F_CrtYd):
            print('   ', sh.GetShape(), sh.GetBoundingBox().Origin.Int() if False else
                  (sh.GetBoundingBox().Origin.x / IU, sh.GetBoundingBox().GetY() / IU))

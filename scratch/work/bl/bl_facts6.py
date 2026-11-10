#!/usr/bin/env python3
"""bl facts6: NE district full dump (all nets) for the joint re-fan design."""
import wx
_app = wx.App(False)
import pcbnew

IU = 1e6
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp260.kicad_pcb')
LN = {pcbnew.F_Cu: 'F', pcbnew.In1_Cu: 'In1', pcbnew.In2_Cu: 'In2', pcbnew.B_Cu: 'B'}
BOX = (76.8, 6.8, 81.0, 17.4)
skip = {'GND'}
for t in b.GetTracks():
    n = t.GetNetname()
    if n in skip:
        continue
    p = t.GetPosition()
    x, y = p.x / IU, p.y / IU
    if not (BOX[0] <= x <= BOX[2] and BOX[1] <= y <= BOX[3]):
        continue
    if t.Type() == pcbnew.PCB_VIA_T:
        print(f'VIA {n} ({x:.3f},{y:.3f}) d{t.GetWidth()/IU:.2f} drill{t.GetDrill()/IU:.2f}')
    else:
        s, e = t.GetStart(), t.GetEnd()
        print(f'{LN.get(t.GetLayer(),"?")} {n} ({s.x/IU:.3f},{s.y/IU:.3f})->({e.x/IU:.3f},{e.y/IU:.3f}) w{t.GetWidth()/IU:.2f}')
for fp in b.GetFootprints():
    pos = fp.GetPosition()
    x, y = pos.x / IU, pos.y / IU
    if BOX[0] - 1 <= x <= BOX[2] + 1 and BOX[1] - 1 <= y <= BOX[3] + 1:
        print(f'FP {fp.GetReference()} at ({x:.3f},{y:.3f}) rot{fp.GetOrientationDegrees():.0f}')
        for p in fp.Pads():
            pp = p.GetPosition()
            print(f'   pad {p.GetNumber()} [{p.GetNetname()}] ({pp.x/IU:.3f},{pp.y/IU:.3f}) '
                  f'{p.GetSize().x/IU:.2f}x{p.GetSize().y/IU:.2f}')

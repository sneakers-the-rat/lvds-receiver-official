#!/usr/bin/env python3
"""bi facts: item dumps for the USB_RST composite (re-fan + dive +
B journey + bh arrival) on exp257."""
import wx
_app = wx.App(False)
import pcbnew

B = '/home/hatch/workspace/pdlvds-route/hw/pdlvds_rx.exp257.kicad_pcb'
b = pcbnew.LoadBoard(B)
IU = 1e6
LN = {pcbnew.F_Cu: 'F', pcbnew.In1_Cu: 'In1', pcbnew.In2_Cu: 'In2', pcbnew.B_Cu: 'B'}
out = open('/home/hatch/workspace/pdlvds-route/scratch/work/bi/bi_facts_out.txt', 'w')


def dump(title, pred):
    out.write(f'== {title}\n')
    for t in b.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            p = t.GetPosition()
            x, y = p.x / IU, p.y / IU
            if pred(None, x, y, t):
                out.write(f'  VIA {t.GetNetname()} @({x:.3f},{y:.3f}) d{t.GetWidth()/IU:.2f}\n')
        else:
            s, e = t.GetStart(), t.GetEnd()
            x0, y0, x1, y1 = s.x / IU, s.y / IU, e.x / IU, e.y / IU
            if pred(LN[t.GetLayer()], (x0 + x1) / 2, (y0 + y1) / 2, t):
                out.write(f'  {LN[t.GetLayer()]} {t.GetNetname()} ({x0:.3f},{y0:.3f})->({x1:.3f},{y1:.3f}) w{t.GetWidth()/IU:.2f}\n')


def inbox(x0, y0, x1, y1, layers=None):
    def f(lay, cx, cy, t):
        if layers and lay and lay not in layers:
            return False
        return x0 <= cx <= x1 and y0 <= cy <= y1
    return f


dump('SOUTH box x[72.5,77.5] y[15.5,20.2] all', inbox(72.5, 15.5, 77.5, 20.2))
dump('JOURNEY B x[68.8,75.2] y[3.8,17.8] B+vias',
     lambda lay, cx, cy, t: (lay in (None, 'B')) and 68.8 <= cx <= 75.2 and 3.8 <= cy <= 17.8)
dump('HOP In2 x[68.9,70.4] y[7.4,9.9]', inbox(68.9, 7.4, 70.4, 9.9, ('In2',)))
dump('NXT rejoin In2 x[74.2,76.6] y[16.8,20.0]', inbox(74.2, 16.8, 76.6, 20.0, ('In2',)))
dump('ARRIVAL box x[73.4,76.4] y[4.0,7.4] all', inbox(73.4, 4.0, 76.4, 7.4))
dump('ULPI_CK all', lambda lay, cx, cy, t: t.GetNetname() == 'ULPI_CK')
dump('PADS U6 row + U7 row', lambda lay, cx, cy, t: False)
for fp in b.GetFootprints():
    if fp.GetReference() in ('U6', 'U7'):
        for p in fp.Pads():
            pos = p.GetPosition()
            out.write(f'  PAD {fp.GetReference()}.{p.GetNumber()} {p.GetNetname()} '
                      f'@({pos.x/IU:.3f},{pos.y/IU:.3f}) {p.GetSize().x/IU:.2f}x{p.GetSize().y/IU:.2f}\n')
out.close()
print('done')

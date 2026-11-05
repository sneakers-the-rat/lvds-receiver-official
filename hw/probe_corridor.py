#!/usr/bin/env python3
"""Occupancy probe for the ULPI bus corridors: list every track/via
whose centre falls in a box, grouped by box.
Usage: xvfb-run -a python3 hw/probe_corridor.py <board>
"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew

MMt = pcbnew.ToMM
board = pcbnew.LoadBoard(sys.argv[1])
BOXES = {
    'EAST strip x[88,100] y[-26,48]': (88, 100, -26, 48),
    'NORTH band x[60,100] y[44,50]': (60, 100, 44, 50),
    'WEST column x[59,66] y[-22,44]': (59, 66, -22, 44),
    'U7 south x[80,95] y[-30,-16]': (80, 95, -30, -16),
}
for name, (x0, x1, y0, y1) in BOXES.items():
    print(f'--- {name} ---')
    hits = []
    for t in board.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            x, y = MMt(t.GetPosition().x), MMt(t.GetPosition().y)
            if x0 <= x <= x1 and y0 <= y <= y1:
                hits.append(f'  VIA {t.GetNetname()} @({x:.2f},{y:.2f})')
        else:
            sx, sy = MMt(t.GetStart().x), MMt(t.GetStart().y)
            ex, ey = MMt(t.GetEnd().x), MMt(t.GetEnd().y)
            cx, cy = (sx + ex) / 2, (sy + ey) / 2
            if x0 <= cx <= x1 and y0 <= cy <= y1:
                hits.append(f'  TRK {t.GetNetname()} L{t.GetLayer()} '
                            f'({sx:.2f},{sy:.2f})->({ex:.2f},{ey:.2f}) '
                            f'w={MMt(t.GetWidth()):.2f}')
    print('\n'.join(hits[:60]) if hits else '  (empty)')
    if len(hits) > 60:
        print(f'  ... {len(hits) - 60} more')

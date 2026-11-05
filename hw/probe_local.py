#!/usr/bin/env python3
"""Local occupancy dump around named pads: every pad, track and via
whose centre falls within R mm of the pad centre.
Usage: xvfb-run -a python3 hw/probe_local.py <board> REF.PIN [REF.PIN...]
"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew

MMt = pcbnew.ToMM
board = pcbnew.LoadBoard(sys.argv[1])
R = 6.0
pads = {}
for fp in board.GetFootprints():
    for p in fp.Pads():
        pads[f'{fp.GetReference()}.{p.GetNumber()}'] = (
            MMt(p.GetPosition().x), MMt(p.GetPosition().y),
            p.GetNetname(), fp.GetReference())
for name in sys.argv[2:]:
    if name not in pads:
        print(f'== {name}: NOT FOUND')
        continue
    cx, cy, net, ref = pads[name]
    print(f'== {name} ({net}) at ({cx:.2f},{cy:.2f}) ==')
    for n2, (x, y, net2, ref2) in sorted(pads.items()):
        if ref2 != ref and abs(x - cx) <= R and abs(y - cy) <= R:
            print(f'  PAD {n2} ({net2}) @({x:.2f},{y:.2f})')
    for t in board.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            x, y = MMt(t.GetPosition().x), MMt(t.GetPosition().y)
            if abs(x - cx) <= R and abs(y - cy) <= R:
                print(f'  VIA {t.GetNetname()} @({x:.2f},{y:.2f})')
        else:
            sx, sy = MMt(t.GetStart().x), MMt(t.GetStart().y)
            ex, ey = MMt(t.GetEnd().x), MMt(t.GetEnd().y)
            mx, my = (sx + ex) / 2, (sy + ey) / 2
            if abs(mx - cx) <= R and abs(my - cy) <= R:
                print(f'  TRK {t.GetNetname()} L{t.GetLayer()} '
                      f'({sx:.2f},{sy:.2f})->({ex:.2f},{ey:.2f}) '
                      f'w={MMt(t.GetWidth()):.2f}')

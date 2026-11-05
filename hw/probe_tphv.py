#!/usr/bin/env python3
"""Probe the TP_HV vs HV_FBX block (hops.py crash site).

hops.py died placing TP_HV (39.375,2.2)->(42.3,-3.3): blocked by
HV_FBX at R50.2. Dump every pad/track/via of HV_FBX, TP_HV, HV_R31A,
HV_R31B, HV_SEC, GND in the corridor x[30,52] y[-10,6], the R50/R34/
R31/R49/TP1 pad coordinates, and the TP_HV group members board-wide.
Usage: xvfb-run -a python3 hw/probe_tphv.py <board>
"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew

MMt = pcbnew.ToMM
board = pcbnew.LoadBoard(sys.argv[1])

def pos(o):
    return (round(MMt(o.GetPosition().x), 3), round(MMt(o.GetPosition().y), 3))

print('--- pads of interest (all board) ---')
for ref in ('R50', 'R49', 'R31', 'R34', 'R30', 'TP1', 'D1', 'C4'):
    fp = board.FindFootprintByReference(ref)
    if not fp:
        print(f'{ref}: NOT FOUND')
        continue
    print(f'{ref} at {pos(fp)} rot={fp.GetOrientationDegrees()}')
    for p in fp.Pads():
        print(f'  {ref}.{p.GetNumber()} net={p.GetNetname()} '
              f'pos={pos(p)} size=({MMt(p.GetSize().x):.2f}x'
              f'{MMt(p.GetSize().y):.2f})')

NETS = {'HV_FBX', 'TP_HV', 'HV_R31A', 'HV_R31B', 'HV_SEC', 'GND',
        'APD_K', 'HV_R30M', 'HV_R29M'}
print('--- corridor items x[30,52] y[-10,6] ---')
for t in board.GetTracks():
    net = t.GetNetname()
    if net not in NETS:
        continue
    if t.Type() == pcbnew.PCB_VIA_T:
        x, y = pos(t)
        if 30 <= x <= 52 and -10 <= y <= 6:
            print(f'  VIA {net} @({x},{y}) d={MMt(t.GetWidth()):.2f}')
    else:
        sx, sy = MMt(t.GetStart().x), MMt(t.GetStart().y)
        ex, ey = MMt(t.GetEnd().x), MMt(t.GetEnd().y)
        cx, cy = (sx + ex) / 2, (sy + ey) / 2
        if 30 <= cx <= 52 and -10 <= cy <= 6:
            print(f'  TRK {net} L{t.GetLayer()} '
                  f'({sx:.2f},{sy:.2f})->({ex:.2f},{ey:.2f}) '
                  f'w={MMt(t.GetWidth()):.2f}')

print('--- TP_HV items board-wide ---')
for t in board.GetTracks():
    if t.GetNetname() != 'TP_HV':
        continue
    if t.Type() == pcbnew.PCB_VIA_T:
        print(f'  VIA @ {pos(t)}')
    else:
        print(f'  TRK L{t.GetLayer()} '
              f'({MMt(t.GetStart().x):.2f},{MMt(t.GetStart().y):.2f})->'
              f'({MMt(t.GetEnd().x):.2f},{MMt(t.GetEnd().y):.2f})')
print('--- HV_FBX items board-wide ---')
for t in board.GetTracks():
    if t.GetNetname() != 'HV_FBX':
        continue
    if t.Type() == pcbnew.PCB_VIA_T:
        print(f'  VIA @ {pos(t)}')
    else:
        print(f'  TRK L{t.GetLayer()} '
              f'({MMt(t.GetStart().x):.2f},{MMt(t.GetStart().y):.2f})->'
              f'({MMt(t.GetEnd().x):.2f},{MMt(t.GetEnd().y):.2f})')

#!/usr/bin/env python3
"""Geography probe for the ULPI/USB_RST residue + NO_EXIT pads.
Usage: xvfb-run -a python3 hw/probe_ulpi.py <board>
"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew

MMt = pcbnew.ToMM
board = pcbnew.LoadBoard(sys.argv[1])

def pos(o):
    return (round(MMt(o.GetPosition().x), 2), round(MMt(o.GetPosition().y), 2))

for ref in ('U6', 'U7', 'U9', 'U10', 'U11', 'U14', 'U4', 'T1'):
    fp = board.FindFootprintByReference(ref)
    if fp:
        print(f'{ref} at {pos(fp)} rot={fp.GetOrientationDegrees()} '
              f'pads={len(fp.Pads())}')

WANT = {
    'U6': {'26', '29', '35', '40', '42', '46', '47', '69', '70', '73',
           '74', '76', '97', '136', '137', '139'},
    'U7': {'4', '6', '7', '9', '11', '13', '15', '18', '19', '20', '21',
           '22', '23', '26', '28', '29'},
    'U9': {'1', '3', '5', '6'},
    'U10': {'2', '3', '7', '8', '9'},
    'U11': {'10', '11', '12', '13'},
    'U14': {'6', '10'},
    'U4': {'1', '12', '14', '18', '20', '21', '27'},
    'T1': {'1', '2', '10'},
}
for ref, pins in WANT.items():
    fp = board.FindFootprintByReference(ref)
    if not fp:
        continue
    for p in fp.Pads():
        if p.GetNumber() in pins:
            print(f'  {ref}.{p.GetNumber()} {p.GetNetname()} '
                  f'@{pos(p)} {MMt(p.GetSize().x):.2f}x'
                  f'{MMt(p.GetSize().y):.2f}')

print('--- ULPI/USB_RST stub ends (track endpoints not on pads) ---')
for t in board.GetTracks():
    if not t.GetNetname().startswith(('ULPI', 'USB_RST')):
        continue
    if t.Type() == pcbnew.PCB_VIA_T:
        print(f"  VIA {t.GetNetname()} @{pos(t)}")
    else:
        print(f"  TRK {t.GetNetname()} L{t.GetLayer()} "
              f"({MMt(t.GetStart().x):.2f},{MMt(t.GetStart().y):.2f})->"
              f"({MMt(t.GetEnd().x):.2f},{MMt(t.GetEnd().y):.2f})")

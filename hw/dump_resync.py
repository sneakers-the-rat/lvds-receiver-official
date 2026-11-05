#!/usr/bin/env python3
"""Position dump for the re-sync surgery: key footprints, U6 pads
42/97, TP1's neighbourhood copper, and the HV_SHDN item chain
(U6-side -> HV-side) for the J5 interlock split.
Usage: xvfb-run -a python3 hw/dump_resync.py BOARD
"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
from hand_stub import build_items

MM = pcbnew.ToMM
board = pcbnew.LoadBoard(sys.argv[1])

for ref in ('R29', 'R30', 'R31', 'R25', 'R26', 'D1', 'C4', 'T1',
            'U10', 'TP1', 'X1', 'U9', 'D4', 'L1', 'L2'):
    fp = board.FindFootprintByReference(ref)
    if not fp:
        print(ref, 'ABSENT')
        continue
    p = fp.GetPosition()
    pads = {pd.GetNumber(): (round(MM(pd.GetPosition().x), 2),
                             round(MM(pd.GetPosition().y), 2),
                             pd.GetNetname()) for pd in fp.Pads()}
    print(f'{ref} @({MM(p.x):.2f},{MM(p.y):.2f}) rot={fp.GetOrientationDegrees()} '
          f'fp={fp.GetFPID().GetLibItemName()} pads={pads}')

u6 = board.FindFootprintByReference('U6')
for want in ('42', '97'):
    for pd in u6.Pads():
        if pd.GetNumber() == want:
            print(f'U6.{want} @({MM(pd.GetPosition().x):.2f},'
                  f'{MM(pd.GetPosition().y):.2f}) net={pd.GetNetname()}')

print('\nTP1 neighbourhood items (x 42..50, y 10..24):')
for kind, net, layers, shape, desc in build_items(board):
    if kind == 'pad':
        continue
    # bounding-box centre via the desc position is unreliable; use
    # shape bbox
    bb = shape.BBox()
    cx, cy = MM(bb.Centre().x), MM(bb.Centre().y)
    if 42 <= cx <= 50 and 10 <= cy <= 24:
        print(f'  {net} {desc} centre=({cx:.2f},{cy:.2f}) layers={sorted(layers)}')

print('\nHV_SHDN items (tracks/vias), sorted by x:')
rows = []
for kind, net, layers, shape, desc in build_items(board):
    if net != 'HV_SHDN' or kind == 'pad':
        continue
    bb = shape.BBox()
    rows.append((MM(bb.Centre().x), MM(bb.Centre().y), desc,
                 sorted(layers)))
for r in sorted(rows):
    print(f'  ({r[0]:.2f},{r[1]:.2f}) {r[2]} layers={r[3]}')

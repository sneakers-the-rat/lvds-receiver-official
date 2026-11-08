#!/usr/bin/env python3
"""Audit candidate via points (all layers, exact model) + dump PHY_1V8 In2 items."""
import sys, wx
_app = wx.App(False)
sys.path.insert(0, 'scratch/work/ai')
import pcbnew
import t_ai_lib as L

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp236prep3.kicad_pcb')
items = L.load_items(b)
print('PHY_1V8 items on In2:')
for it in items[1]:
    if it[1] == 'PHY_1V8':
        print('  ', L.fmt_it(it))
CANDS = [(76.8, 1.7), (73.3, 0.4), (68.1, 1.4), (69.3, -0.6), (72.5, 2.0),
         (71.9, 1.8), (70.875, -1.85), (77.7, 1.9), (80.45, -3.3), (78.25, -8.0)]
for (x, y) in CANDS:
    ms = []
    for li in range(3):
        m, w = L.pt_margin(li, x, y, 'ZZZ', 0.25, items[li])
        ms.append(f'L{li} {m:+.3f} vs {L.fmt_it(w)}')
    print(f'via ({x},{y}): ' + ' | '.join(ms))

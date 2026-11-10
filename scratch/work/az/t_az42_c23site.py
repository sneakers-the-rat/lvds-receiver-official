"""t_az42: survey the proposed C23 site (79.5,11.5) rot0 0402:
pads (79.02,11.5) 1V8A / (79.98,11.5) GND. Dump every item whose
centre is within box x[77.5,81.5] y[9.0,14.0], all layers; check
pad-rect clearance of both proposed pads against all foreign items
(exact item_margin with pad subjects built by hand).
"""
import sys
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

BOARD = 'hw/pdlvds_rx.exp251.kicad_pcb'
pool = load_board_pool(BOARD)
for l in range(3):
    print(f'--- layer {l} items near site ---')
    for it in pool[l]:
        cx, cy = C(it)
        if 77.5 < cx < 81.5 and 9.0 < cy < 14.0:
            print('   ', it)
# proposed pads as pad items: 0402 pad size 0.56x0.5 -> hh (0.28,0.25)
for (net, x, y) in [('PHY_1V8A', 79.02, 11.5), ('GND', 79.98, 11.5)]:
    pad = ('pad', net, (x, y, 0.28, 0.25, 0.0), 0.25 if net != 'GND'
           else 0.2)
    for l in (0, 2):
        worst = []
        for o in pool[l]:
            if o[1] == net:
                continue
            m = item_margin(l, pad, [o])
            if m < 0.3:
                worst.append((round(m, 3), o))
        worst.sort(key=lambda t: t[0])
        print(f'pad {net} ({x},{y}) layer {l}: {len(worst)} < 0.3,',
              'worst:', worst[:4])
print('=== done ===')

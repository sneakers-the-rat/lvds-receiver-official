#!/usr/bin/env python3
"""Arrival-first pricing for USB_RST on exp257: scan candidate surfacing
vias in the box south/west/east of U6.40; for each, price (a) the via vs
ALL items on all layers, (b) the F hop from the via to the nearest point
of the U6.40 pad rect. Report vias where both margins >= -0.02.
Exact geometry via gridroute.load_items; no raster."""
import math
import sys
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/hw')
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/scratch/work/parent-shots')
import gridroute as G
from price_rst import margin_via, margin_trk, items

PAD = (74.60, 3.922, 74.90, 5.402)  # U6.40 pad rect (x0,y0,x1,y1)


def clamp_pad(p):
    return (max(PAD[0], min(PAD[2], p[0])), max(PAD[1], min(PAD[3], p[1])))


rows = []
y = 5.50
while y <= 7.30:
    x = 73.85
    while x <= 75.65:
        c = (round(x, 2), round(y, 2))
        mv = margin_via(c, items)
        tgt = clamp_pad(c)
        mh = margin_trk(c, tgt, 'F', items)
        v_worst = mv[0][0] if mv else 9
        h_worst = mh[0][0] if mh else 9
        rows.append((min(v_worst, h_worst), v_worst, h_worst, c,
                     mv[0][1] if mv else '', mh[0][1] if mh else ''))
        x += 0.15
    y += 0.15
rows.sort(reverse=True)
print('top candidate surfacing vias (score = min(via margin, hop margin)):')
for s, v, h, c, dv, dh in rows[:14]:
    print(f'  {c}  via {v:+.3f} ({dv}) | hop {h:+.3f} ({dh})')

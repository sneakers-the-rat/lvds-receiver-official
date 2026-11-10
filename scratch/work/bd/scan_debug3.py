"""scan_debug3: pinpoint the sealed leg of DIR's journey in the
raster: F start->DV, B DV->goal, plus an ASCII map of the mouth."""
import sys

sys.path.insert(0, 'hw')
sys.path.insert(0, 'scratch/work/bd')
import gridroute as GR
from scan_rst import (ALL4, BOARD, GND_NOW, build_base, classify,
                      free_cell, near_district)

items = GR.load_items(BOARD, keep=near_district)
fixed, kept, relay = classify(items)
r = build_base(fixed, 0.10)
r.add_item(GR.Item('GND', 'via', a=GND_NOW, hw=0.25))
for other in ALL4:
    if other != 'ULPI_DIR':
        for it in kept[other]:
            r.add_item(it, routed_hw=0.10)

p1 = GR.astar(r, (75.75, 16.875, 'F'), (74.82, 18.10, 'F'))
print('F start -> DV:', 'PATH' if p1 else 'SEALED')
p2 = GR.astar(r, (74.82, 18.10, 'B'), (71.375, 19.125, 'B'))
print('B DV -> goal:', 'PATH' if p2 else 'SEALED')
p3 = GR.astar(r, (75.75, 16.875, 'F'), (74.82, 18.10, 'B'))
print('F start -> DV(B):', 'PATH' if p3 else 'SEALED')

print('F grid x[75.2,76.45] y[16.80,17.75] (#=blocked):')
i0, j0 = r.cell(75.2, 16.80)
i1, j1 = r.cell(76.45, 17.75)
for j in range(j0, j1 + 1):
    row = ''.join('#' if r.track['F'][j, i] else '.'
                  for i in range(i0, i1 + 1))
    print(f'  y={r.centre(i0, j)[1]:.2f} {row}')
print('cols: x from', r.centre(i0, j0)[0], 'step 0.05')

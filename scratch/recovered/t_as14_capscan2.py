"""t_as14: CAP U6-end via scan with the three fence items ripped in the model:
+3V3A F diagonal (70.125,1.875)->(70.338,1.25); I2C_SDA In2 diagonal
(69.375,2.125)->(71.125,1.875); I2C_SCL B staircase segs in the box.
Find CAP_CLK/CAP_DATA vias + straight F approach from each pad's west edge."""
import sys, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
from t_ai_lib import load_items, pt_margin, seg_margin, in_box_pool, apply_rip

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp240.kicad_pcb')
items = load_items(board)
RIPS = [
    ('seg', '+3V3A', 70.125, 1.875),
    ('seg', 'I2C_SDA', 69.375, 2.125),
    ('seg', 'I2C_SCL', 69.875, 1.625),
    ('seg', 'I2C_SCL', 70.125, 1.875),
    ('seg', 'I2C_SCL', 70.375, 2.125),
    ('seg', 'I2C_SCL', 70.625, 2.375),
]
statics, nrip = apply_rip({l: list(items[l]) for l in range(3)}, RIPS)
print('model rips applied:', nrip)

CASES = [
    ('U6.34 CAP_CLK', 'CAP_CLK', (70.60, 1.75)),
    ('U6.35 CAP_DATA', 'CAP_DATA', (70.60, 2.25)),
]
BOX = (68.7, 71.25, 0.7, 3.4)
pool = in_box_pool(statics, (BOX[0] - 1.0, BOX[1] + 1.0, BOX[2] - 1.0,
                             BOX[3] + 1.0))
for name, net, (px, py) in CASES:
    found = []
    x = BOX[0]
    while x <= BOX[1]:
        y = BOX[2]
        while y <= BOX[3]:
            worst = 9
            for l in range(3):
                m, _w = pt_margin(l, x, y, net, 0.25, pool[l])
                worst = min(worst, m)
            if worst >= 0.0:
                mapp, _w = seg_margin(0, (px, py), (x, y), net, 0.1, pool[0],
                                      step=0.04)
                if mapp >= 0.0:
                    found.append((round(min(worst, mapp), 3), round(x, 3),
                                  round(y, 3), round(worst, 3),
                                  round(mapp, 3)))
            y += 0.05
        x += 0.05
    found.sort(reverse=True)
    print(f'{name}: {len(found)} candidates; top 12:')
    for f in found[:12]:
        print(f'   score {f[0]:+.3f} via ({f[1]},{f[2]}) via {f[3]:+.3f} '
              f'approach {f[4]:+.3f}')

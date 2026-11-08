"""t_as18: CAP U6-end via scan with EXACT rip set (no cascade):
SDA In2 6 segs, SCL B 4 segs, +3V3A F 3 segs - exactly what a board prep
would rip. Also probes the U5.5 CAP_CLK dive box with the same statics."""
import sys, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
from t_ai_lib import load_items, pt_margin, seg_margin, in_box_pool

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp240.kicad_pcb')
items = load_items(board)
EXACT = [  # (net, layer, x1, y1, x2, y2)
    ('I2C_SDA', 1, 69.375, 2.125, 71.125, 1.875),
    ('I2C_SDA', 1, 71.125, 1.875, 70.875, 1.625),
    ('I2C_SDA', 1, 70.875, 1.625, 70.625, 1.375),
    ('I2C_SDA', 1, 70.625, 1.375, 70.375, 1.125),
    ('I2C_SDA', 1, 70.375, 1.125, 70.125, 0.875),
    ('I2C_SDA', 1, 70.125, 0.875, 69.900, 0.820),
    ('I2C_SCL', 2, 69.875, 1.625, 70.125, 1.875),
    ('I2C_SCL', 2, 70.125, 1.875, 70.375, 2.125),
    ('I2C_SCL', 2, 70.375, 2.125, 70.625, 2.375),
    ('I2C_SCL', 2, 70.625, 2.375, 70.875, 2.625),
    ('+3V3A', 0, 70.125, 2.625, 70.125, 1.875),
    ('+3V3A', 0, 70.125, 1.875, 70.338, 1.250),
    ('+3V3A', 0, 70.338, 1.250, 71.338, 1.250),
]

def key(it):
    k, n, d = it[0], it[1], it[2]
    if k != 'seg':
        return None
    return (n, round(d[0], 3), round(d[1], 3), round(d[2], 3), round(d[3], 3))

want = {}
for (n, li, x1, y1, x2, y2) in EXACT:
    want.setdefault(li, set()).add((n, x1, y1, x2, y2))
    want[li].add((n, x2, y2, x1, y1))
statics = {l: [] for l in range(3)}
nrip = 0
for l in range(3):
    for it in items[l]:
        if key(it) in want.get(l, set()):
            nrip += 1
            continue
        statics[l].append(it)
print('exact rips removed:', nrip, '(expect 13)')

CASES = [
    ('U6.34 CAP_CLK', 'CAP_CLK', (70.60, 1.75), (68.7, 71.25, 0.7, 3.4)),
    ('U6.35 CAP_DATA', 'CAP_DATA', (70.60, 2.25), (68.7, 71.25, 0.7, 3.4)),
]
for name, net, (px, py), (x0, x1, y0, y1) in CASES:
    pool = in_box_pool(statics, (x0 - 1.0, x1 + 1.0, y0 - 1.0, y1 + 1.0))
    found = []
    x = x0
    while x <= x1:
        y = y0
        while y <= y1:
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
    print(f'{name}: {len(found)} candidates; top 8:')
    for f in found[:8]:
        print(f'   score {f[0]:+.3f} via ({f[1]},{f[2]}) via {f[3]:+.3f} '
              f'approach {f[4]:+.3f}')

"""t_as19: gate the CAP U6 escapes against the 20-rip statics.
Rips: SDA In2 6, SCL B 6, +3V3A F 8 (exact segs).
Adds: CAP_CLK via (70.1,2.0) + F approach; CAP_DATA via (69.9,3.62) + F
approach (70.6,2.25)->(70.3,2.75)->(70.05,3.1)->(69.9,3.62).
All adds gated vs statics and mutually (item-vs-item)."""
import sys, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
from t_ai_lib import load_items, pt_margin, seg_margin

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp240.kicad_pcb')
items = load_items(board)
EXACT = [
    ('I2C_SDA', 1, 69.375, 2.125, 71.125, 1.875),
    ('I2C_SDA', 1, 71.125, 1.875, 70.875, 1.625),
    ('I2C_SDA', 1, 70.875, 1.625, 70.625, 1.375),
    ('I2C_SDA', 1, 70.625, 1.375, 70.375, 1.125),
    ('I2C_SDA', 1, 70.375, 1.125, 70.125, 0.875),
    ('I2C_SDA', 1, 70.125, 0.875, 69.900, 0.820),
    ('I2C_SCL', 2, 69.375, 1.375, 69.625, 1.625),
    ('I2C_SCL', 2, 69.625, 1.625, 69.875, 1.625),
    ('I2C_SCL', 2, 69.875, 1.625, 70.125, 1.875),
    ('I2C_SCL', 2, 70.125, 1.875, 70.375, 2.125),
    ('I2C_SCL', 2, 70.375, 2.125, 70.625, 2.375),
    ('I2C_SCL', 2, 70.625, 2.375, 70.875, 2.625),
    ('+3V3A', 0, 70.125, 2.625, 70.125, 1.875),
    ('+3V3A', 0, 70.125, 1.875, 70.338, 1.250),
    ('+3V3A', 0, 70.338, 1.250, 71.338, 1.250),
    ('+3V3A', 0, 69.875, 2.875, 70.125, 2.625),
    ('+3V3A', 0, 69.475, 2.750, 69.875, 2.875),
    ('+3V3A', 0, 69.875, 3.625, 69.875, 2.875),
    ('+3V3A', 0, 69.625, 3.875, 69.875, 3.625),
    ('+3V3A', 0, 69.375, 4.125, 69.625, 3.875),
]

def key(it):
    if it[0] != 'seg':
        return None
    d = it[2]
    return (it[1], round(d[0], 3), round(d[1], 3), round(d[2], 3),
            round(d[3], 3))

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
print('exact rips removed:', nrip, '(expect 20)')

ADDS = {0: [], 1: [], 2: []}
def via(net, x, y):
    for l in range(3):
        ADDS[l].append(('via', net, (x, y, 0.25)))
def seg(l, net, a, b, hw=0.1):
    ADDS[l].append(('seg', net, (a[0], a[1], b[0], b[1], hw)))

via('CAP_CLK', 70.1, 2.0)
seg(0, 'CAP_CLK', (70.6, 1.75), (70.1, 2.0))
via('CAP_DATA', 69.9, 3.62)
seg(0, 'CAP_DATA', (70.6, 2.25), (70.3, 2.75))
seg(0, 'CAP_DATA', (70.3, 2.75), (70.05, 3.1))
seg(0, 'CAP_DATA', (70.05, 3.1), (69.9, 3.62))

fails = 0
for l in range(3):
    for idx, it in enumerate(ADDS[l]):
        others = [o for j, o in enumerate(ADDS[l]) if j != idx]
        pool = statics[l] + others
        if it[0] == 'via':
            m, w = pt_margin(l, it[2][0], it[2][1], it[1], 0.25, pool)
        else:
            d = it[2]
            m, w = seg_margin(l, (d[0], d[1]), (d[2], d[3]), it[1], d[4],
                              pool, step=0.02)
        tag = 'FAIL' if m < 0 else 'ok  '
        if m < 0:
            fails += 1
        print(f'{tag} L{l} {it[1]} {it[2]}: {m:+.3f} vs {w}')
print('FAILS:', fails)

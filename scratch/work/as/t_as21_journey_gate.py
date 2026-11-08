"""t_as21: gate the CAP journey plans against exp241esc statics.
CLK: In2 west ride + REFCLK hook + rise (73.5,25.9) + F arrival.
DATA: B middle ride + rise (74.3,22.7) + F arrival.
All plan items gated vs board statics and mutually."""
import sys, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
from t_ai_lib import load_items, pt_margin, seg_margin

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
items = load_items(board)

ADDS = {0: [], 1: [], 2: []}
def via(net, x, y):
    for l in range(3):
        ADDS[l].append(('via', net, (x, y, 0.25)))
def seg(l, net, a, b, hw=0.1):
    ADDS[l].append(('seg', net, (a[0], a[1], b[0], b[1], hw)))

# CAP_CLK In2 journey from built via (70.02,1.83)
CLK_IN2 = [(70.02, 1.83), (69.5, 2.9), (69.15, 4.7), (69.3, 6.3),
           (69.75, 8.2), (69.75, 19.5), (71.5, 21.5), (70.9, 22.8),
           (70.95, 24.6), (73.5, 25.9)]
for a, b in zip(CLK_IN2, CLK_IN2[1:]):
    seg(1, 'CAP_CLK', a, b)
via('CAP_CLK', 73.5, 25.9)
seg(0, 'CAP_CLK', (73.5, 25.9), (75.55, 25.5))

# CAP_DATA B journey from built via (69.9,3.18)
DATA_B = [(69.9, 3.18), (70.2, 4.4), (70.2, 16.5), (74.3, 22.7)]
for a, b in zip(DATA_B, DATA_B[1:]):
    seg(2, 'CAP_DATA', a, b)
via('CAP_DATA', 74.3, 22.7)
seg(0, 'CAP_DATA', (74.3, 22.7), (75.55, 22.845))

fails = 0
worst_all = (9, None)
for l in range(3):
    for idx, it in enumerate(ADDS[l]):
        others = [o for j, o in enumerate(ADDS[l]) if j != idx]
        pool = items[l] + others
        if it[0] == 'via':
            m, w = pt_margin(l, it[2][0], it[2][1], it[1], 0.25, pool)
        else:
            d = it[2]
            m, w = seg_margin(l, (d[0], d[1]), (d[2], d[3]), it[1], d[4],
                              pool, step=0.02)
        if m < worst_all[0]:
            worst_all = (m, (l, it, w))
        if m < 0:
            fails += 1
            print(f'FAIL L{l} {it[1]} {it[2]}: {m:+.3f} vs {w}')
print('FAILS:', fails, '| worst overall:', worst_all)

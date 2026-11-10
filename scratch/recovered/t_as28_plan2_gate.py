"""t_as28: gate CAP journey plan v2 against exp241esc statics + mutual."""
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
def seg(l, net, pts, hw=0.1):
    for a, b in zip(pts, pts[1:]):
        ADDS[l].append(('seg', net, (a[0], a[1], b[0], b[1], hw)))

# CAP_CLK
seg(1, 'CAP_CLK', [(70.02, 1.83), (69.3, 2.5), (68.3, 3.55), (68.3, 12.9),
                   (69.5, 12.75)])
via('CAP_CLK', 69.5, 12.75)
seg(2, 'CAP_CLK', [(69.5, 12.75), (69.5, 19.0), (70.2, 21.8), (71.0, 23.9),
                   (72.5, 25.5), (73.9, 26.1)])
via('CAP_CLK', 73.9, 26.1)
seg(0, 'CAP_CLK', [(73.9, 26.1), (75.55, 25.5)])
# CAP_DATA
seg(1, 'CAP_DATA', [(69.9, 3.18), (69.0, 3.45), (68.05, 4.25), (68.4, 5.6),
                    (68.4, 9.0), (68.0, 11.0), (67.8, 12.7)])
via('CAP_DATA', 67.8, 12.7)
seg(2, 'CAP_DATA', [(67.8, 12.7), (67.95, 14.8), (67.85, 16.2)])
via('CAP_DATA', 67.85, 16.2)
seg(1, 'CAP_DATA', [(67.85, 16.2), (68.3, 18.5), (69.5, 20.5), (70.8, 21.6),
                    (71.3, 21.9)])
via('CAP_DATA', 71.3, 21.9)
seg(2, 'CAP_DATA', [(71.3, 21.9), (73.0, 22.6), (74.45, 22.8)])
via('CAP_DATA', 74.45, 22.8)
seg(0, 'CAP_DATA', [(74.45, 22.8), (75.55, 22.845)])

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

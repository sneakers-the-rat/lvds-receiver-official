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
seg(2, 'CAP_CLK', [(70.02, 1.83), (70.35, 2.6)])
via('CAP_CLK', 70.35, 2.6)
seg(1, 'CAP_CLK', [(70.35, 2.6), (69.0, 1.05), (68.45, 1.3), (67.95, 2.3),
                   (67.7, 3.8), (67.75, 5.4), (68.2, 7.0), (68.6, 8.6),
                   (68.45, 10.6), (68.8, 11.3), (69.6, 12.2), (70.4, 12.4),
                   (72.6, 11.9)])
via('CAP_CLK', 72.6, 11.9)
seg(2, 'CAP_CLK', [(72.6, 11.9), (71.5, 14.5), (70.3, 16.0), (68.9, 17.6),
                   (69.1, 20.0), (69.7, 22.7), (70.2, 24.5), (71.5, 26.3),
                   (72.8, 27.3), (74.85, 26.45)])
via('CAP_CLK', 74.85, 26.45)
seg(0, 'CAP_CLK', [(74.85, 26.45), (75.55, 25.5)])
# CAP_DATA
seg(2, 'CAP_DATA', [(69.9, 3.18), (69.3, 3.9), (68.95, 5.2), (68.9, 7.5),
                    (68.85, 10.5), (67.94, 12.0), (67.94, 16.9), (69.0, 17.0),
                    (72.3, 17.0), (72.0, 19.15), (73.4, 19.85), (74.45, 22.8)])
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

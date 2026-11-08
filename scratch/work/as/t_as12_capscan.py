"""t_as12: dive-via scans for CAP_CLK/CAP_DATA endpoints on exp240.
For each pad: scan a box for via points (d0.5) with all-layer pt_margin>=0
AND a straight F seg from the pad edge point to the via with margin>=0."""
import sys, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
from t_ai_lib import load_items, pt_margin, seg_margin, in_box_pool

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp240.kicad_pcb')
items = load_items(board)

CASES = [
    # name, net, pad edge point (on F), scan box (x0,x1,y0,y1)
    ('U5.5 CAP_CLK', 'CAP_CLK', (75.55, 25.385), (73.4, 76.0, 24.2, 26.5)),
    ('U5.3 CAP_DATA', 'CAP_DATA', (75.55, 22.845), (73.4, 76.0, 21.6, 24.0)),
    ('U6.34 CAP_CLK', 'CAP_CLK', (70.60, 1.75), (68.7, 71.2, 0.8, 3.3)),
    ('U6.35 CAP_DATA', 'CAP_DATA', (70.60, 2.25), (68.7, 71.2, 0.8, 3.3)),
]
for name, net, (px, py), (x0, x1, y0, y1) in CASES:
    pool = in_box_pool(items, (x0 - 1.0, x1 + 1.0, y0 - 1.0, y1 + 1.0))
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
    print(f'{name}: {len(found)} via+approach candidates; top 10:')
    for f in found[:10]:
        print(f'   score {f[0]:+.3f} via ({f[1]},{f[2]}) via-margin {f[3]:+.3f} '
              f'approach {f[4]:+.3f}')

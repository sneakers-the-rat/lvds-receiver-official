"""t_ak5: margin map for a hypothetical ULPI_D0 d0.5 via over the
U6 north-row fanout box: per-layer worst blocker at the best points.
Usage: t_ak5_d0scan.py board"""
import math, sys
sys.path.insert(0, 'hw')
sys.path.insert(0, 'scratch/work/ai')
import wx
_app = wx.App(False)
import pcbnew
from t_ai_lib import load_items, pt_margin, in_box_pool, fmt_it

board = pcbnew.LoadBoard(sys.argv[1])
items = load_items(board)
X0, X1, Y0, Y1 = 72.4, 74.6, 5.2, 6.6
pools = {li: in_box_pool(items, (X0, X1, Y0, Y1), pad=1.2)[li]
         for li in range(3)}
rows = []
gx = X0
while gx <= X1:
    gy = Y0
    while gy <= Y1:
        ms = {}
        worst = {}
        for li in range(3):
            m, w = pt_margin(li, gx, gy, 'ULPI_D0', 0.25, pools[li])
            ms[li] = m
            worst[li] = w
        rows.append((min(ms.values()), gx, gy, ms, worst))
        gy += 0.0625
    gx += 0.0625
rows.sort(reverse=True)
for tot, gx, gy, ms, worst in rows[:14]:
    bl = {0: 'F', 1: 'In2', 2: 'B'}
    print(f'({gx:.3f},{gy:.3f}) min={tot:+.3f} ' +
          ' '.join(f'{bl[li]}={ms[li]:+.3f}' for li in range(3)))
    liw = min(ms, key=ms.get)
    print(f'    worst on {"F In2 B".split()[liw]}: {fmt_it(worst[liw])}')

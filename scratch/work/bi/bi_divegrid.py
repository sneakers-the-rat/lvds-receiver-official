#!/usr/bin/env python3
"""Decisive dive test: with ULPI_DIR + ULPI_NXT south escapes REMOVED
ENTIRELY (most generous form of lever 1), does any RST dive via exist
south of U7.9? Grid d0.50 and d0.40 over x[73.6,75.3] y[16.95,19.3].
Also with DM_PHY F loop additionally removed (to name its fence)."""
import sys
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/hw')
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/scratch/work/bi')
import gridroute as G
from bi_price import m_via, BASE


def near(p, q, tol=0.006):
    return abs(p[0] - q[0]) < tol and abs(p[1] - q[1]) < tol


def drop_net_items(pool, net, layers=('F', 'In2', 'B'), ymax=20.6, ymin=16.8):
    out = []
    for it in pool:
        if it.net == net:
            if it.kind == 'via' and ymin <= it.a[1] <= ymax:
                continue
            if it.kind == 'trk' and it.layer in layers and \
               ymin <= min(it.a[1], it.b[1]) and max(it.a[1], it.b[1]) <= ymax:
                continue
        out.append(it)
    return out


pool1 = drop_net_items(drop_net_items(BASE, 'ULPI_NXT'), 'ULPI_DIR')
pool2 = drop_net_items(pool1, 'DM_PHY', ymax=19.6, ymin=15.4)

for name, pool in [('lever1-max (DIR+NXT escapes deleted)', pool1),
                   ('lever1 + DM_PHY loop deleted', pool2)]:
    for dia in (0.5, 0.40):
        best = []
        y = 16.95
        while y <= 19.30:
            x = 73.60
            while x <= 75.30:
                c = (round(x, 2), round(y, 2))
                m = m_via(c, dia / 2, 'USB_RST', pool)
                best.append((m[0][0], c, m[0][1]))
                x += 0.05
            y += 0.05
        best.sort(reverse=True)
        print(f'{name}, via d{dia}: best {best[0][0]:+.3f} @{best[0][1]} :: {best[0][2]}')
        print(f'   2nd {best[1][0]:+.3f} @{best[1][1]} :: {best[1][2]}')

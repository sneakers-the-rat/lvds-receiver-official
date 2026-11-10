#!/usr/bin/env python3
"""Fast decisive dive test (box-filtered pool). With ULPI_DIR + ULPI_NXT
south escapes REMOVED ENTIRELY (lever-1 max), does any RST dive via
exist south of U7.9? Grid d0.50/d0.40 over x[73.6,75.3] y[16.95,19.3].
Then the same with the DM_PHY F loop also removed."""
import sys
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/hw')
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/scratch/work/bi')
import gridroute as G
from bi_price import m_via, BASE

BOX = (72.8, 16.2, 76.0, 20.0)


def near(p, q, tol=0.006):
    return abs(p[0] - q[0]) < tol and abs(p[1] - q[1]) < tol


def in_box(it):
    x0, y0, x1, y1 = BOX
    if it.kind == 'via':
        return x0 <= it.a[0] <= x1 and y0 <= it.a[1] <= y1
    if it.kind == 'trk':
        return not (max(it.a[0], it.b[0]) < x0 or min(it.a[0], it.b[0]) > x1 or
                    max(it.a[1], it.b[1]) < y0 or min(it.a[1], it.b[1]) > y1)
    r = it.rect
    return not (r[2] < x0 or r[0] > x1 or r[3] < y0 or r[1] > y1)


def drop_net(pool, net, ymin=16.8, ymax=20.6):
    out = []
    for it in pool:
        if it.net == net:
            if it.kind == 'via' and ymin <= it.a[1] <= ymax:
                continue
            if it.kind == 'trk' and ymin <= min(it.a[1], it.b[1]) and \
               max(it.a[1], it.b[1]) <= ymax:
                continue
        out.append(it)
    return out


boxed = [it for it in BASE if in_box(it)]
print('boxed items:', len(boxed))
pool1 = drop_net(drop_net(boxed, 'ULPI_NXT'), 'ULPI_DIR')
pool2 = drop_net(pool1, 'DM_PHY', ymin=15.4, ymax=19.6)
for name, pool in [('lever1-max', pool1), ('lever1+DM_PHY deleted', pool2)]:
    for dia in (0.5, 0.40):
        best = []
        y = 16.95
        while y <= 19.31:
            x = 73.60
            while x <= 75.31:
                c = (round(x, 2), round(y, 2))
                m = m_via(c, dia / 2, 'USB_RST', pool)
                best.append((m[0][0], c, m[0][1]))
                x += 0.05
            y += 0.05
        best.sort(reverse=True)
        print(f'{name} d{dia}: best {best[0][0]:+.3f} @{best[0][1]} :: {best[0][2]}', flush=True)
        print(f'   2nd {best[1][0]:+.3f} @{best[1][1]} :: {best[1][2]}', flush=True)
print('DONE')

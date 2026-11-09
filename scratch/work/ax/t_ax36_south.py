"""t_ax36: for the top southern R20 sites, test both webs by A*.
Per site: fresh pool, rip stub + old R20.2 feed (A/B/D) + old pads,
add re-join C', add new pads; A* SCL ML pad1 -> pocket via
(69.35,1.4); A* +3V3D ML pad2 -> nearest +3V3D item point (reported).
"""
import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
import math

STUB = [
    ('seg', 'I2C_SCL', (69.675, 12.75, 69.625, 12.625, 0.1), 0.2),
    ('seg', 'I2C_SCL', (69.425, 12.75, 69.675, 12.75, 0.1), 0.2),
    ('via', 'I2C_SCL', (69.625, 12.625, 0.3), 0.2),
    ('seg', 'I2C_SCL', (69.625, 12.625, 65.0, 12.5, 0.1), 0.2),
    ('seg', 'I2C_SCL', (65.0, 12.5, 64.75, 12.0, 0.1), 0.2),
    ('seg', 'I2C_SCL', (64.75, 12.0, 65.25, 8.5, 0.1), 0.2),
    ('seg', 'I2C_SCL', (65.25, 8.5, 66.875, 6.75, 0.1), 0.2),
]
FEED = [
    ('seg', '+3V3D', (70.875, 12.625, 70.825, 12.75, 0.1), 0.25),
    ('seg', '+3V3D', (70.825, 12.75, 71.075, 12.75, 0.1), 0.25),
    ('seg', '+3V3D', (70.825, 12.75, 70.625, 12.375, 0.1), 0.25),
]


def rect_dist(px, py, hw, hh, qx, qy):
    return math.hypot(max(abs(px - qx) - hw, 0.0),
                      max(abs(py - qy) - hh, 0.0))


def item_dist(cx, cy, hw, hh, it):
    kind, d = it[0], it[2]
    if kind == 'pad':
        return math.hypot(max(abs(cx - d[0]) - (hw + d[2]), 0.0),
                          max(abs(cy - d[1]) - (hh + d[3]), 0.0))
    if kind == 'via':
        return max(rect_dist(cx, cy, hw, hh, d[0], d[1]) - d[2], 0.0)
    x1, y1, x2, y2, shw = d
    best = 9.9
    n = max(2, int(math.hypot(x2 - x1, y2 - y1) / 0.1) + 1)
    for i in range(n + 1):
        t = i / n
        best = min(best, rect_dist(cx, cy, hw, hh,
                                   x1 + t * (x2 - x1),
                                   y1 + t * (y2 - y1)))
    return max(best - shw, 0.0)


for (cx, cy) in ((68.5, -1.75), (68.0, -1.5), (67.5, -1.25)):
    pool = load_board_pool()
    for it in STUB + FEED:
        rip_items([it])
    for net, px in (('I2C_SCL', 69.425), ('+3V3D', 71.075)):
        for p in [it for it in pool[0] if it[0] == 'pad'
                  and it[1] == net and abs(it[2][0] - px) < 0.01
                  and abs(it[2][1] - 12.75) < 0.01]:
            rip_items([p])
    pool[0].append(('seg', '+3V3D',
                    (70.625, 12.375, 70.875, 12.625, 0.1), 0.25))
    p1 = (cx - 0.825, cy)
    p2 = (cx + 0.825, cy)
    pool[0].append(('pad', 'I2C_SCL', (p1[0], p1[1], 0.4, 0.475, 0.0),
                    0.2))
    pool[0].append(('pad', '+3V3D', (p2[0], p2[1], 0.4, 0.475, 0.0),
                    0.25))
    print(f'== site ({cx},{cy}): pad1 {p1} pad2 {p2}', flush=True)
    # nearest +3V3D item to pad2
    ds = []
    for l in range(3):
        for it in pool[l]:
            if it[1] == '+3V3D':
                ds.append((item_dist(p2[0], p2[1], 0.4, 0.475, it), l,
                           it))
    ds.sort(key=lambda t: t[0])
    d0, l0, it0 = ds[0]
    print(f'   +3V3D nearest: L{l0} d={d0:.2f} {L.fmt_it(it0)}',
          flush=True)
    goal2 = (it0[2][0], it0[2][1])
    astar = make_astar((64.0, 72.0, -4.5, 3.0), 0.025)
    J = astar('I2C_SCL', ((0, 1, 2), p1[0], p1[1]), (0, 69.35, 1.4),
              hw=0.10)
    print('   SCL A*:', 'FOUND' if J else 'NONE', flush=True)
    if J:
        print('     vias:', J['vias'], flush=True)
    astar = make_astar((64.0, 74.0, -4.5, 5.0), 0.025)
    J = astar('+3V3D', ((0, 1, 2), p2[0], p2[1]), (l0, goal2[0],
                                                   goal2[1]), hw=0.10)
    print('   +3V3D A*:', 'FOUND' if J else 'NONE', flush=True)
    if J:
        print('     vias:', J['vias'], flush=True)

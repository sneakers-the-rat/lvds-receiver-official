"""t_ax28: identify the d1/d2 items at the top R20 scan sites and
the local geography (nearest foreign pads, items by layer)."""
import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
import math

pool = load_board_pool()
b = pcbnew.LoadBoard(BOARD)
fr = fragments('I2C_SCL', (40, 100, -30, 50))
main_items = []
for f in fr:
    its = [it for (l, it) in f['items']]
    if any(it[0] == 'via' and abs(it[2][0] - 69.35) < 0.01
           and abs(it[2][1] - 1.4) < 0.01 for it in its):
        main_items = f['items']
v3d_items = [(l, it) for l in range(3) for it in pool[l]
             if it[1] == '+3V3D']


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
    n = max(2, int(math.hypot(x2 - x1, y2 - y1) / 0.05) + 1)
    for i in range(n + 1):
        t = i / n
        best = min(best, rect_dist(cx, cy, hw, hh,
                                   x1 + t * (x2 - x1),
                                   y1 + t * (y2 - y1)))
    return max(best - shw, 0.0)


for (cx, cy, rot) in ((80.0, 8.5, 0), (71.5, 3.75, 0), (80.0, 8.75, 0)):
    off = 0.825
    p1 = (cx - off, cy)
    p2 = (cx + off, cy)
    print(f'== site ({cx},{cy}) rot {rot}: pad1 {p1} pad2 {p2}',
          flush=True)
    d1s = sorted(((item_dist(p1[0], p1[1], 0.4, 0.475, it), l, it)
                  for (l, it) in main_items))[:3]
    for (d, l, it) in d1s:
        print(f'   SCL L{l} d={d:.3f}: {L.fmt_it(it)}', flush=True)
    d2s = sorted(((item_dist(p2[0], p2[1], 0.4, 0.475, it), l, it)
                  for (l, it) in v3d_items))[:3]
    for (d, l, it) in d2s:
        print(f'   +3V3D L{l} d={d:.3f}: {L.fmt_it(it)}', flush=True)
    # nearest foreign pads
    near = []
    for fp in b.GetFootprints():
        if fp.GetReference() == 'R20':
            continue
        for p in fp.Pads():
            px, py = p.GetPosition().x / 1e6, p.GetPosition().y / 1e6
            dd = math.hypot(px - cx, py - cy)
            if dd < 3.0:
                near.append((dd, fp.GetReference(), p.GetNetname(),
                             round(px, 2), round(py, 2)))
    near.sort()
    for n in near[:6]:
        print(f'   near pad: {n}', flush=True)

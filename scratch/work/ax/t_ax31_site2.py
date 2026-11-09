"""t_ax31: for R20 @ (72.25,4.5) rot90:
- U6 and R20 courtyard bboxes from the board
- identity/layer of the SCL item touching pad1 rect (72.25,3.675)
  and the +3V3D item touching pad2 rect (72.25,5.325)
- viafit at dive via candidate (72.1,4.04) on the SCL B diagonal
- B diagonal seg(s) near (72.1,4.04)"""
import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
import math

pool = load_board_pool()
b = pcbnew.LoadBoard(BOARD)
for ref in ('U6', 'R20', 'U7', 'U9'):
    for fp in b.GetFootprints():
        if fp.GetReference() == ref:
            bb = fp.GetCourtyard(pcbnew.F_CrtYd).BBox() if hasattr(fp, 'GetCourtyard') \
                else None
            print(f'{ref} at ({fp.GetPosition().x/1e6:.2f},'
                  f'{fp.GetPosition().y/1e6:.2f}) courtyard bbox: '
                  f'{bb.GetLeft()/1e6:.2f},{bb.GetTop()/1e6:.2f} .. '
                  f'{bb.GetRight()/1e6:.2f},{bb.GetBottom()/1e6:.2f}'
                  if bb else f'{ref}: no courtyard API', flush=True)


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


for (nm, net, cx, cy) in (('pad1', 'I2C_SCL', 72.25, 3.675),
                          ('pad2', '+3V3D', 72.25, 5.325)):
    print(f'== {nm} ({cx},{cy}) vs {net}:', flush=True)
    ds = []
    for l in range(3):
        for it in pool[l]:
            if it[1] == net:
                ds.append((item_dist(cx, cy, 0.475, 0.4, it), l, it))
    ds.sort(key=lambda t: t[0])
    for (d, l, it) in ds[:3]:
        print(f'   L{l} d={d:.3f}: {L.fmt_it(it)}', flush=True)

print('via cand (72.1,4.04) for I2C_SCL:', flush=True)
for l in range(3):
    others = [o for o in pool[l] if o[1] != 'I2C_SCL']
    m, bnd = L.pt_margin(l, 72.1, 4.04, 'I2C_SCL', 0.25, others)
    print(f'   L{l}: {m:+.3f} binder {L.fmt_it(bnd)}', flush=True)
print('SCL B items near (72.1,4.04):', flush=True)
for it in pool[2]:
    if it[1] == 'I2C_SCL':
        d = it[2]
        if 68 < d[0] < 79 and 0 < d[1] < 10:
            print('  ', L.fmt_it(it), flush=True)

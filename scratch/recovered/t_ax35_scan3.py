"""t_ax35: R20 relocation scan v3 (sound checks).
Legality per candidate (0603, rot 0/90):
- pad rect vs foreign footprint pads >= 0.30 (rect-exact)
- pad rect vs foreign F items >= 0.20 (rect-exact via item_dist)
- R20 courtyard bbox (3.06x1.56 / 1.56x3.06) must not intersect any
  other footprint's courtyard bbox
Score: d1 pad1->SCL main copper, d2 pad2->+3V3D copper (any layer).
"""
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
fpads = []
courts = []
for fp in b.GetFootprints():
    if fp.GetReference() == 'R20':
        continue
    for p in fp.Pads():
        fpads.append((p.GetPosition().x / 1e6, p.GetPosition().y / 1e6,
                      p.GetSize().x / 2e6, p.GetSize().y / 2e6))
    bb = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
    courts.append((bb.GetLeft() / 1e6, bb.GetTop() / 1e6,
                   bb.GetRight() / 1e6, bb.GetBottom() / 1e6,
                   fp.GetReference()))
f_items = [it for it in pool[0] if it[1] not in ('I2C_SCL', '+3V3D')]


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


results = []
PHW, PHH = 0.4, 0.475
for rot in (0, 90):
    off = 0.825
    chw, chh = (1.53, 0.78) if rot == 0 else (0.78, 1.53)
    cy = -4.0
    while cy <= 16.0:
        cx = 63.0
        while cx <= 85.0:
            if rot == 0:
                p1 = (cx - off, cy)
                p2 = (cx + off, cy)
                hw1, hh1 = PHW, PHH
            else:
                p1 = (cx, cy - off)
                p2 = (cx, cy + off)
                hw1, hh1 = PHH, PHW
            ok = True
            # courtyard bbox exclusion
            for (l, t, r, bo, ref) in courts:
                if cx - chw < r and cx + chw > l and \
                   cy - chh < bo and cy + chh > t:
                    ok = False
                    break
            if ok:
                for (px, py) in (p1, p2):
                    for (fx, fy, fhw, fhh) in fpads:
                        if abs(px - fx) < hw1 + fhw + 0.3 and \
                           abs(py - fy) < hh1 + fhh + 0.3 and \
                           math.hypot(
                               max(abs(px - fx) - (hw1 + fhw), 0.0),
                               max(abs(py - fy) - (hh1 + fhh),
                                   0.0)) < 0.30:
                            ok = False
                            break
                    if not ok:
                        break
            if ok:
                for (px, py) in (p1, p2):
                    for it in f_items:
                        d = it[2]
                        if abs(d[0] - px) < hw1 + 2.4 and \
                           abs(d[1] - py) < hh1 + 2.4 and \
                           item_dist(px, py, hw1, hh1, it) < 0.20:
                            ok = False
                            break
                    if not ok:
                        break
            if ok:
                d1 = min(item_dist(p1[0], p1[1], hw1, hh1, it)
                         for (l, it) in main_items)
                d2 = min(item_dist(p2[0], p2[1], hw1, hh1, it)
                         for (l, it) in v3d_items)
                if d1 <= 1.6 and d2 <= 1.6:
                    results.append((d1 + d2, d1, d2, cx, cy, rot))
            cx += 0.25
        cy += 0.25
results.sort()
for r in results[:20]:
    print(f'sum {r[0]:.2f} d1 {r[1]:.2f} d2 {r[2]:.2f} centre '
          f'({r[3]:.2f},{r[4]:.2f}) rot {r[5]}', flush=True)
print(f'{len(results)} legal sites', flush=True)

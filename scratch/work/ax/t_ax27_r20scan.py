"""t_ax27: R20 relocation scan (0603, rot 0/90).
Legality: pad rects clear foreign footprint pads by >=0.30 and
foreign F items by >=0.20 (perimeter sampling). Score: geometric
distance pad1->SCL main-fragment copper (any layer), pad2->+3V3D
copper (any layer). Main fragment = the model fragment containing
the pocket via (69.35,1.4)."""
import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
import math

pool = load_board_pool()
b = pcbnew.LoadBoard(BOARD)

fr = fragments('I2C_SCL', (40, 100, -30, 50))
main_items = []
stub_items = []
for f in fr:
    its = [it for (l, it) in f['items']]
    pts = [(round(it[2][0], 2), round(it[2][1], 2)) for it in its]
    if any(abs(it[2][0] - 69.35) < 0.01 and abs(it[2][1] - 1.4) < 0.01
           for it in its if it[0] == 'via'):
        main_items = f['items']
    if any(abs(it[2][0] - 69.625) < 0.01 and abs(it[2][1] - 12.625) < 0.01
           for it in its if it[0] == 'via'):
        stub_items = f['items']
print(f'fragments: {len(fr)}; main {len(main_items)} items, '
      f'stub {len(stub_items)} items', flush=True)

v3d_items = [(l, it) for l in range(3) for it in pool[l]
             if it[1] == '+3V3D']

# foreign footprint pads (exclude R20)
fpads = []
for fp in b.GetFootprints():
    if fp.GetReference() == 'R20':
        continue
    for p in fp.Pads():
        fpads.append((p.GetPosition().x / 1e6, p.GetPosition().y / 1e6,
                      p.GetSize().x / 2e6, p.GetSize().y / 2e6,
                      fp.GetReference()))


def rect_dist(px, py, hw, hh, qx, qy):
    dx = max(abs(px - qx) - hw, 0.0)
    dy = max(abs(py - qy) - hh, 0.0)
    return math.hypot(dx, dy)


def item_dist(cx, cy, hw, hh, it):
    """distance from rect (centre c, half hw/hh) to item copper."""
    kind, d = it[0], it[2]
    if kind == 'pad':
        return max(rect_dist(cx, cy, hw + d[2], hh + d[3], d[0], d[1]),
                   0.0) if False else \
            math.hypot(max(abs(cx - d[0]) - (hw + d[2]), 0.0),
                       max(abs(cy - d[1]) - (hh + d[3]), 0.0))
    if kind == 'via':
        return max(rect_dist(cx, cy, hw, hh, d[0], d[1]) - d[2], 0.0)
    x1, y1, x2, y2, shw = d
    best = 9.9
    n = max(2, int(math.hypot(x2 - x1, y2 - y1) / 0.1) + 1)
    for i in range(n + 1):
        t = i / n
        px, py = x1 + t * (x2 - x1), y1 + t * (y2 - y1)
        best = min(best, rect_dist(cx, cy, hw, hh, px, py))
    return max(best - shw, 0.0)


results = []
PHW, PHH = 0.4, 0.475  # R20 pad half-size
for rot in (0, 90):
    off = 0.825
    cy = -6.0
    while cy <= 20.0:
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
            for (px, py) in (p1, p2):
                for (fx, fy, fhw, fhh, ref) in fpads:
                    if math.hypot(max(abs(px - fx) - (hw1 + fhw), 0.0),
                                  max(abs(py - fy) - (hh1 + fhh),
                                      0.0)) < 0.30:
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
for r in results[:15]:
    print(f'sum {r[0]:.2f} d1 {r[1]:.2f} d2 {r[2]:.2f} centre '
          f'({r[3]:.2f},{r[4]:.2f}) rot {r[5]}', flush=True)
print(f'{len(results)} legal sites', flush=True)

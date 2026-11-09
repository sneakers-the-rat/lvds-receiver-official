"""t_ax110: C16 scan v2 - wider area + GND reachability test per site.
Legality as t_ax103; then for each legal site (best 12 by web score),
A* GND pad2 -> nearest GND F point (via/pad centre within 6mm)."""
import sys, math
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa

pool = load_board_pool('hw/pdlvds_rx.exp249.kicad_pcb')
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp249.kicad_pcb')
fpads = []
courts = []
for fp in b.GetFootprints():
    bb = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
    rec = (bb.GetLeft() / 1e6, bb.GetTop() / 1e6, bb.GetRight() / 1e6,
           bb.GetBottom() / 1e6, fp.GetReference())
    if fp.GetReference() == 'C16':
        c16court = rec
        continue
    courts.append(rec)
    for p in fp.Pads():
        fpads.append((p.GetPosition().x / 1e6, p.GetPosition().y / 1e6,
                      p.GetSize().x / 2e6, p.GetSize().y / 2e6,
                      p.GetNetname()))
cw = (c16court[2] - c16court[0]) / 2
ch = (c16court[3] - c16court[1]) / 2
f_items = pool[0]
v3d_F = [it for it in pool[0] if it[1] == '+3V3D']
gnd_F = [it for it in pool[0] if it[1] == 'GND']


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


PHW, PHH = 0.45, 0.475
results = []
for rot in (0, 90, 180, 270):
    if rot == 0:
        o1, o2 = (-0.775, 0.0), (0.775, 0.0)
        chw, chh = cw, ch
    elif rot == 180:
        o1, o2 = (0.775, 0.0), (-0.775, 0.0)
        chw, chh = cw, ch
    elif rot == 90:
        o1, o2 = (0.0, -0.775), (0.0, 0.775)
        chw, chh = ch, cw
    else:
        o1, o2 = (0.0, 0.775), (0.0, -0.775)
        chw, chh = ch, cw
    cy = 2.0
    while cy <= 22.0:
        cx = 58.0
        while cx <= 84.0:
            if any(cx - chw < c[2] and cx + chw > c[0]
                   and cy - chh < c[3] and cy + chh > c[1]
                   for c in courts):
                cx += 0.25
                continue
            p1 = (cx + o1[0], cy + o1[1])
            p2 = (cx + o2[0], cy + o2[1])
            ok = True
            for (px, py, phw, phh, net) in fpads:
                need1 = 0.0 if net == '+3V3D' else 0.25
                need2 = 0.0 if net == 'GND' else 0.25
                if rect_dist(px, py, phw, phh, *p1) < need1 - 1e-9 \
                        or rect_dist(px, py, phw, phh, *p2) < need2 - 1e-9:
                    ok = False
                    break
            if ok:
                for it in f_items:
                    if it[1] != '+3V3D' and \
                            item_dist(*p1, PHW, PHH, it) < 0.25:
                        ok = False
                        break
                    if it[1] != 'GND' and \
                            item_dist(*p2, PHW, PHH, it) < 0.25:
                        ok = False
                        break
            if ok:
                d1 = min(item_dist(*p1, PHW, PHH, it) for it in v3d_F)
                d2 = min(item_dist(*p2, PHW, PHH, it) for it in gnd_F)
                if d1 <= 3.0:
                    results.append((d1 + d2, d1, d2, cx, cy, rot))
            cx += 0.25
        cy += 0.25
results.sort()
print(f'{len(results)} legal sites with d1<=3; testing GND reachability '
      f'on best 12:', flush=True)
gnd_pts = [(it[2][0], it[2][1]) for it in gnd_F if it[0] in ('via', 'pad')]
for r in results[:12]:
    _, d1, d2, cx, cy, rot = r
    o2 = {0: (0.775, 0.0), 180: (-0.775, 0.0), 90: (0.0, 0.775),
          270: (0.0, -0.775)}[rot]
    p2 = (cx + o2[0], cy + o2[1])
    near = sorted(gnd_pts,
                  key=lambda q: (q[0] - p2[0]) ** 2 + (q[1] - p2[1]) ** 2)[:3]
    verdict = 'NO-GOAL'
    for q in near:
        if abs(q[0] - p2[0]) < 0.01 and abs(q[1] - p2[1]) < 0.01:
            verdict = 'ON-GND'
            break
        box = (min(p2[0], q[0]) - 2.5, max(p2[0], q[0]) + 2.5,
               min(p2[1], q[1]) - 2.5, max(p2[1], q[1]) + 2.5)
        astar = make_astar(box, 0.05)
        J = astar('GND', ((0,), p2[0], p2[1]), (0, q[0], q[1]), hw=0.10)
        if J:
            verdict = f'REACHES {q}'
            break
    print(f'  ({cx:.2f},{cy:.2f}) rot {rot} d1 {d1:.2f} d2 {d2:.2f}: '
          f'{verdict}', flush=True)

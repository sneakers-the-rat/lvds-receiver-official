"""t_ae4: computational scan for a legal C20 relocation site.

Motivation: three hand-picked sites died in a row (SDA via at
(80.625,18.375); X1 courtyard reaching x83.105 vs the SDA
pinch; the (76.9,7.9) north site sitting on +3V3A/SCL vias,
its XI leg crossing the ULPI_D fanout) -- all from designing
against partial dumps. This scan tests candidate centres on
a 0.25 grid x 4 rotations against the exact item model
(repair.build_items + router.dist_to_item -- the model the
DRC-rule grid router uses):

  1. both pad rects (0.90x0.95, pitch 1.55) clear of all
     foreign F-layer items (tracks, vias, pads) by >=0.2 edge
     distance. Two-stage: 9-point coarse sample (threshold
     0.53 = 0.2 + sampling slack 0.33), then 0.0625-grid fine
     sample (threshold 0.25 = 0.2 + slack 0.045);
  2. survivors ranked by |C20.1-U7.28| + |C20.1-X1.1|;
  3. top survivors get the exact courtyard test: C20's real
     courtyard polygon rotated/translated to the candidate vs
     every other footprint's courtyard (check_pcb's own
     extraction incl. bbox fallback), BooleanIntersection
     area <= 0.001 mm^2.

Domain restricted to the eastern half (x>=58, y in [-12,42]):
C20 is X1's load cap; both XI partners (U7.28, X1.1) live at
x 76-86, so a western site is not a serious candidate.

Usage: xvfb-run -a python3 scratch/work/t_ae4_c20scan.py BOARD
"""
import math, sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import repair
from router import dist_to_item
import check_pcb

src = sys.argv[1]
board = pcbnew.LoadBoard(src)
items, _pc = repair.build_items(board)
F = 0

U728 = (76.25, 11.562)
X11 = (85.75, 18.25)
PAD_HW, PAD_HH, PITCH = 0.45, 0.475, 0.775

def min_dist_pts(pts, net):
    worst = 9.9
    for (x, y) in pts:
        for it in items[F].near(F, x, y):
            if it[1] == net:
                continue
            d = dist_to_item(it, x, y)
            if d < worst:
                worst = d
    return worst

def pad_clear(cx, cy, hw, hh, net):
    # coarse: corners + edge midpoints + centre
    pts = [(cx + a * hw, cy + b * hh)
           for a in (-1, 0, 1) for b in (-1, 0, 1)]
    if min_dist_pts(pts, net) < 0.53:
        return 0.0
    # fine: 0.0625 grid over the rect
    nx = int(2 * hw / 0.0625)
    ny = int(2 * hh / 0.0625)
    pts = [(cx - hw + (i + 0.5) * 2 * hw / nx,
            cy - hh + (j + 0.5) * 2 * hh / ny)
           for i in range(nx) for j in range(ny)]
    d = min_dist_pts(pts, net)
    return d if d >= 0.25 else 0.0

cands = []
rots = [(1, 0), (-1, 0), (0, 1), (0, -1)]  # pad1 offset dir
cx = 58.0
while cx <= 95.0:
    cy = -12.0
    while cy <= 42.0:
        for (rx, ry) in rots:
            p1 = (cx + rx * PITCH, cy + ry * PITCH)
            p2 = (cx - rx * PITCH, cy - ry * PITCH)
            hw, hh = (PAD_HW, PAD_HH) if rx else (PAD_HH, PAD_HW)
            d1 = pad_clear(p1[0], p1[1], hw, hh, 'XI')
            if d1 <= 0:
                continue
            d2 = pad_clear(p2[0], p2[1], hw, hh, 'GND')
            if d2 <= 0:
                continue
            score = (math.hypot(p1[0] - U728[0], p1[1] - U728[1])
                     + math.hypot(p1[0] - X11[0], p1[1] - X11[1]))
            cands.append((score, cx, cy, rx, ry, d1, d2))
        cy += 0.25
    cx += 0.25
print(f'pad-clear candidates: {len(cands)}')
cands.sort()

fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
c20 = fps['C20']
c20_poly = c20.GetCourtyard(pcbnew.F_CrtYd)
chain = c20_poly.Outline(0)
c20_pts = []
for i in range(chain.PointCount()):
    p = chain.GetPoint(i)
    c20_pts.append((pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)))
c20_c = pcbnew.ToMM(c20.GetPosition())
print('C20 courtyard local pts:',
      [(round(x - c20_c[0], 3), round(y - c20_c[1], 3))
       for x, y in c20_pts])

others = []
for ref, fp in fps.items():
    if ref == 'C20':
        continue
    layer = pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd
    poly = None
    try:
        poly = fp.GetCourtyard(layer)
    except Exception:
        poly = None
    if poly is None or poly.OutlineCount() == 0:
        poly = check_pcb._fallback_courtyard(fp, fp.IsFlipped())
    others.append((ref, fp.IsFlipped(), poly, poly.BBox()))

MATS = {(1, 0): (-1, 0, 0, -1), (-1, 0): (1, 0, 0, 1),
        (0, 1): (0, 1, -1, 0), (0, -1): (0, -1, 1, 0)}

def courtyard_blockers(cx, cy, rx, ry):
    """Returns list of (ref, overlap mm^2) for all overlaps."""
    a, b, c, d = MATS[(rx, ry)]
    poly = pcbnew.SHAPE_POLY_SET()
    ch = pcbnew.SHAPE_LINE_CHAIN()
    for (lx, ly) in c20_pts:
        gx = cx + a * (lx - c20_c[0]) + b * (ly - c20_c[1])
        gy = cy + c * (lx - c20_c[0]) + d * (ly - c20_c[1])
        ch.Append(pcbnew.VECTOR2I(pcbnew.FromMM(gx),
                                  pcbnew.FromMM(gy)))
    ch.SetClosed(True)
    poly.AddOutline(ch)
    bb = poly.BBox()
    out = []
    for ref, flipped, opoly, obb in others:
        if flipped:
            continue
        if not bb.Intersects(obb):
            continue
        inter = pcbnew.SHAPE_POLY_SET(poly)
        inter.BooleanIntersection(opoly,
                                  pcbnew.SHAPE_POLY_SET.PM_FAST)
        area = 0.0
        for k in range(inter.OutlineCount()):
            area += inter.Outline(k).Area()
        if area / 1e12 > 0.001:
            out.append((ref, area / 1e12))
    return out

results = []
for (score, cx, cy, rx, ry, d1, d2) in cands:
    bl = courtyard_blockers(cx, cy, rx, ry)
    tot = sum(a for _r, a in bl)
    results.append((tot, score, cx, cy, rx, ry, d1, d2, bl))
results.sort()
print('--- lowest total courtyard overlap (mm^2) ---')
for (tot, score, cx, cy, rx, ry, d1, d2, bl) in results[:20]:
    bls = ','.join(f'{r}:{a:.3f}' for r, a in bl[:4])
    print(f'ovl {tot:.3f} centre ({cx:.2f},{cy:.2f}) pad1dir '
          f'({rx},{ry}) score {score:.1f} padclear {d1:.2f}/'
          f'{d2:.2f} blockers {bls}')

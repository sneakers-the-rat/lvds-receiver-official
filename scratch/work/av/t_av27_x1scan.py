"""t_av27: X1 site scan. Pool from the au97 head (esc board items).
X1 pads: 4.5x2.0 at pitch 8.5 (rot90: pads at cy+-4.25; rot0:
cx+-4.25 with 2.0x4.5 pads). A site is legal if both pad rects
clear every foreign F item by >=0.23 (0.2 DRC + margin) and the
inflated body rect clears foreign F PADS by >=0.2. Ranked by
distance from the XO pad to frag-1's tail end (68.875,20.375)."""
import wx
_app = wx.App(False)
import sys, math
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'av27'}
src = open('scratch/work/au/t_au97_phase2y.py').read()
exec(src.split("# 1. RBIAS tail re-lay")[0], g)
pool = g['pool']
import t_ai_lib as L

F = pool[0]
XO_TAIL = (68.875, 20.375)


def rect_dist(px, py, r):
    x0, x1, y0, y1 = r
    dx = max(x0 - px, 0.0, px - x1)
    dy = max(y0 - py, 0.0, py - y1)
    return math.hypot(dx, dy)


def seg_dist(px, py, s):
    x1, y1, x2, y2 = s
    vx, vy = x2 - x1, y2 - y1
    L2 = vx * vx + vy * vy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0,
                                ((px - x1) * vx + (py - y1) * vy) / L2))
    return math.hypot(px - (x1 + t * vx), py - (y1 + t * vy))


def item_dist_to_rect(it, r):
    """min distance from item geometry to rect r=(x0,x1,y0,y1)."""
    kind, net, geom, clr = it
    x0, x1, y0, y1 = r
    if kind == 'pad':
        cx, cy, hw, hh, rot = geom
        # rect-rect distance (pads here are axis-aligned enough)
        dx = max(x0 - (cx + hw), (cx - hw) - x1, 0.0)
        dy = max(y0 - (cy + hh), (cy - hh) - y1, 0.0)
        if dx == 0.0 and dy == 0.0:
            # overlap check
            if (cx + hw) < x0 or (cx - hw) > x1 or \
               (cy + hh) < y0 or (cy - hh) > y1:
                return max(dx, dy)
            return -1.0
        return math.hypot(dx, dy)
    if kind == 'via':
        cx, cy, rr = geom
        return rect_dist(cx, cy, r) - rr
    if kind == 'seg':
        sx1, sy1, sx2, sy2, hw = geom
        # sample endpoints + check rect corners to seg
        d = min(rect_dist(sx1, sy1, r), rect_dist(sx2, sy2, r))
        for cxr in (x0, x1):
            for cyr in (y0, y1):
                d = min(d, seg_dist(cxr, cyr, (sx1, sy1, sx2, sy2)))
        # midpoint
        d = min(d, rect_dist((sx1 + sx2) / 2, (sy1 + sy2) / 2, r))
        return d - hw
    return 9.9


def site_margin(cx, cy, rot):
    if rot == 90:
        pads = [(cx, cy + 4.25, 2.25, 1.0, 'XI'),
                (cx, cy - 4.25, 2.25, 1.0, 'XO')]
        body = (cx - 2.95, cx + 2.95, cy - 5.95, cy + 5.95)
    else:
        pads = [(cx - 4.25, cy, 1.0, 2.25, 'XI'),
                (cx + 4.25, cy, 1.0, 2.25, 'XO')]
        body = (cx - 5.95, cx + 5.95, cy - 2.95, cy + 2.95)
    worst = 9.9
    for (px, py, hw, hh, net) in pads:
        r = (px - hw, px + hw, py - hh, py + hh)
        for it in F:
            if it[1] == net:
                continue
            d = item_dist_to_rect(it, r)
            if d < worst:
                worst = d
    # body vs foreign pads
    bw = 9.9
    for it in F:
        if it[0] != 'pad':
            continue
        d = item_dist_to_rect(it, body)
        if d < bw:
            bw = d
    return worst, bw, pads


results = []
for rot in (90, 0):
    cy = 0.0
    y = -4.0
    while y <= 44.0:
        x = 44.0
        while x <= 72.0:
            m, bw, pads = site_margin(x, y, rot)
            if m >= 0.23 and bw >= 0.20:
                xo = [p for p in pads if p[4] == 'XO'][0]
                d = math.hypot(xo[0] - XO_TAIL[0], xo[1] - XO_TAIL[1])
                results.append((d, m, bw, x, y, rot))
            x += 0.5
        y += 0.5
results.sort()
print(f'legal X1 sites: {len(results)}')
for (d, m, bw, x, y, rot) in results[:25]:
    print(f'  centre=({x:.1f},{y:.1f}) rot={rot} padmargin={m:+.3f} '
          f'bodymargin={bw:+.3f} hop={d:.1f}mm')
print('done')

"""t_aw6: binding fences for near X2 sites (corrected pad margins)."""
import wx
_app = wx.App(False)
import sys, math
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'aw6'}
src = open('scratch/work/au/t_au97_phase2y.py').read()
exec(src.split("# 1. RBIAS tail re-lay")[0], g)
pool = g['pool']
import t_ai_lib as L
from router import dist_to_item

PADS0 = [('+3V3D', -1.05, 0.825), ('GND', 1.05, 0.825),
         ('REFCLK', 1.05, -0.825), ('+3V3D', -1.05, -0.825)]
OWN = {(70.45, 24.575), (72.55, 24.575), (72.55, 22.925), (70.45, 22.925)}
obs = [it for it in pool[0]
       if not (it[0] == 'pad' and (round(it[2][0], 3), round(it[2][1], 3))
               in OWN)]

def item_aabb(it):
    kind, d = it[0], it[2]
    if kind == 'pad':
        r = math.hypot(d[2], d[3])
        return d[0] - r, d[0] + r, d[1] - r, d[1] + r
    if kind == 'seg':
        return (min(d[0], d[2]) - d[4], max(d[0], d[2]) + d[4],
                min(d[1], d[3]) - d[4], max(d[1], d[3]) + d[4])
    return d[0] - d[2], d[0] + d[2], d[1] - d[2], d[1] + d[2]
OBS_AB = [(o, item_aabb(o)) for o in obs]

def pad_margin(net, cx, cy, hw, hh):
    x0, x1, y0, y1 = cx - hw, cx + hw, cy - hh, cy + hh
    pts = [(cx, cy)]
    n = 10
    for i in range(n + 1):
        t = i / n
        pts.append((x0 + (x1 - x0) * t, y0))
        pts.append((x0 + (x1 - x0) * t, y1))
        pts.append((x0, y0 + (y1 - y0) * t))
        pts.append((x1, y0 + (y1 - y0) * t))
    worst = (9e9, None)
    for o, ab in OBS_AB:
        if o[1] == net:
            continue
        clr = L.pair_clr(net, o[1])
        dx = max(ab[0] - x1, x0 - ab[1], 0.0)
        dy = max(ab[2] - y1, y0 - ab[3], 0.0)
        if math.hypot(dx, dy) - clr > 0.6:
            continue
        for (px, py) in pts:
            d = dist_to_item(o, px, py) - clr
            if d < worst[0]:
                worst = (d, o)
    return worst

SITES = [(71.5, 27.5, 0), (72.0, 27.5, 0), (72.5, 27.5, 0),
         (71.5, 28.0, 0), (72.0, 28.0, 0), (73.25, 27.0, 90),
         (73.0, 27.5, 90), (70.0, 27.0, 0), (74.0, 26.5, 90),
         (71.0, 27.5, 0), (72.5, 28.5, 0), (73.5, 28.0, 90)]
for (cx, cy, rot) in SITES:
    print(f'--- site ({cx},{cy}) rot{rot} ---', flush=True)
    for (net, dx, dy) in PADS0:
        if rot == 0:
            ox, oy, hw, hh = dx, dy, 0.65, 0.55
        else:
            ox, oy, hw, hh = -dy, dx, 0.55, 0.65
        m, o = pad_margin(net, cx + ox, cy + oy, hw, hh)
        print(f'   pad {net} ({cx + ox:.2f},{cy + oy:.2f}): {m:+.3f}'
              + ('' if o is None else f' vs {L.fmt_it(o)}'), flush=True)
print('done', flush=True)

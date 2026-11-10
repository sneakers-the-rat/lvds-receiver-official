"""t_aw3 (v2): X2 relocation site scan.

v1 used item_margin with pads as subjects; item_margin returns the
9.9 sentinel for non-seg/via subjects (see t_au71_phase2b.item_margin),
so v1 was VOID wherever a via/seg bound. v2 computes pad margins by
sampling the candidate pad perimeter + centre against
router.dist_to_item minus pair_clr, plus an inside test for obstacle
key points. Screens: (a) min margin >= +0.02; (b) site vacates the
F pocket band x[69.8,73.2] y[22.3,25.2]; (c) courtyard bbox screen
vs exp240 real courtyards. Ranked by displacement from (71.5,23.75).
"""
import wx
_app = wx.App(False)
import sys, json, math
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'aw3'}
src = open('scratch/work/au/t_au97_phase2y.py').read()
exec(src.split("# 1. RBIAS tail re-lay")[0], g)
pool = g['pool']
import t_ai_lib as L
from router import dist_to_item
import pcbnew

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
    """Min margin of an axis-aligned pad rect vs foreign pool[0] items.
    AABB lower-bound prefilter: an item whose AABB is >0.6+clr from
    the rect cannot bind; legality at +0.02 stays exact."""
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
        # obstacle key points inside the rect -> collision
        kps = []
        if o[0] == 'via':
            kps = [(o[2][0], o[2][1])]
        elif o[0] == 'seg':
            kps = [(o[2][0], o[2][1]), (o[2][2], o[2][3])]
        elif o[0] == 'pad':
            kps = [(o[2][0], o[2][1])]
        for (kx, ky) in kps:
            if x0 < kx < x1 and y0 < ky < y1:
                if -1.0 < worst[0]:
                    worst = (-1.0, o)
        for (px, py) in pts:
            d = dist_to_item(o, px, py) - clr
            if d < worst[0]:
                worst = (d, o)
    return worst

def margins(cx, cy, rot):
    out = []
    for (net, dx, dy) in PADS0:
        if rot == 0:
            ox, oy, hw, hh = dx, dy, 0.65, 0.55
        else:
            ox, oy, hw, hh = -dy, dx, 0.55, 0.65
        w = pad_margin(net, cx + ox, cy + oy, hw, hh)
        out.append((net, cx + ox, cy + oy, w))
    return out

def vacates(cx, cy, rot):
    for (net, dx, dy) in PADS0:
        if rot == 0:
            ox, oy, hw, hh = dx, dy, 0.65, 0.55
        else:
            ox, oy, hw, hh = -dy, dx, 0.55, 0.65
        x0, x1 = cx + ox - hw, cx + ox + hw
        y0, y1 = cy + oy - hh, cy + oy + hh
        if x0 < 73.2 and x1 > 69.8 and y0 < 25.2 and y1 > 22.3:
            return False
    return True

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp240.kicad_pcb')
IU = 1e6
def crt_bbox(fp):
    bb = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
    return (bb.GetLeft() / IU, bb.GetTop() / IU,
            bb.GetRight() / IU, bb.GetBottom() / IU)
x2 = b.FindFootprintByReference('X2')
x2c = crt_bbox(x2)
others = []
for fp in b.GetFootprints():
    if fp.GetReference() == 'X2':
        continue
    try:
        bb = crt_bbox(fp)
    except Exception:
        continue
    if bb[2] < 64 or bb[0] > 79 or bb[3] < 14 or bb[1] > 33:
        continue
    others.append((fp.GetReference(), bb))

def crt_ok(cx, cy, rot):
    w = x2c[2] - x2c[0]
    h = x2c[3] - x2c[1]
    if rot:
        w, h = h, w
    bx0, bx1 = cx - w / 2, cx + w / 2
    by0, by1 = cy - h / 2, cy + h / 2
    for (ref, bb) in others:
        if bx0 < bb[2] and bx1 > bb[0] and by0 < bb[3] and by1 > bb[1]:
            return ref
    return None

cands = []
for rot in (0, 90):
    for cxi in range(0, 25):
        for cyi in range(0, 29):
            cx = 69.0 + 0.25 * cxi
            cy = 23.75 + 0.25 * cyi
            if abs(cx - 71.5) < 0.01 and abs(cy - 23.75) < 0.01:
                continue
            if not vacates(cx, cy, rot):
                continue
            ms = margins(cx, cy, rot)
            mn = min(m[3][0] for m in ms)
            bad = crt_ok(cx, cy, rot)
            disp = math.hypot(cx - 71.5, cy - 23.75)
            cands.append((bad is None, disp, mn, cx, cy, rot, bad, ms))
cands.sort(key=lambda t: t[2], reverse=True)
print(f'vacating candidates scored: {len(cands)}; '
      f'margin>=+0.02: {sum(1 for c in cands if c[2] >= 0.02)}; '
      f'courtyard-OK among those: '
      f'{sum(1 for c in cands if c[2] >= 0.02 and c[0])}', flush=True)
shown = 0
for (ok, disp, mn, cx, cy, rot, bad, ms) in cands:
    if shown >= 20:
        break
    bind = min(ms, key=lambda m: m[3][0])
    print(f'  site ({cx:.2f},{cy:.2f}) rot{rot} disp {disp:.2f} '
          f'min_margin {mn:+.3f} courtyard '
          f'{"OK" if ok else "OVERLAP " + str(bad)} binding: pad '
          f'{bind[0]} at ({bind[1]:.2f},{bind[2]:.2f}) vs '
          f'{L.fmt_it(bind[3][1])}', flush=True)
    shown += 1
json.dump([[c[2], c[3], c[4], c[5], c[0], c[1]] for c in cands],
          open('scratch/work/aw/x2_sites.json', 'w'))
print('done', flush=True)

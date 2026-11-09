"""t_aw1: census of the H5 district in the au97-head model.
XO fragments + key points; X2 pads; REFCLK/+3V3D/GND items near X2;
C22/C24 pads; clk9/arr_clk tail geometry."""
import wx
_app = wx.App(False)
import sys, json
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'aw1'}
src = open('scratch/work/au/t_au97_phase2y.py').read()
exec(src.split("# 1. RBIAS tail re-lay")[0], g)
pool = g['pool']
C = g['C']
fragments = g['fragments']
JOURNEYS = g['JOURNEYS']
import t_ai_lib as L

R2 = lambda v: round(v, 3)

def near(it, x, y, d=0.6):
    k, net, geo, clr = it
    if k == 'pad':
        cx, cy = geo[0], geo[1]
        return abs(cx - x) < d and abs(cy - y) < d
    if k == 'via':
        return abs(geo[0] - x) < d and abs(geo[1] - y) < d
    if k == 'seg':
        x1, y1, x2, y2, hw = geo
        return (min(x1, x2) - d < x < max(x1, x2) + d
                and min(y1, y2) - d < y < max(y1, y2) + d)
    return False

print('=== XO fragments, box (63,94,7,29) ===', flush=True)
fr = fragments('XO', (63, 94, 7, 29))
print(f'XO fragments: {len(fr)} sizes '
      f'{sorted((len(f["items"]) for f in fr), reverse=True)}', flush=True)
for i, f in enumerate(fr):
    xs, ys = [], []
    for (l, it) in f['items']:
        k, net, geo, clr = it
        if k == 'pad':
            xs.append(geo[0]); ys.append(geo[1])
        elif k == 'via':
            xs.append(geo[0]); ys.append(geo[1])
        elif k == 'seg':
            xs += [geo[0], geo[2]]; ys += [geo[1], geo[3]]
    print(f'  frag{i}: n={len(f["items"])} x[{min(xs):.2f},{max(xs):.2f}] '
          f'y[{min(ys):.2f},{max(ys):.2f}]', flush=True)
    for (px, py, tag) in [(71.625, 25.625, 'F-dip start'),
                          (71.875, 19.625, 'B stub'),
                          (68.875, 20.375, 'goal')]:
        hits = [(l, it) for (l, it) in f['items'] if near(it, px, py, 0.35)]
        for (l, it) in hits:
            print(f'    near {tag} ({px},{py}): L{l} {L.fmt_it(it)}',
                  flush=True)

print('=== pads in box (68.5,74.5,21,27) — X2 area ===', flush=True)
for l in range(3):
    for it in pool[l]:
        if it[0] == 'pad':
            cx, cy = it[2][0], it[2][1]
            if 68.5 < cx < 74.5 and 21 < cy < 27:
                print(f'  L{l} {L.fmt_it(it)}', flush=True)

print('=== items by net, box (68,76.5,20.5,29.5) ===', flush=True)
for net in ('REFCLK', '+3V3D', 'XO'):
    print(f'-- {net} --', flush=True)
    for l in range(3):
        for it in pool[l]:
            if it[1] != net:
                continue
            k, n, geo, clr = it
            if k == 'pad':
                cx, cy = geo[0], geo[1]
                ok = 68 < cx < 76.5 and 20.5 < cy < 29.5
            elif k == 'via':
                ok = 68 < geo[0] < 76.5 and 20.5 < geo[1] < 29.5
            else:
                ok = (68 < geo[0] < 76.5 and 20.5 < geo[1] < 29.5) or \
                     (68 < geo[2] < 76.5 and 20.5 < geo[3] < 29.5)
            if ok:
                print(f'  L{l} {L.fmt_it(it)}', flush=True)

print('=== REFCLK all items (board-wide endpoints) ===', flush=True)
for l in range(3):
    for it in pool[l]:
        if it[1] == 'REFCLK' and it[0] in ('pad', 'via'):
            print(f'  L{l} {L.fmt_it(it)}', flush=True)

print('=== C22/C24 pads (y=18 row) ===', flush=True)
for l in range(3):
    for it in pool[l]:
        if it[0] == 'pad' and abs(it[2][1] - 18.0) < 0.01 \
                and 67 < it[2][0] < 74.5:
            print(f'  L{l} {L.fmt_it(it)}', flush=True)

print('=== clk9 + arr_clk journeys ===', flush=True)
for name in ('clk9', 'arr_clk'):
    J = JOURNEYS[name]
    print(f'-- {name}: vias={J["vias"]}', flush=True)
    for r in J['runs']:
        pts = r['pts']
        print(f'   L{r["layer"]} n={len(pts)} first={pts[0]} last={pts[-1]}',
              flush=True)
        if r['layer'] == 0:
            for p in pts:
                if 20.5 < p[1] < 23.5:
                    print(f'      F pt {p}', flush=True)
print('done', flush=True)

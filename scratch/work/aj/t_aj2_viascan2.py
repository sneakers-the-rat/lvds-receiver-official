"""t_aj2: feasible-via scan like t_ai2, plus ADDVIA env: extra foreign
vias (net:x:y:dia, semicolon list) placed on all layers as obstacles,
and VERBOSE=1 prints every feasible point with its margin.
Usage: t_aj2_viascan2.py board NET x0 x1 y0 y1 [step] [dia]
Env RIP: semicolon list of kind:net:x:y rip specs (as t_ai2)."""
import os, sys
sys.path.insert(0, 'hw')
sys.path.insert(0, 'scratch/work/ai')
import wx
_app = wx.App(False)
import pcbnew
import t_ai_lib as L

SRC, NET = sys.argv[1], sys.argv[2]
X0, X1, Y0, Y1 = map(float, sys.argv[3:7])
STEP = float(sys.argv[7]) if len(sys.argv) > 7 else 0.0625
DIA = float(sys.argv[8]) if len(sys.argv) > 8 else 0.5
board = pcbnew.LoadBoard(SRC)
items = L.load_items(board)
if os.environ.get('RIP'):
    specs = []
    for s in os.environ['RIP'].split(';'):
        k, n, x, y = s.split(':')
        specs.append((k, n, float(x), float(y)))
    items, nr = L.apply_rip(items, specs)
    print(f'ripped {nr} item entries')
    for li in range(3):
        pass
if os.environ.get('ADDVIA'):
    from router import netclass
    for s in os.environ['ADDVIA'].split(';'):
        n, x, y, d = s.split(':')
        clr = netclass(n)[1]
        for li in range(3):
            items[li].append(('via', n, (float(x), float(y), float(d) / 2),
                              clr))
    print(f'added obstacle vias: {os.environ["ADDVIA"]}')
pool = L.in_box_pool(items, (X0, X1, Y0, Y1), pad=1.2)
rad = DIA / 2
feas = []
j = 0
while Y0 + j * STEP <= Y1 + 1e-9:
    i = 0
    while X0 + i * STEP <= X1 + 1e-9:
        x, y = X0 + i * STEP, Y0 + j * STEP
        m = min(L.pt_margin(li, x, y, NET, rad, pool[li])[0]
                for li in range(3))
        if m >= 0:
            feas.append((round(m, 3), round(x, 4), round(y, 4)))
        i += 1
    j += 1
print(f'{NET} d{DIA}: {len(feas)} feasible via points in '
      f'x[{X0},{X1}] y[{Y0},{Y1}] step {STEP}')
if os.environ.get('VERBOSE'):
    for f in sorted(feas, key=lambda t: -t[0]):
        print(f'    pt margin {f[0]:+.3f} at ({f[1]},{f[2]})')
feas.sort(key=lambda t: (t[2], t[1]))
clusters = []
for m, x, y in feas:
    for c in clusters:
        if abs(x - c['cx']) <= 0.27 and abs(y - c['cy']) <= 0.27:
            c['pts'].append((m, x, y))
            c['cx'] = sum(p[1] for p in c['pts']) / len(c['pts'])
            c['cy'] = sum(p[2] for p in c['pts']) / len(c['pts'])
            break
    else:
        clusters.append({'pts': [(m, x, y)], 'cx': x, 'cy': y})
for c in clusters:
    pts = c['pts']
    best = max(pts)
    xs = [p[1] for p in pts]; ys = [p[2] for p in pts]
    print(f'  cluster n={len(pts)} x[{min(xs):.3f},{max(xs):.3f}] '
          f'y[{min(ys):.3f},{max(ys):.3f}] best {best}')

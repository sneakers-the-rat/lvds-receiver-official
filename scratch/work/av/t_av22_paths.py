"""t_av22: dump the dip and ride A* paths (base state: rip+C49+DIR)
to see where they conflict."""
import wx
_app = wx.App(False)
import sys
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'av22'}
src = open('scratch/work/au/t_au97_phase2y.py').read()
exec(src.split("# 1. RBIAS tail re-lay")[0], g)
pool = g['pool']
make_astar = g['make_astar']
C = g['C']
R2 = lambda v: round(v, 3)

rip = [it for it in pool[1] if it[0] == 'seg' and it[1] == 'RBIAS']
assert len(rip) == 19
for it in rip:
    pool[1].remove(it)


def find_pad(net, cx, cy=19.5):
    for l in range(3):
        for it in pool[l]:
            if it[0] == 'pad' and it[1] == net:
                cc = C(it)
                if abs(cc[0] - cx) < 0.01 and abs(cc[1] - cy) < 0.01:
                    return l, it
    raise AssertionError(net)


for net, cx in (('+3V3A', 69.225), ('GND', 70.775)):
    l, it = find_pad(net, cx)
    pool[l].remove(it)
    kind, ntn, (ccx, ccy, hw_, hh, rot), clr = it
    pool[l].append(('pad', ntn, (ccx + 0.5, ccy, hw_, hh, rot), clr))
for l in range(3):
    for it in list(pool[l]):
        if it[0] == 'seg' and it[1] == '+3V3A':
            x1, y1, x2, y2, hw_ = it[2]
            if (abs(x2 - 69.225) < 0.01 and abs(y2 - 19.5) < 0.01
                    and abs(hw_ - 0.150) < 0.001):
                pool[l].remove(it)
DIR_SEG = (71.375, 19.125, 68.875, 29.0)
for it in list(pool[2]):
    if it[0] == 'seg' and it[1] == 'ULPI_DIR' \
            and tuple(R2(v) for v in it[2][:4]) == DIR_SEG:
        pool[2].remove(it)

a_dip = make_astar((67.5, 75.5, 14.5, 23.5), step=0.025)
J = a_dip('XO', ((2,), 71.875, 19.625), (1, 68.875, 20.375), 0.10)
print(f'DIP vias={J["vias"]}', flush=True)
for r in J['runs']:
    pts = r['pts']
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    print(f'  L{r["layer"]} n={len(pts)} x[{min(xs):.2f},{max(xs):.2f}] '
          f'y[{min(ys):.2f},{max(ys):.2f}]', flush=True)
    print('   path:', ' '.join(f'({p[0]:.2f},{p[1]:.2f})'
                               for p in pts[::20]), flush=True)

a_rb = make_astar((67.0, 75.0, 10.5, 22.5), step=0.025)
J2 = a_rb('RBIAS', ((0, 1, 2), 73.875, 11.625), (2, 69.625, 20.625),
          0.125)
print(f'RIDE vias={J2["vias"]}', flush=True)
for r in J2['runs']:
    pts = r['pts']
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    print(f'  L{r["layer"]} n={len(pts)} x[{min(xs):.2f},{max(xs):.2f}] '
          f'y[{min(ys):.2f},{max(ys):.2f}]', flush=True)
    print('   path:', ' '.join(f'({p[0]:.2f},{p[1]:.2f})'
                               for p in pts[::20]), flush=True)
print('done', flush=True)

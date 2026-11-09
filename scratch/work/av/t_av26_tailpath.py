"""t_av26: dump the re-laid ULPI_DIR tail path (base state)."""
import wx
_app = wx.App(False)
import sys
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'av26'}
src = open('scratch/work/au/t_au97_phase2y.py').read()
exec(src.split("# 1. RBIAS tail re-lay")[0], g)
pool = g['pool']
make_astar = g['make_astar']
R2 = lambda v: round(v, 3)
DIR_SEG = (71.375, 19.125, 68.875, 29.0)
for it in list(pool[2]):
    if it[0] == 'seg' and it[1] == 'ULPI_DIR' \
            and tuple(R2(v) for v in it[2][:4]) == DIR_SEG:
        pool[2].remove(it)
a_dir = make_astar((68.3, 74.8, 18.6, 29.6), step=0.025)
J = a_dir('ULPI_DIR', ((2,), 71.375, 19.125), (2, 68.875, 29.0), 0.10)
pts = J['runs'][0]['pts']
print(f'tail n={len(pts)}')
print('path:', ' '.join(f'({p[0]:.2f},{p[1]:.2f})' for p in pts[::10]))
print('done')

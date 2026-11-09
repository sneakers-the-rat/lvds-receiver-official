import wx
_app = wx.App(False)
import sys
sys.path.insert(0, 'scratch/work/au'); sys.path.insert(0, 'scratch/work/ai'); sys.path.insert(0, 'hw')
g = {'__name__': 'av10'}
src = open('scratch/work/au/t_au97_phase2y.py').read()
exec(src.split("# 1. RBIAS tail re-lay")[0], g)
pool = g['pool']
import t_ai_lib as L
def C(it):
    d = it[2]
    if it[0] == 'seg': return ((d[0]+d[2])/2, (d[1]+d[3])/2)
    return (d[0], d[1])
print('--- In2 items x[68.3,74.8] y[18.9,26.3], all nets ---', flush=True)
for it in pool[1]:
    cx, cy = C(it)
    if 68.3 < cx < 74.8 and 18.9 < cy < 26.3:
        print('  ', L.fmt_it(it), flush=True)
print('--- F items x[70.5,75.0] y[20.5,26.3] (F leg area) ---', flush=True)
for it in pool[0]:
    cx, cy = C(it)
    if 70.5 < cx < 75.0 and 20.5 < cy < 26.3:
        print('  ', L.fmt_it(it), flush=True)
print('done', flush=True)

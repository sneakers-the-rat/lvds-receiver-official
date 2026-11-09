import wx
_app = wx.App(False)
import sys, json
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'av18'}
src = open('scratch/work/au/t_au97_phase2y.py').read()
exec(src.split("# 1. RBIAS tail re-lay")[0], g)
pool = g['pool']
item_margin = g['item_margin']
import t_ai_lib as L
# NOTE: this probe checks the field in the au93 state for the
# record; the decisive numbers come from t_av13's own scan.
for (x, y) in [(70.45, 20.25), (70.5, 20.3), (70.4, 20.2)]:
    v = ('via', 'XO', (x, y, 0.25), 0.2)
    for l in range(3):
        res = []
        for o in pool[l]:
            if o[1] == 'XO':
                continue
            m = item_margin(l, v, [o])
            if m < 0.35:
                res.append((m, o))
        res.sort(key=lambda t: t[0])
        for m, o in res[:2]:
            print(f'({x},{y}) L{l} via margin {m:+.3f} vs {L.fmt_it(o)}', flush=True)
print('done', flush=True)

"""t_aw3b: probe item_margin pad-vs-via for the suspect pair."""
import wx
_app = wx.App(False)
import sys
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'aw3b'}
src = open('scratch/work/au/t_au97_phase2y.py').read()
exec(src.split("# 1. RBIAS tail re-lay")[0], g)
pool = g['pool']
item_margin = g['item_margin']
import t_ai_lib as L

via = None
for it in pool[0]:
    if it[0] == 'via' and it[1] == 'XO' and abs(it[2][0] - 71.625) < 0.01 \
            and abs(it[2][1] - 25.625) < 0.01:
        via = it
print('via item:', via, flush=True)
pad = ('pad', '+3V3D', (72.425, 25.95, 0.55, 0.65, 0), 0.2)
print('pad vs via margin:', item_margin(0, pad, [via]), flush=True)
print('via vs pad margin:', item_margin(0, via, [pad]), flush=True)
# how many pool[0] items are within 3mm of the pad centre?
n = 0
for o in pool[0]:
    m = item_margin(0, pad, [o])
    if m < 3.0:
        n += 1
        if o[1] != '+3V3D':
            print(f'  near: {m:+.3f} {L.fmt_it(o)}', flush=True)
print(f'items with margin<3: {n}', flush=True)

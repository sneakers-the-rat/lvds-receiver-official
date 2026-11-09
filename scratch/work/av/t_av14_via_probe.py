import wx
_app = wx.App(False)
import sys
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'av14'}
src = open('scratch/work/au/t_au97_phase2y.py').read()
exec(src.split("# 1. RBIAS tail re-lay")[0], g)
pool = g['pool']
item_margin = g['item_margin']
import t_ai_lib as L
NEW_VIA = ('via', 'RBIAS', (69.45, 20.85, 0.300), 0.2)
NEW_TAIL = ('seg', 'RBIAS', (69.45, 20.85, 69.425, 21.0, 0.100), 0.2)
for l in range(3):
    res = []
    for o in pool[l]:
        if o[1] == 'RBIAS':
            continue
        m = item_margin(l, NEW_VIA, [o])
        if m < 0.3:
            res.append((m, o))
    res.sort(key=lambda t: t[0])
    for m, o in res[:5]:
        print(f'L{l} via margin {m:+.3f} vs {L.fmt_it(o)}', flush=True)
for l in range(3):
    res = []
    for o in pool[l]:
        if o[1] == 'RBIAS':
            continue
        m = item_margin(l, NEW_TAIL, [o])
        if m < 0.3:
            res.append((m, o))
    res.sort(key=lambda t: t[0])
    for m, o in res[:3]:
        print(f'L{l} tail margin {m:+.3f} vs {L.fmt_it(o)}', flush=True)
# scan a small neighbourhood for a legal r0.3 via spot
print('--- r0.3 via scan around (69.45,20.85) ---', flush=True)
best = []
x = 69.1
while x <= 69.9:
    y = 20.6
    while y <= 21.15:
        v = ('via', 'RBIAS', (x, y, 0.300), 0.2)
        w = 9.9
        for l in range(3):
            for o in pool[l]:
                if o[1] == 'RBIAS':
                    continue
                w = min(w, item_margin(l, v, [o]))
        if w >= -0.001:
            best.append((round(w, 3), round(x, 3), round(y, 3)))
        y += 0.05
    x += 0.05
best.sort(reverse=True)
for b in best[:15]:
    print('   ', b, flush=True)
print('done', flush=True)

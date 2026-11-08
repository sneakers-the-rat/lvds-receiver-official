"""t_ar2: gate a plan JSON against a board's statics (no build).
Usage: t_ar2_gate.py BOARD plan.json [plan2.json ...]
Layers: 0=F,1=In2,2=B. Via radius model 0.25 (d0.5)."""
import sys, wx, json
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
from t_ai_lib import load_items, pt_margin, seg_margin, fmt_it

board = pcbnew.LoadBoard(sys.argv[1])
items = load_items(board)
pool = {l: list(items[l]) for l in range(3)}
plans = []
for f in sys.argv[2:]:
    for e in json.load(open(f)):
        plans.append(tuple(e))
fails = 0
for i, e in enumerate(plans):
    if e[0] == 'via':
        _, net, x, y = e
        it = ('via', net, (x, y, 0.25), 0.2)
        worst = 9
        for l in range(3):
            m, w = pt_margin(l, x, y, net, 0.25, pool[l])
            if m < worst:
                worst, wl, ww = m, l, w
            pool[l].append(it)
        tag = 'OK ' if worst >= -0.001 else 'FAIL'
        if worst < -0.001:
            fails += 1
        print(f'{tag} [{i}] via {net} ({x},{y}) worst L{wl} {worst:+.3f} vs {fmt_it(ww)}')
    else:
        _, net, li, ax, ay, bx, by, wd = e
        it = ('seg', net, (ax, ay, bx, by, wd / 2), 0.2)
        m, w = seg_margin(li, (ax, ay), (bx, by), net, wd / 2, pool[li], step=0.04)
        tag = 'OK ' if m >= -0.001 else 'FAIL'
        if m < -0.001:
            fails += 1
        print(f'{tag} [{i}] seg {net} L{li} ({ax},{ay})->({bx},{by}) w{wd}: {m:+.3f} vs {fmt_it(w)}')
        pool[li].append(it)
print(f'TOTAL {len(plans)} items, {fails} FAILS')

"""t_ar3: gate a plan against board statics WITH statics mods.
Usage: t_ar3_gate2.py BOARD mods.json plan.json [plan2.json ...]
mods.json: {"rips": [item-spec...], "adds": [plan-entry...]}
  rip spec for seg: ["seg", NET, LI, AX, AY]  (start-point match, any end)
  rip spec for via: ["via", NET, X, Y]
Plan entries gated in order (mods adds first). Layers 0=F,1=In2,2=B."""
import sys, wx, json
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
from t_ai_lib import load_items, pt_margin, seg_margin, fmt_it, apply_rip

board = pcbnew.LoadBoard(sys.argv[1])
mods = json.load(open(sys.argv[2])) if sys.argv[2] != '-' else {}
items = load_items(board)
statics, nrip = apply_rip({l: list(items[l]) for l in range(3)},
                          [tuple(r) for r in mods.get('rips', [])])
print(f'statics rips applied: {nrip} (expected {len(mods.get("rips", []))})')
pool = {l: list(statics[l]) for l in range(3)}
plans = [tuple(e) for e in mods.get('adds', [])]
for f in sys.argv[3:]:
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

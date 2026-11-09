"""t_aw14: join-2 diagnostics from the cached state.
Find the stub fragment's true items; census the pad's neighbourhood;
probe legal via points (viafit) around the stub."""
import wx
_app = wx.App(False)
import sys, pickle
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'aw14'}
src = open('scratch/work/au/t_au97_phase2y.py').read()
exec(src.split("# 1. RBIAS tail re-lay")[0], g)
st = pickle.load(open('scratch/work/aw/state_aw.pkl', 'rb'))
_ns = {id(g): g}
for _fn in (g['fragments'], g['item_margin'], g['make_astar'],
            g['try_emit'], g['journey_items_dense']):
    _ns[id(_fn.__globals__)] = _fn.__globals__
for _d in _ns.values():
    _d['pool'] = st['pool']
    _d['NEW'] = st['NEW']
    _d['JOURNEYS'] = st['JOURNEYS']
    _d['NET_HW'] = st['NET_HW']
pool = st['pool']
fragments = g['fragments']
item_margin = g['item_margin']
C = g['C']
import t_ai_lib as L

print('--- +3V3D pads in box (70,78,18,26) ---', flush=True)
for l in range(3):
    for it in pool[l]:
        if it[0] == 'pad' and it[1] == '+3V3D':
            cc = C(it)
            if 70 <= cc[0] <= 78 and 18 <= cc[1] <= 26:
                print(f'  L{l} {L.fmt_it(it)} C={cc}', flush=True)

print('--- +3V3D fragments in box (70,78,18,26) ---', flush=True)
fr = fragments('+3V3D', (70.0, 78.0, 18.0, 26.0))
for i, f in enumerate(fr):
    print(f'  frag{i}: {len(f["items"])} items', flush=True)
    if len(f['items']) <= 10:
        for (ll, it) in f['items']:
            print(f'      L{ll} {L.fmt_it(it)} C={C(it)}', flush=True)

print('--- all-net census within 1.6 of (72.725,20.5) ---', flush=True)
for l in range(3):
    for it in pool[l]:
        cc = C(it)
        if abs(cc[0] - 72.725) <= 1.6 and abs(cc[1] - 20.5) <= 1.6:
            print(f'  L{l} {L.fmt_it(it)}', flush=True)

print('--- viafit probe: +3V3D via r0.25 margins, '
      'x[71.25,74.75] y[18.75,22.75] step 0.25 ---', flush=True)
via = ('via', '+3V3D', (0.0, 0.0, 0.25), 0.2)
legal = []
y = 18.75
while y <= 22.76:
    x = 71.25
    while x <= 74.76:
        worst = 9e9
        for l in range(3):
            v = ('via', '+3V3D', (round(x, 3), round(y, 3), 0.25), 0.2)
            m = item_margin(l, v, pool[l])
            worst = min(worst, m)
        if worst >= -0.001:
            legal.append((round(x, 3), round(y, 3), round(worst, 3)))
        x += 0.25
    y += 0.25
print(f'legal via points: {legal}', flush=True)
print('T_AW14 DIAG COMPLETE', flush=True)

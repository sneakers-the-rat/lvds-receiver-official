"""t_aw31: find what gates the moved SDA via (69.05,2.45) at -0.349
on F. Replay cache + t_aw18 mutations (as t_aw28), move the via,
print worst offenders per layer."""
import wx
_app = wx.App(False)
import sys, json, pickle
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'aw31'}
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
JOURNEYS = st['JOURNEYS']
NET_HW = st['NET_HW']
B = json.load(open('scratch/work/aw/build_aw1.json'))
fragments = g['fragments']
try_emit = g['try_emit']
C = g['C']
import t_ai_lib as L
from router import dist_to_item
R2 = lambda v: round(v, 3)

fr = fragments('+3V3D', (70.0, 78.0, 18.0, 26.0))
stub_fr = None
for f in fr:
    for (ll, it) in f['items']:
        if it[0] == 'pad' and abs(C(it)[0] - 72.725) < 0.01 \
                and abs(C(it)[1] - 20.5) < 0.01:
            stub_fr = f
for (ll, it) in list(stub_fr['items']):
    if it[0] == 'seg' and it in pool[ll]:
        pool[ll].remove(it)
for l in range(3):
    for it in list(pool[l]):
        if it[0] == 'pad' and (R2(it[2][0]), R2(it[2][1])) in \
                {(72.725, 20.5), (74.275, 20.5)}:
            pool[l].remove(it)
pool[0].append(('pad', '+3V3D', (72.77, 20.75, 0.28, 0.31, 0), 0.2))
pool[0].append(('pad', 'GND', (73.73, 20.75, 0.28, 0.31, 0), 0.2))
NET_HW['detour_+3V3D_stub'] = ('+3V3D', 0.125)
assert try_emit('detour_+3V3D_stub', B['journeys']['detour_+3V3D_stub'],
                '+3V3D', 0.125)
print('replay ok', flush=True)

for l in range(3):
    for i, it in enumerate(pool[l]):
        if it[0] == 'via' and it[1] == 'I2C_SDA' and \
                abs(it[2][0] - 69.05) < 0.01 and \
                abs(it[2][1] - 2.05) < 0.01:
            pool[l][i] = ('via', 'I2C_SDA', (69.05, 2.45, it[2][2]),
                          it[3])

via_pt = (69.05, 2.45)
for l in range(3):
    scored = []
    for o in pool[l]:
        if o[1] == 'I2C_SDA':
            continue
        clr = L.pair_clr('I2C_SDA', o[1])
        d = dist_to_item(o, via_pt[0], via_pt[1]) - 0.25 - clr
        scored.append((d, o))
    scored.sort(key=lambda s: s[0])
    print(f'L{l} worst vs SDA via (69.05,2.45):', flush=True)
    for (d, o) in scored[:4]:
        print(f'   {d:+.3f} {L.fmt_it(o)}', flush=True)
print('T_AW31 COMPLETE', flush=True)

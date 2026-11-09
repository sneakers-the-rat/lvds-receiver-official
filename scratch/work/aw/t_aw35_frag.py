import wx
_app = wx.App(False)
import sys, json, pickle
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'aw35'}
src = open('scratch/work/au/t_au97_phase2y.py').read()
exec(src.split("# 1. RBIAS tail re-lay")[0], g)
st = pickle.load(open('scratch/work/aw/state_aw.pkl', 'rb'))
_ns = {id(g): g}
for _fn in (g['fragments'], g['item_margin'], g['make_astar'],
            g['try_emit'], g['journey_items_dense']):
    _ns[id(_fn.__globals__)] = _fn.__globals__
for _d in _ns.values():
    _d['pool'] = st['pool']; _d['NEW'] = st['NEW']
    _d['JOURNEYS'] = st['JOURNEYS']; _d['NET_HW'] = st['NET_HW']
pool = st['pool']; JOURNEYS = st['JOURNEYS']; NET_HW = st['NET_HW']
B = json.load(open('scratch/work/aw/build_aw1.json'))
fragments = g['fragments']; try_emit = g['try_emit']; C = g['C']
import t_ai_lib as L
R2 = lambda v: round(v, 3)
fr = fragments('+3V3D', (70.0, 78.0, 18.0, 26.0))
sf = None
for f in fr:
    for (ll, it) in f['items']:
        if it[0] == 'pad' and abs(C(it)[0]-72.725) < 0.01 and abs(C(it)[1]-20.5) < 0.01:
            sf = f
for (ll, it) in list(sf['items']):
    if it[0] == 'seg' and it in pool[ll]:
        pool[ll].remove(it)
for l in range(3):
    for it in list(pool[l]):
        if it[0] == 'pad' and (R2(it[2][0]), R2(it[2][1])) in {(72.725, 20.5), (74.275, 20.5)}:
            pool[l].remove(it)
pool[0].append(('pad', '+3V3D', (72.77, 20.75, 0.28, 0.31, 0), 0.2))
pool[0].append(('pad', 'GND', (73.73, 20.75, 0.28, 0.31, 0), 0.2))
NET_HW['detour_+3V3D_stub'] = ('+3V3D', 0.125)
assert try_emit('detour_+3V3D_stub', B['journeys']['detour_+3V3D_stub'], '+3V3D', 0.125)
sfr = fragments('I2C_SCL', (60, 78, -6, 14))
for i, f in enumerate(sfr):
    print(f'=== fragment {i} ({len(f["items"])} items)', flush=True)
    for (ll, it) in sorted(f['items'], key=lambda z: (z[0], str(z[1][2]))):
        print(f'   L{ll} {L.fmt_it(it)}', flush=True)

print('--- closest pairs fragment0 vs fragment2 ---', flush=True)
def endpoints(f):
    pts = []
    for (ll, it) in f['items']:
        if it[0] == 'seg':
            pts.append((ll, it[2][0], it[2][1]))
            pts.append((ll, it[2][2], it[2][3]))
        else:
            pts.append((ll, it[2][0], it[2][1]))
    return pts
p0 = endpoints(sfr[0])
p2 = endpoints(sfr[2])
pairs = []
for (l1, x1, y1) in p0:
    for (l2, x2, y2) in p2:
        d = ((x1-x2)**2 + (y1-y2)**2) ** 0.5
        pairs.append((d, l1, (x1, y1), l2, (x2, y2)))
pairs.sort()
for pr in pairs[:10]:
    print(f'   d={pr[0]:.2f} L{pr[1]} {pr[2]} <-> L{pr[3]} {pr[4]}', flush=True)
for i, f in enumerate(sfr):
    xs = [q[1] for q in endpoints(f)]
    ys = [q[2] for q in endpoints(f)]
    print(f'fragment {i} bbox x[{min(xs):.2f},{max(xs):.2f}] y[{min(ys):.2f},{max(ys):.2f}]', flush=True)

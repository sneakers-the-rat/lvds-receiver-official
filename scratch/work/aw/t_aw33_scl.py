"""t_aw33: SCL bridge forensics. Replay cache + t_aw18 state; list
SCL fragments' items near the W chain end; check what occupies the
bridge box on each layer (data_entry In2 run, clk9 B run, F items)."""
import wx
_app = wx.App(False)
import sys, json, pickle
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'aw33'}
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

sfr = fragments('I2C_SCL', (60, 78, -6, 14))
print(f'SCL fragments: {len(sfr)}', flush=True)
for i, f in enumerate(sfr):
    print(f'--- fragment {i} ({len(f["items"])} items): items with an '
          f'endpoint in (65.5,70.5,-0.5,7.5) or a pad:', flush=True)
    for (ll, it) in f['items']:
        if it[0] == 'pad':
            print(f'   L{ll} {L.fmt_it(it)}', flush=True)
            continue
        if it[0] == 'via':
            cx, cy = it[2][0], it[2][1]
            if 65.5 < cx < 70.5 and -0.5 < cy < 7.5:
                print(f'   L{ll} {L.fmt_it(it)}', flush=True)
            continue
        x1, y1, x2, y2 = it[2][:4]
        for (px, py) in ((x1, y1), (x2, y2)):
            if 65.5 < px < 70.5 and -0.5 < py < 7.5:
                print(f'   L{ll} {L.fmt_it(it)}', flush=True)
                break

print('--- data_entry journey ---', flush=True)
J = JOURNEYS['data_entry']
print('  vias:', J['vias'], flush=True)
for r in J['runs']:
    print(f"  L{r['layer']} first {r['pts'][0]} last {r['pts'][-1]} "
          f"n={len(r['pts'])}", flush=True)
print('--- clk9 B run in box ---', flush=True)
J = JOURNEYS['clk9']
for r in J['runs']:
    pts = [p for p in r['pts'] if 65 < p[0] < 70.5 and -0.5 < p[1] < 7.5]
    if pts:
        print(f"  L{r['layer']} pts in box: {len(pts)} "
              f"first {pts[0]} last {pts[-1]}", flush=True)
print('--- pool items (foreign) in box (66,70.5,0.5,7), by layer ---',
      flush=True)
for l in range(3):
    nets = {}
    for it in pool[l]:
        if it[1] == 'I2C_SCL':
            continue
        if it[0] == 'seg':
            cx = (it[2][0] + it[2][2]) / 2
            cy = (it[2][1] + it[2][3]) / 2
        else:
            cx, cy = it[2][0], it[2][1]
        if 66 < cx < 70.5 and 0.5 < cy < 7:
            nets[it[1]] = nets.get(it[1], 0) + 1
    print(f'  L{l}: {nets}', flush=True)
print('T_AW33 COMPLETE', flush=True)

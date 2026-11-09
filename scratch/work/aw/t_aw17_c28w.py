"""t_aw17: move C28 south-west out of the sealed pocket.
Scan centres W/SW of the knot; pad legality via corrected pad_margin;
stub A* from the new pad; join criterion = same fragment as U5's
+3V3D pad in the wide box (55,97,-12,40) - not merely count-1.
From the t_aw12 cache."""
import wx
_app = wx.App(False)
import sys, json, pickle
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'aw17'}
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
NEW = st['NEW']
JOURNEYS = st['JOURNEYS']
NET_HW = st['NET_HW']
B = st['B']
RIP_ADD = st['RIP_ADD']
new_pads = st['new_pads']
fragments = g['fragments']
make_astar = g['make_astar']
journey_items_dense = g['journey_items_dense']
item_margin = g['item_margin']
try_emit = g['try_emit']
C = g['C']
import t_ai_lib as L
from router import dist_to_item

CX, CY, ROT = 75.75, 32.25, 0
R2 = lambda v: round(v, 3)

def frag_report(net, box):
    fr = fragments(net, box)
    print(f'fragments({net}) = {len(fr)} sizes '
          f'{sorted((len(f["items"]) for f in fr), reverse=True)}',
          flush=True)
    return fr

def pad_margin(net, cx, cy, hw, hh, layer=0):
    x0, x1, y0, y1 = cx - hw, cx + hw, cy - hh, cy + hh
    pts = [(cx, cy)]
    n = 10
    for i in range(n + 1):
        t = i / n
        pts.append((x0 + (x1 - x0) * t, y0))
        pts.append((x0 + (x1 - x0) * t, y1))
        pts.append((x0, y0 + (y1 - y0) * t))
        pts.append((x1, y0 + (y1 - y0) * t))
    worst = (9e9, None)
    for o in pool[layer]:
        if o[1] == net:
            continue
        clr = L.pair_clr(net, o[1])
        for (px, py) in pts:
            d = dist_to_item(o, px, py) - clr
            if d < worst[0]:
                worst = (d, o)
    return worst

print('--- cached state check ---', flush=True)
assert len(frag_report('XO', (63, 94, 7, 29))) == 1
assert len(frag_report('DM_PHY', (60, 82, -4, 32))) == 1
base_v3 = frag_report('+3V3D', (60, 95, -8, 28))
assert len(base_v3) == 5

# rip the old stub segs and remove C28's pads
fr = fragments('+3V3D', (70.0, 78.0, 18.0, 26.0))
stub_fr = None
for f in fr:
    for (ll, it) in f['items']:
        if it[0] == 'pad' and abs(C(it)[0] - 72.725) < 0.01 \
                and abs(C(it)[1] - 20.5) < 0.01:
            stub_fr = f
assert stub_fr is not None
for (ll, it) in list(stub_fr['items']):
    if it[0] == 'seg':
        if it in pool[ll]:
            pool[ll].remove(it)
        RIP_ADD.setdefault('+3V3D', []).append(
            [it[0], it[1], list(it[2]), it[3]])
for l in range(3):
    for it in list(pool[l]):
        if it[0] == 'pad' and (R2(it[2][0]), R2(it[2][1])) in \
                {(72.725, 20.5), (74.275, 20.5)}:
            pool[l].remove(it)
print('old stub segs ripped; C28 pads removed', flush=True)

a_j2 = make_astar((66.0, 78.0, 16.0, 27.0), step=0.025)
VIA_GOALS = [(0, 71.125, 24.375), (1, 71.125, 24.375),
             (2, 71.125, 24.375)]

def goals_for(sx, sy):
    gs = ([(0, 76.525, 24.115), (0, 70.45, 22.425),
           (0, 70.2, 24.575), (0, 67.475, 20.5)] + VIA_GOALS)
    gs.sort(key=lambda gg: (gg[1] - sx) ** 2 + (gg[2] - sy) ** 2)
    return gs

def joins_u5(pad_xy, Jv, hw):
    """temp-add journey items; check pad and U5 pad share a fragment
    in the wide box; remove items again."""
    its = journey_items_dense(Jv, '+3V3D', hw=hw)
    for l in range(3):
        pool[l] += its[l]
    fr = fragments('+3V3D', (55, 97, -12, 40))
    idx_pad = idx_u5 = None
    for i, f in enumerate(fr):
        for (ll, it) in f['items']:
            if it[0] == 'pad':
                cc = C(it)
                if abs(cc[0] - pad_xy[0]) < 0.01 \
                        and abs(cc[1] - pad_xy[1]) < 0.01:
                    idx_pad = i
                if abs(cc[0] - 76.525) < 0.01 \
                        and abs(cc[1] - 24.115) < 0.01:
                    idx_u5 = i
    for l in range(3):
        for it in its[l]:
            if it in pool[l]:
                pool[l].remove(it)
    return idx_pad is not None and idx_pad == idx_u5

def courtyard_clash(cx, cy):
    # proxies from known neighbour centres/courtyards
    if abs(cx - 68.75) < 1.7 and cy < 19.75:
        return 'C24'
    if abs(cx - 67.5) < 1.9 and abs(cy - 22.75) < 1.6:
        return 'C38'
    if abs(cx - 72.5) < 1.6 and abs(cy - 18.0) < 1.5:
        return 'C22'
    if abs(cx - 66.75) < 1.9 and abs(cy - 20.5) < 1.5:
        return 'L1'
    return None

cands = []
cx = 69.75
while cx <= 72.26:
    cy = 18.75
    while cy <= 21.01:
        if not (abs(cx - 73.5) < 0.01 and abs(cy - 20.5) < 0.01):
            cands.append((round(cx, 2), round(cy, 2)))
        cy += 0.25
    cx += 0.25
cands.sort(key=lambda cc: (cc[0] - 73.5) ** 2 + (cc[1] - 20.5) ** 2)
print(f'scan candidates: {len(cands)}', flush=True)

C28_MOVE = None
join2 = False
n_legal = 0
for (cx, cy) in cands:
    if courtyard_clash(cx, cy):
        continue
    p_v3 = (cx - 0.775, cy)
    p_gnd = (cx + 0.775, cy)
    m1, _o = pad_margin('+3V3D', p_v3[0], p_v3[1], 0.45, 0.475)
    m2, _o = pad_margin('GND', p_gnd[0], p_gnd[1], 0.45, 0.475)
    if m1 < -0.001 or m2 < -0.001:
        continue
    n_legal += 1
    pad_v3 = ('pad', '+3V3D', (p_v3[0], p_v3[1], 0.45, 0.475, 0), 0.2)
    pad_gnd = ('pad', 'GND', (p_gnd[0], p_gnd[1], 0.45, 0.475, 0), 0.2)
    pool[0].append(pad_v3)
    pool[0].append(pad_gnd)
    done = False
    for hw in (0.125, 0.10):
        for gg in goals_for(p_v3[0], p_v3[1]):
            Jv = a_j2('+3V3D', ((0,), p_v3[0], p_v3[1]), gg, hw)
            if Jv is None:
                continue
            if not joins_u5(p_v3, Jv, hw):
                print(f'  cand ({cx},{cy}) hw{hw} goal{gg}: route '
                      f'found but does NOT join U5 fragment',
                      flush=True)
                continue
            if try_emit('detour_+3V3D_stub', Jv, '+3V3D', hw):
                print(f'  C28 -> ({cx},{cy}) margins {m1:+.3f}/'
                      f'{m2:+.3f} stub hw={hw} goal={gg} '
                      f'vias={Jv["vias"]}', flush=True)
                done = True
                break
        if done:
            break
    if done:
        C28_MOVE = {'from': [73.5, 20.5], 'to': [cx, cy], 'rot': 0,
                    'pads': {'+3V3D': list(p_v3), 'GND': list(p_gnd)}}
        join2 = True
        break
    pool[0].remove(pad_v3)
    pool[0].remove(pad_gnd)
print(f'pad-legal candidates seen: {n_legal}', flush=True)
assert join2, 'C28 W/SW scan: no legal+routable+U5-joining centre'
v3 = frag_report('+3V3D', (60, 95, -8, 28))
assert len(v3) == len(base_v3) - 1
print('JOIN 2 CLOSED (C28 moved W/SW)', flush=True)
assert len(frag_report('DM_PHY', (60, 82, -4, 32))) == 1

print('=== full gate (au97 semantics) ===', flush=True)
fails = []
for l in range(3):
    for it in NEW[l]:
        m = item_margin(l, it, pool[l])
        if m < -0.001:
            fails.append((m, l, it))
print(f'full gate fails: {len(fails)}', flush=True)
for (m, l, it) in fails[:12]:
    print(f'   {m:+.3f} L{l} {L.fmt_it(it)}', flush=True)
assert not fails, 'full gate failed - do not build from this model'

print('=== final fragments ===', flush=True)
frag_report('CAP_CLK', (60, 80, -2, 28))
frag_report('CAP_DATA', (60, 80, -2, 28))
frag_report('XO', (63, 94, 7, 29))
frag_report('RBIAS', (63, 80, 9, 26))
frag_report('+3V3D', (60, 95, -8, 28))
frag_report('REFCLK', (60, 80, 9, 42))
frag_report('DM_PHY', (60, 82, -4, 32))

RIP2_OUT = {net: [list(x) for x in lst] for net, lst in B['rip2'].items()}
for net, lst in RIP_ADD.items():
    RIP2_OUT.setdefault(net, []).extend(lst)
out = dict(journeys=JOURNEYS, fixed=B['fixed'], rip2=RIP2_OUT,
           extra=B['extra'], arrivals=B['arrivals'],
           clk_via=(70.2, 1.8), exit_via=(69.075, 2.8), u9_shift=1.25,
           moves={'X2': {'from': [71.5, 23.75], 'to': [CX, CY],
                         'rot': ROT}},
           shrinks={'C22': {'pads': [[72.02, 18.0], [72.98, 18.0]],
                            'size': [0.56, 0.62]},
                    'C24': {'pads': [[68.27, 18.0], [69.23, 18.0]],
                            'size': [0.56, 0.62]}},
           x2_pads={net: [list(p) for p in ps]
                    for net, ps in new_pads.items()})
if C28_MOVE:
    out['moves']['C28'] = C28_MOVE
json.dump(out, open('scratch/work/aw/build_aw1.json', 'w'), indent=1)
print('saved build_aw1.json', flush=True)
print('H5 MODEL COMPLETE (t_aw17 c28w)', flush=True)

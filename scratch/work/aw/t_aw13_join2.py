"""t_aw13: join-2 campaign from the t_aw12 cached model state.
State = full H5 model with ride+dip+DM relay+REFCLK relay+X2 links all
emitted; only the +3V3D stub join (join 2) is open.
Campaigns: A terminus start, expanded goals, tight box;
B stub segs ripped, C28 pad start; C C28 relocation scan.
On success: full gate (au97 semantics) + save build_aw1.json."""
import wx
_app = wx.App(False)
import sys, json, pickle
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'aw13'}
src = open('scratch/work/au/t_au97_phase2y.py').read()
exec(src.split("# 1. RBIAS tail re-lay")[0], g)

st = pickle.load(open('scratch/work/aw/state_aw.pkl', 'rb'))
# au97 creates its OWN inner g for the src71 machinery: the helper
# functions' __globals__ is that inner dict, not the exec globals.
# Replace the state objects in EVERY namespace that holds them.
_ns = {id(g): g}
for _fn in (g['fragments'], g['item_margin'], g['make_astar'],
            g['try_emit'], g['journey_items_dense']):
    _ns[id(_fn.__globals__)] = _fn.__globals__
for _d in _ns.values():
    _d['pool'] = st['pool']
    _d['NEW'] = st['NEW']
    _d['JOURNEYS'] = st['JOURNEYS']
    _d['NET_HW'] = st['NET_HW']
print(f'state replaced in {len(_ns)} namespaces', flush=True)
pool = st['pool']
NEW = st['NEW']
JOURNEYS = st['JOURNEYS']
NET_HW = st['NET_HW']
B = st['B']
RIP_ADD = st['RIP_ADD']
new_pads = st['new_pads']
fragments = g['fragments']
make_astar = g['make_astar']
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
xo = frag_report('XO', (63, 94, 7, 29))
assert len(xo) == 1, 'cached XO state wrong'
dm = frag_report('DM_PHY', (60, 82, -4, 32))
assert len(dm) == st['base_dm_len'], 'cached DM state wrong'
v3 = frag_report('+3V3D', (60, 95, -8, 28))
assert len(v3) == st['base_v3_len'], 'cached +3V3D state wrong'
rb = frag_report('RBIAS', (63, 80, 9, 26))
assert len(rb) == 1, 'cached RBIAS state wrong'
print('cached state verified', flush=True)

print('=== JOIN 2 (t_aw13, tight box) ===', flush=True)
C28_MOVE = None
a_j2 = make_astar((69.5, 78.0, 17.5, 26.5), step=0.025)
VIA_GOALS = [(0, 71.125, 24.375), (1, 71.125, 24.375),
             (2, 71.125, 24.375)]
link_pts = []
seen_lp = set()
for nm in ('x2_v3a_0', 'x2_v3a_1'):
    for r in JOURNEYS[nm]['runs']:
        for p in r['pts'][::10]:
            key = (r['layer'], R2(p[0]), R2(p[1]))
            if key not in seen_lp and 69.5 < p[0] < 78.0 \
                    and 17.5 < p[1] < 26.5:
                seen_lp.add(key)
                link_pts.append(key)
print(f'link-point goals in box: {len(link_pts)}', flush=True)

def stub_goals(sx, sy):
    gs = ([(0, 76.525, 24.115), (0, 70.45, 22.425),
           (0, 70.2, 24.575)] + VIA_GOALS + link_pts)
    gs.sort(key=lambda gg: (gg[1] - sx) ** 2 + (gg[2] - sy) ** 2)
    return gs

def stub_try(tag, start):
    sx, sy = start[1], start[2]
    for hw in (0.125, 0.10):
        for gg in stub_goals(sx, sy):
            Jv = a_j2('+3V3D', start, gg, hw)
            if Jv is not None:
                print(f'  stub ({tag}) hw={hw} goal={gg}: '
                      f'vias={Jv["vias"]} '
                      f'runs={[(r["layer"], len(r["pts"])) for r in Jv["runs"]]}',
                      flush=True)
                if try_emit('detour_+3V3D_stub', Jv, '+3V3D', hw):
                    return True
    print(f'  stub ({tag}): NONE', flush=True)
    return False

join2 = stub_try('A-term', ((0,), 72.375, 21.125))
if not join2:
    print('=== JOIN 2-B: rip stub segs, C28 pad start ===', flush=True)
    fr = fragments('+3V3D', (70.0, 78.0, 18.0, 26.0))
    stub_fr = None
    for f in fr:
        for (ll, it) in f['items']:
            if it[0] == 'pad' and abs(C(it)[0] - 72.725) < 0.01 \
                    and abs(C(it)[1] - 20.5) < 0.01:
                stub_fr = f
    assert stub_fr is not None, 'stub fragment not found by pad'
    print('  stub fragment items: '
          f'{[L.fmt_it(it) for (ll, it) in stub_fr["items"]]}',
          flush=True)
    for (ll, it) in list(stub_fr['items']):
        if it[0] == 'seg':
            if it in pool[ll]:
                pool[ll].remove(it)
            RIP_ADD.setdefault('+3V3D', []).append(
                [it[0], it[1], list(it[2]), it[3]])
    join2 = stub_try('B-pad', ((0,), 72.725, 20.5))
if not join2:
    print('=== JOIN 2-C: C28 relocation scan ===', flush=True)
    for l in range(3):
        for it in list(pool[l]):
            if it[0] == 'pad' and \
                    (R2(it[2][0]), R2(it[2][1])) in \
                    {(72.725, 20.5), (74.275, 20.5)}:
                pool[l].remove(it)
    cands = []
    cx = 73.0
    while cx <= 75.01:
        cy = 19.25
        while cy <= 23.26:
            if not (abs(cx - 73.5) < 0.01 and abs(cy - 20.5) < 0.01):
                cands.append((cx, cy))
            cy += 0.25
        cx += 0.25
    cands.sort(key=lambda cc: (cc[0] - 73.5) ** 2 + (cc[1] - 20.5) ** 2)
    for (cx, cy) in cands:
        if cx + 1.0 > 76.0:
            continue
        p_v3 = (cx - 0.775, cy)
        p_gnd = (cx + 0.775, cy)
        m1, _o1 = pad_margin('+3V3D', p_v3[0], p_v3[1], 0.45, 0.475)
        m2, _o2 = pad_margin('GND', p_gnd[0], p_gnd[1], 0.45, 0.475)
        if m1 < -0.001 or m2 < -0.001:
            continue
        pad_v3 = ('pad', '+3V3D', (p_v3[0], p_v3[1], 0.45, 0.475, 0), 0.2)
        pad_gnd = ('pad', 'GND', (p_gnd[0], p_gnd[1], 0.45, 0.475, 0), 0.2)
        pool[0].append(pad_v3)
        pool[0].append(pad_gnd)
        ok = False
        for hw in (0.125, 0.10):
            for gg in stub_goals(p_v3[0], p_v3[1])[:14]:
                Jv = a_j2('+3V3D', ((0,), p_v3[0], p_v3[1]), gg, hw)
                if Jv is not None and \
                        try_emit('detour_+3V3D_stub', Jv, '+3V3D', hw):
                    print(f'  C28 -> ({cx:.2f},{cy:.2f}) margins '
                          f'{m1:+.3f}/{m2:+.3f} stub hw={hw} goal={gg}',
                          flush=True)
                    ok = True
                    break
            if ok:
                break
        if ok:
            C28_MOVE = {'from': [73.5, 20.5], 'to': [cx, cy], 'rot': 0,
                        'pads': {'+3V3D': list(p_v3), 'GND': list(p_gnd)}}
            join2 = True
            break
        pool[0].remove(pad_v3)
        pool[0].remove(pad_gnd)
    if not join2:
        print('  C28 scan: no legal+routable centre', flush=True)
if not join2:
    print('=== JOIN 2 fence census (box 70.5,76.5,18.5,25.5) ===',
          flush=True)
    for l in range(3):
        for it in pool[l]:
            cc = C(it)
            if 70.5 <= cc[0] <= 76.5 and 18.5 <= cc[1] <= 25.5:
                print(f'   L{l} {L.fmt_it(it)}', flush=True)
assert join2, 'JOIN 2 FAILED all t_aw13 campaigns'
v3 = frag_report('+3V3D', (60, 95, -8, 28))
assert len(v3) == st['base_v3_len'] - 1, \
    f"+3V3D fragments {st['base_v3_len']} -> {len(v3)}, expected -1"
print('JOIN 2 CLOSED', flush=True)

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
print('H5 MODEL COMPLETE (t_aw13)', flush=True)

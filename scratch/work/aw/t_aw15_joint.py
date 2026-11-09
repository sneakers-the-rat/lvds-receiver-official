"""t_aw15: joint re-plan - remove the DM_PHY relay (our own newest
fence around the C28 stub), close join 2 in the opened pocket, then
re-lay DM_PHY around the closed stub. From the t_aw12 cache."""
import wx
_app = wx.App(False)
import sys, json, pickle
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'aw15'}
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

CX, CY, ROT = 75.75, 32.25, 0
R2 = lambda v: round(v, 3)

def frag_report(net, box):
    fr = fragments(net, box)
    print(f'fragments({net}) = {len(fr)} sizes '
          f'{sorted((len(f["items"]) for f in fr), reverse=True)}',
          flush=True)
    return fr

print('--- cached state check ---', flush=True)
assert len(frag_report('XO', (63, 94, 7, 29))) == 1
assert len(frag_report('DM_PHY', (60, 82, -4, 32))) == 1
assert len(frag_report('+3V3D', (60, 95, -8, 28))) == 5

# Phase 1: remove the DM relay journey
print('=== Phase 1: rip dmphy_relay ===', flush=True)
Jdm_old = JOURNEYS['dmphy_relay']
its = journey_items_dense(Jdm_old, 'DM_PHY', hw=0.10)
n_rm = 0
for l in range(3):
    for it in its[l]:
        if it in NEW[l]:
            NEW[l].remove(it)
            n_rm += 1
        if it in pool[l]:
            pool[l].remove(it)
del JOURNEYS['dmphy_relay']
NET_HW.pop('dmphy_relay', None)
print(f'removed {n_rm} NEW items', flush=True)
assert len(frag_report('DM_PHY', (60, 82, -4, 32))) == 2

# Phase 2: rip stub segs, close join 2 from the C28 pad
print('=== Phase 2: join 2 in the opened pocket ===', flush=True)
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
print('stub segs ripped', flush=True)

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

def stub_goals(sx, sy):
    gs = ([(0, 76.525, 24.115), (0, 70.45, 22.425),
           (0, 70.2, 24.575)] + VIA_GOALS + link_pts)
    gs.sort(key=lambda gg: (gg[1] - sx) ** 2 + (gg[2] - sy) ** 2)
    return gs

join2 = False
for hw in (0.125, 0.10):
    for gg in stub_goals(72.725, 20.5):
        Jv = a_j2('+3V3D', ((0,), 72.725, 20.5), gg, hw)
        if Jv is not None:
            print(f'  stub hw={hw} goal={gg}: vias={Jv["vias"]} '
                  f'runs={[(r["layer"], len(r["pts"])) for r in Jv["runs"]]}',
                  flush=True)
            if try_emit('detour_+3V3D_stub', Jv, '+3V3D', hw):
                join2 = True
                break
    if join2:
        break
assert join2, 'join 2 still NONE with DM pocket opened'
v3 = frag_report('+3V3D', (60, 95, -8, 28))
assert len(v3) == 4, f'+3V3D frags {len(v3)} != 4 after stub close'
print('JOIN 2 CLOSED (DM pocket opened)', flush=True)

# Phase 3: re-lay DM_PHY around the closed stub
print('=== Phase 3: DM_PHY re-lay v2 ===', flush=True)
a, b = (69.625, 23.125), (72.875, 19.875)
a_dm = make_astar((66.0, 79.0, 15.0, 29.0), step=0.025)

def compose(legs):
    vias, runs = [], []
    for Jv in legs:
        if Jv is None:
            return None
        vias += [list(v) for v in Jv['vias']]
        runs += Jv['runs']
    return dict(vias=vias, runs=runs)

Jdm = None
dm_hw_used = None
for hw in (0.125, 0.10):
    Jdm = a_dm('DM_PHY', ((0, 1, 2), a[0], a[1]), (1, b[0], b[1]), hw)
    print(f'  DM direct ML hw{hw}: {"FOUND" if Jdm else "NONE"}',
          flush=True)
    if Jdm:
        dm_hw_used = hw
        break
if Jdm is None:
    WPS = [('east', [(1, 74.75, 21.75), (1, 74.75, 20.25)]),
           ('south', [(1, 73.75, 17.25), (1, 71.0, 17.25)]),
           ('north', [(1, 71.0, 25.75), (1, 74.5, 25.75)]),
           ('eastB', [(2, 74.75, 21.75), (2, 74.75, 20.25)])]
    for tag, wps in WPS:
        for hw in (0.125, 0.10):
            legs = []
            cur = ((0, 1, 2), a[0], a[1])
            ok = True
            for (wl, wx, wy) in wps:
                Jv = a_dm('DM_PHY', cur, (wl, wx, wy), hw)
                if Jv is None:
                    ok = False
                    break
                legs.append(Jv)
                cur = ((0, 1, 2), wx, wy)
            if ok:
                Jv = a_dm('DM_PHY', cur, (1, b[0], b[1]), hw)
                if Jv is not None:
                    legs.append(Jv)
                    Jdm = compose(legs)
                    dm_hw_used = hw
                    print(f'  DM waypoint {tag} hw{hw}: FOUND',
                          flush=True)
                    break
        if Jdm:
            break
        print(f'  DM waypoint {tag}: NONE', flush=True)
assert Jdm is not None, 'DM re-lay v2 NONE in all variants'
assert try_emit('dmphy_relay', Jdm, 'DM_PHY', dm_hw_used), \
    'DM v2 gate refused'
NET_HW['dmphy_relay'] = ('DM_PHY', dm_hw_used)
assert len(frag_report('DM_PHY', (60, 82, -4, 32))) == 1
print(f'DM_PHY RE-LAID v2 at hw{dm_hw_used}', flush=True)

# Phase 4: full gate + save
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
json.dump(out, open('scratch/work/aw/build_aw1.json', 'w'), indent=1)
print('saved build_aw1.json', flush=True)
print('H5 MODEL COMPLETE (t_aw15 joint)', flush=True)

"""t_aw16: re-lay ULPI_NXT's In2 diagonal off the stub pocket (BLOCK
wall on its old line), then close join 2 from the C28 pad, DM relay
left in place. From the t_aw12 cache."""
import wx
_app = wx.App(False)
import sys, json, pickle
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'aw16'}
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
base_nxt = frag_report('ULPI_NXT', (60, 82, -4, 32))

# Phase 1: rip ULPI_NXT's In2 diagonal, re-lay with a wall on the line
print('=== Phase 1: ULPI_NXT diagonal re-lay ===', flush=True)
victim = None
for it in list(pool[1]):
    if it[0] == 'seg' and it[1] == 'ULPI_NXT':
        key = tuple(R2(v) for v in it[2][:4])
        if key in {(74.5, 19.25, 69.875, 23.75),
                   (69.875, 23.75, 74.5, 19.25)}:
            victim = it
assert victim is not None, 'ULPI_NXT diagonal not found'
pool[1].remove(victim)
RIP_ADD.setdefault('ULPI_NXT', []).append(
    [victim[0], victim[1], list(victim[2]), victim[3]])
print(f'ripped {L.fmt_it(victim)}', flush=True)

a_nxt = make_astar((68.5, 76.0, 17.5, 25.5), step=0.025)
# control: no wall - must reproduce a route, else endpoints are sealed
Jctl = a_nxt('ULPI_NXT', ((1,), 69.875, 23.75), (1, 74.5, 19.25), 0.10)
print(f'  NXT relay control (no wall): {"FOUND" if Jctl else "NONE"}',
      flush=True)
assert Jctl is not None, 'ULPI_NXT endpoints sealed even without wall'
Jnxt = None
for wall_hw in (0.5, 0.35):
    # wall covers only the MIDDLE of the old line; endpoint throats open
    wall = ('seg', 'BLOCK', (70.625, 23.0, 73.75, 20.0, wall_hw), 0.0)
    pool[1].append(wall)
    Jnxt = a_nxt('ULPI_NXT', ((1,), 69.875, 23.75), (1, 74.5, 19.25),
                 0.10)
    pool[1].remove(wall)
    print(f'  NXT relay inset-wall hw={wall_hw}: '
          f'{"FOUND" if Jnxt else "NONE"}', flush=True)
    if Jnxt:
        break
if Jnxt is None:
    # waypoint detour north, no wall (goals sanity-checked vs fences:
    # +3V3D via (71.125,24.375) r0.4 keeps x>=72.3 at y~24.4)
    legs = []
    cur = ((1,), 69.875, 23.75)
    ok = True
    for (wl, wx, wy) in [(0, 73.0, 24.5), (0, 75.25, 22.5),
                         (1, 75.25, 20.25)]:
        Jv = a_nxt('ULPI_NXT', cur, (wl, wx, wy), 0.10)
        if Jv is None:
            ok = False
            break
        legs.append(Jv)
        cur = ((0, 1, 2), wx, wy)
    if ok:
        Jv = a_nxt('ULPI_NXT', cur, (1, 74.5, 19.25), 0.10)
        if Jv is not None:
            legs.append(Jv)
            vias, runs = [], []
            for Jx in legs:
                vias += [list(v) for v in Jx['vias']]
                runs += Jx['runs']
            Jnxt = dict(vias=vias, runs=runs)
            print('  NXT relay waypoint-north: FOUND', flush=True)
assert Jnxt is not None, 'ULPI_NXT re-lay NONE (wall + waypoint)'
print(f'  NXT relay: vias={Jnxt["vias"]} '
      f'runs={[(r["layer"], len(r["pts"])) for r in Jnxt["runs"]]}',
      flush=True)
assert try_emit('ulpi_nxt_relay', Jnxt, 'ULPI_NXT', 0.10), \
    'NXT relay gate refused'
NET_HW['ulpi_nxt_relay'] = ('ULPI_NXT', 0.10)
nxt = frag_report('ULPI_NXT', (60, 82, -4, 32))
assert len(nxt) == len(base_nxt), 'ULPI_NXT fragment count changed'
print('ULPI_NXT RE-LAID off the pocket', flush=True)

# Phase 2: rip stub segs, close join 2 from the C28 pad
print('=== Phase 2: join 2 ===', flush=True)
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
assert join2, 'join 2 still NONE after ULPI_NXT re-lay'
v3 = frag_report('+3V3D', (60, 95, -8, 28))
assert len(v3) == 4, f'+3V3D frags {len(v3)} != 4 after stub close'
print('JOIN 2 CLOSED (ULPI_NXT moved)', flush=True)
assert len(frag_report('DM_PHY', (60, 82, -4, 32))) == 1

# Phase 3: full gate + save
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
frag_report('ULPI_NXT', (60, 82, -4, 32))

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
print('H5 MODEL COMPLETE (t_aw16 nxt)', flush=True)

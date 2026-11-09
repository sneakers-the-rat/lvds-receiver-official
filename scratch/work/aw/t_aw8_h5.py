"""t_aw8: H5 v2 - dip first, then split ride (B crossing).

Sequence: rip RBIAS staircase (19) -> shrink C22/C24 to board-true
0402 -> move X2 to SITE (pads only; REFCLK via + its 2 F segs ripped)
-> XO F dip -> RBIAS ride -> REFCLK relay -> +3V3D X2 links ->
join 2 stub (fallback: clk tail re-plan E, then retry) -> full gate
-> save build_aw1.json. Usage: t_aw4_h5.py CX CY ROT
"""
import wx
_app = wx.App(False)
import sys, json, math
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'aw4'}
src = open('scratch/work/au/t_au97_phase2y.py').read()
exec(src.split("# 1. RBIAS tail re-lay")[0], g)
pool = g['pool']
NEW = g['NEW']
JOURNEYS = g['JOURNEYS']
NET_HW = g['NET_HW']
B = g['B']
fragments = g['fragments']
make_astar = g['make_astar']
journey_items_dense = g['journey_items_dense']
item_margin = g['item_margin']
try_emit = g['try_emit']
gate_pairs = g['gate_pairs']
C = g['C']
import t_ai_lib as L
from router import dist_to_item

CX, CY, ROT = float(sys.argv[1]), float(sys.argv[2]), int(sys.argv[3])
print(f'=== H5 at X2 site ({CX},{CY}) rot{ROT} ===', flush=True)
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

print('--- baseline fragments ---', flush=True)
base_xo = frag_report('XO', (63, 94, 7, 29))
base_rb = frag_report('RBIAS', (63, 80, 9, 26))
base_v3 = frag_report('+3V3D', (60, 95, -8, 28))
base_clk = frag_report('CAP_CLK', (60, 80, -2, 28))
base_dat = frag_report('CAP_DATA', (60, 80, -2, 28))
base_ref = frag_report('REFCLK', (60, 80, 9, 42))

RIP_ADD = {}

def rip_rounded(l, net, geo4, kind='seg'):
    """Remove item matching by rounded geometry; assert exactly 1."""
    n = 0
    for it in list(pool[l]):
        if it[0] != kind or it[1] != net:
            continue
        if kind == 'seg':
            key = tuple(R2(v) for v in it[2][:4])
            want = tuple(R2(v) for v in geo4)
        else:
            key = (R2(it[2][0]), R2(it[2][1]))
            want = (R2(geo4[0]), R2(geo4[1]))
        if key == want:
            pool[l].remove(it)
            n += 1
    assert n == 1, f'rip {kind} {net} {geo4} L{l}: {n} victims'
    RIP_ADD.setdefault(net, []).append([kind, net, list(geo4), 0.2])
    return n

# ---------------------------------------------------------- 1. staircase
rip19 = [it for it in pool[1] if it[0] == 'seg' and it[1] == 'RBIAS']
assert len(rip19) == 19, f'RBIAS In2 segs {len(rip19)} != 19'
for it in rip19:
    pool[1].remove(it)
    RIP_ADD.setdefault('RBIAS', []).append(
        [it[0], it[1], list(it[2]), it[3]])
print('RBIAS staircase ripped (19)', flush=True)

# ---------------------------------------------------------- 2. shrink
def shrink_pad(net, old_cx, new_cx, cy=18.0):
    for l in range(3):
        for it in list(pool[l]):
            if it[0] == 'pad' and it[1] == net:
                cc = C(it)
                if abs(cc[0] - old_cx) < 0.01 and abs(cc[1] - cy) < 0.01:
                    pool[l].remove(it)
                    pool[l].append(('pad', net,
                                     (new_cx, cy, 0.28, 0.31, 0), it[3]))
                    return True
    return False
for net, o, n in [('PHY_1V8', 71.725, 72.02), ('GND', 73.275, 72.98),
                  ('+3V3A', 67.975, 68.27), ('GND', 69.525, 69.23)]:
    assert shrink_pad(net, o, n), f'shrink {net} {o} failed'
print('C22+C24 shrunk to board-true 0402 (pads 0.56x0.62 at +/-0.48)',
      flush=True)

# ---------------------------------------------------------- 3. X2 move
PADS0 = [('+3V3D', -1.05, 0.825), ('GND', 1.05, 0.825),
         ('REFCLK', 1.05, -0.825), ('+3V3D', -1.05, -0.825)]
def offs(dx, dy):
    if ROT == 0:
        return dx, dy, 0.65, 0.55
    return -dy, dx, 0.55, 0.65
old_pads = []
for l in range(3):
    for it in list(pool[l]):
        if it[0] == 'pad' and (R2(it[2][0]), R2(it[2][1])) in \
                {(70.45, 24.575), (72.55, 24.575), (72.55, 22.925),
                 (70.45, 22.925)}:
            pool[l].remove(it)
            old_pads.append(it)
assert len(old_pads) == 4, f'X2 old pads removed {len(old_pads)} != 4'
new_pads = {}
for (net, dx, dy) in PADS0:
    ox, oy, hw, hh = offs(dx, dy)
    it = ('pad', net, (CX + ox, CY + oy, hw, hh, 0), 0.2)
    pool[0].append(it)
    new_pads.setdefault(net, []).append((CX + ox, CY + oy))
    m, o = pad_margin(net, CX + ox, CY + oy, hw, hh)
    print(f'  X2 pad {net} at ({CX + ox:.3f},{CY + oy:.3f}) '
          f'margin {m:+.3f}' + ('' if o is None else
          f' vs {L.fmt_it(o)}'), flush=True)
    assert m >= -0.001, 'moved X2 pad not copper-legal'
print('X2 pads moved', flush=True)
# REFCLK via + its 2 F segs (they attach to the old pad site)
for l in range(3):
    rip_rounded(l, 'REFCLK', (71.875, 23.375), kind='via')
rip_rounded(0, 'REFCLK', (72.3, 22.925, 72.55, 22.925))
rip_rounded(0, 'REFCLK', (71.875, 23.375, 72.3, 22.925))
print('REFCLK via + F segs ripped', flush=True)

# ---------------------------------------------------------- 5. XO dip
print('=== XO F dip ===', flush=True)
a_dip = make_astar((66.0, 76.0, 16.5, 27.5), step=0.025)
J = a_dip('XO', ((0,), 71.625, 25.625), (1, 68.875, 20.375), 0.10)
if J is not None:
    print(f'dip ML: vias={J["vias"]} '
          f'runs={[(r["layer"], len(r["pts"])) for r in J["runs"]]}',
          flush=True)
    assert try_emit('xo_bridge', J, 'XO', 0.10), 'dip gate refused'
else:
    print('dip ML NONE; trying split legs', flush=True)
    a_f = make_astar((66.0, 75.0, 17.0, 27.5), step=0.025)
    J1 = a_f('XO', ((0,), 71.625, 25.625), (0, 70.15, 18.6), 0.10,
             layer_lock=(True, False, False))
    print('  F leg to (70.15,18.6): ' +
          ('NONE' if J1 is None else f'{len(J1["runs"][0]["pts"])} pts'),
          flush=True)
    assert J1 is not None, 'F leg NONE - H5 piece 4 fails at this site'
    dive = None
    for dv in [(70.15, 18.6), (70.95, 18.5), (70.6, 18.55),
               (70.35, 18.6), (70.8, 18.45)]:
        ok = True
        for l in range(3):
            v = ('via', 'XO', (dv[0], dv[1], 0.25), 0.2)
            for o in pool[l]:
                if o[1] == 'XO':
                    continue
                if item_margin(l, v, [o]) < -0.001:
                    ok = False
        print(f'  dive {dv}: via field {"CLEAR" if ok else "blocked"}',
              flush=True)
        if ok:
            dive = dv
            break
    assert dive is not None, 'no clear dive for the F dip'
    J1b = a_f('XO', ((0,), 71.625, 25.625), (0, dive[0], dive[1]), 0.10,
              layer_lock=(True, False, False))
    assert J1b is not None, 'F leg to chosen dive NONE'
    a_i = make_astar((66.0, 75.0, 17.0, 27.5), step=0.025)
    J2 = a_i('XO', ((1,), dive[0], dive[1]), (1, 68.875, 20.375), 0.10,
             layer_lock=(False, True, False))
    assert J2 is not None, 'In2 hop NONE'
    J = dict(vias=[list(dive)], runs=J1b['runs'] + J2['runs'])
    assert try_emit('xo_bridge', J, 'XO', 0.10), 'dip gate refused'
xo_now = frag_report('XO', (63, 94, 7, 29))
assert len(xo_now) == 1, f'XO fragments {len(xo_now)} != 1'
print('XO BRIDGE CLOSED', flush=True)

# ---------------------------------------------------------- 5. RBIAS ride (split, B crossing under the dip band)
print('=== RBIAS ride (split: In2 leg, dive NE of dip band, B leg) ===',
      flush=True)
a_rb = make_astar((67.0, 75.5, 10.5, 22.5), step=0.025)
rb_done = False
tried = 0
for dyi in range(0, 30):
    if rb_done:
        break
    for dxi in range(0, 23):
        dive = (70.2 + 0.1 * dxi, 16.6 + 0.1 * dyi)
        J1 = a_rb('RBIAS', ((1,), 73.875, 11.625), (1, dive[0], dive[1]),
                  0.125, layer_lock=(False, True, False))
        if J1 is None:
            continue
        J2 = a_rb('RBIAS', ((2,), dive[0], dive[1]), (2, 69.625, 20.625),
                  0.125, layer_lock=(False, False, True))
        if J2 is None:
            continue
        tried += 1
        Jr = dict(vias=[list(dive)], runs=J1['runs'] + J2['runs'])
        print(f'  dive {dive}: composed '
              f'{[(r["layer"], len(r["pts"])) for r in Jr["runs"]]}',
              flush=True)
        if try_emit('rbias_relay', Jr, 'RBIAS', 0.125):
            print(f'  ride EMITTED at dive {dive} '
                  f'(composed candidates tried: {tried})', flush=True)
            rb_done = True
            break
if not rb_done:
    for hw in (0.125, 0.10):
        Jr = a_rb('RBIAS', ((0, 1, 2), 73.875, 11.625),
                  (2, 69.625, 20.625), hw)
        print(f'  full-ML ride hw={hw}: ' +
              ('NONE' if Jr is None else
               f'vias={Jr["vias"]} '
               f'runs={[(r["layer"], len(r["pts"])) for r in Jr["runs"]]}'),
              flush=True)
        if Jr is not None and try_emit('rbias_relay', Jr, 'RBIAS', hw):
            rb_done = True
            break
assert rb_done, 'RBIAS RIDE FAILED'
rb_now = frag_report('RBIAS', (63, 80, 9, 26))
assert len(rb_now) == 1, f'RBIAS fragments {len(rb_now)} != 1'
print('RBIAS RIDE CLOSED', flush=True)

# ---------------------------------------------------------- 6. REFCLK relay
print('=== REFCLK relay ===', flush=True)
ref_pad = new_pads['REFCLK'][0]
a_ref = make_astar((67.0, 78.5, 20.0, 34.0), step=0.025)
Jref = a_ref('REFCLK', ((1,), 71.125, 23.375), (0, ref_pad[0], ref_pad[1]),
             0.10)
assert Jref is not None, 'REFCLK relay NONE'
assert try_emit('refclk_relay', Jref, 'REFCLK', 0.10), 'REFCLK gate refused'
ref_now = frag_report('REFCLK', (60, 80, 9, 42))
assert len(ref_now) == len(base_ref), 'REFCLK fragment count changed'
print('REFCLK RELAY CLOSED', flush=True)

def astar_goals(ast, net, start, goals, hw):
    """goals: list of (layer, x, y) single-layer goals, tried in order."""
    for gg in goals:
        Jv = ast(net, start, gg, hw)
        if Jv is not None:
            return Jv, gg
    return None, None

# ---------------------------------------------------------- 7. +3V3D X2 links
print('=== +3V3D X2 links ===', flush=True)
a_v3 = make_astar((67.0, 78.5, 19.5, 34.0), step=0.025)
VIA_GOALS = [(0, 71.125, 24.375), (1, 71.125, 24.375),
             (2, 71.125, 24.375)]
for i, (px, py) in enumerate(new_pads['+3V3D']):
    goals = [(0, 70.45, 22.425), (0, 70.2, 24.575)] + VIA_GOALS
    Jv, gg = astar_goals(a_v3, '+3V3D', ((0,), px, py), goals, 0.125)
    assert Jv is not None, f'X2 +3V3D pad ({px},{py}) link NONE'
    assert try_emit(f'x2_v3a_{i}', Jv, '+3V3D', 0.125), \
        f'X2 +3V3D pad ({px},{py}) link gate refused'
    print(f'  X2 +3V3D pad ({px:.2f},{py:.2f}) linked via goal {gg}',
          flush=True)
v3_now = frag_report('+3V3D', (60, 95, -8, 28))

# ---------------------------------------------------------- 8. join 2
print('=== JOIN 2: +3V3D stub ===', flush=True)
a_j2 = make_astar((68.0, 78.5, 18.5, 34.0), step=0.025)
def stub_try(tag):
    goals = ([(0, new_pads['+3V3D'][0][0], new_pads['+3V3D'][0][1]),
              (0, new_pads['+3V3D'][1][0], new_pads['+3V3D'][1][1])]
             + VIA_GOALS + [(0, 70.2, 24.575)])
    for hw in (0.15, 0.125, 0.10):
        for gg in goals:
            Jv = a_j2('+3V3D', ((0,), 72.375, 21.125), gg, hw)
            if Jv is not None:
                print(f'  stub ({tag}) hw={hw} goal={gg}: '
                      f'vias={Jv["vias"]} '
                      f'runs={[(r["layer"], len(r["pts"])) for r in Jv["runs"]]}',
                      flush=True)
                if try_emit('detour_+3V3D_stub', Jv, '+3V3D', hw):
                    return True
    print(f'  stub ({tag}): NONE at all widths/goals', flush=True)
    return False

join2 = stub_try('post-H5')
if not join2:
    print('=== JOIN 2 phase B: re-plan clk tail E ===', flush=True)
    old_clk9 = JOURNEYS['clk9']
    old_arr = JOURNEYS['arr_clk']
    old_items = {}
    for nm, JJ in (('clk9', old_clk9), ('arr_clk', old_arr)):
        its = journey_items_dense(JJ, 'CAP_CLK', hw=0.10)
        old_items[nm] = its
        for l in range(3):
            for it in its[l]:
                if it in NEW[l]:
                    NEW[l].remove(it)
                if it in pool[l]:
                    pool[l].remove(it)
    del JOURNEYS['clk9']
    del JOURNEYS['arr_clk']
    NET_HW.pop('clk9', None)
    NET_HW.pop('arr_clk', None)
    wall = ('seg', 'BLOCK', (69.0, 21.8, 74.5, 21.8, 0.45), 0.0)
    pool[0].append(wall)
    a_tail = make_astar((63.0, 77.5, 15.0, 27.0), step=0.025)
    Jt = a_tail('CAP_CLK', ((1,), 64.75, 16.95), (1, 74.4, 22.9), 0.10)
    pool[0].remove(wall)
    assert Jt is not None, 'clk tail re-plan NONE even with F wall'
    xs_f = [p[0] for r in Jt['runs'] if r['layer'] == 0
            for p in r['pts'] if 21.3 < p[1] < 22.3]
    print(f'  new tail: vias={Jt["vias"]} '
          f'runs={[(r["layer"], len(r["pts"])) for r in Jt["runs"]]} '
          f'F pts in y21.3-22.3 band: x range '
          f'{(min(xs_f), max(xs_f)) if xs_f else None}', flush=True)
    ride_run = [r for r in old_clk9['runs'] if r['layer'] == 2][0]
    f_tail = [r for r in old_clk9['runs'] if r['layer'] == 0
              and tuple(r['pts'][0]) == (74.4, 22.9)][0]
    new_clk9 = dict(vias=[[64.75, 16.95]] + Jt['vias'] + [[74.4, 22.9]],
                    runs=[ride_run] + Jt['runs'] + [f_tail])
    assert try_emit('clk9', new_clk9, 'CAP_CLK', 0.10), 'new clk9 refused'
    NET_HW['clk9'] = ('CAP_CLK', 0.10)
    frag_report('CAP_CLK', (60, 80, -2, 28))
    join2 = stub_try('post-tail-replan')
assert join2, 'JOIN 2 FAILED'
v3_end = frag_report('+3V3D', (60, 95, -8, 28))
print(f'+3V3D fragments: baseline {len(base_v3)} -> now {len(v3_end)}',
      flush=True)
assert len(v3_end) == len(base_v3) - 1, 'stub join did not merge exactly 1'

# ---------------------------------------------------------- 9. full gate
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
print('H5 MODEL COMPLETE', flush=True)

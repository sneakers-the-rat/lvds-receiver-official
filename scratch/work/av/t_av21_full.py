"""t_av21: CAP landing design v4 - full sequence.

Proven pieces (t_av20): staircase rip (all 19) + C49 E+0.5 + web
emit + ULPI_DIR tail re-lay (no dummies) + MULTI-LAYER XO dip
(via (73.9,21.425), B run 96 pts, In2 run 354 pts; gate +0.000 vs
C28 GND pad, +0.027 vs CAP_CLK via) + RBIAS ride (dive
(69.925,20.475) area). This script runs them in dependency order
(bridge emitted BEFORE the ride A*), then join 2 (t_av13 logic),
full gate, fragment verification, saves build_av1.json +
pool_av1.json.
"""
import wx
_app = wx.App(False)
import sys, json, math
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'av21'}
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
import numpy as np

R2 = lambda v: round(v, 3)


def frag_report(net, box):
    fr = fragments(net, box)
    print(f'fragments({net}) = {len(fr)} sizes '
          f'{sorted((len(f["items"]) for f in fr), reverse=True)}',
          flush=True)
    return fr


def remove_journey(name):
    net, hw = NET_HW[name]
    its = journey_items_dense(JOURNEYS[name], net, hw=hw)
    for l in range(3):
        for it in its[l]:
            NEW[l].remove(it)
            pool[l].remove(it)
    del JOURNEYS[name]
    del NET_HW[name]


# ------------------------------------------------------------- rip 19
rip_now = [it for it in pool[1] if it[0] == 'seg' and it[1] == 'RBIAS']
assert len(rip_now) == 19, f'rip set {len(rip_now)} != 19'
for it in rip_now:
    pool[1].remove(it)
RIP_ADD = {'RBIAS': [[it[0], it[1], list(it[2]), it[3]] for it in rip_now]}
print(f'RBIAS staircase: ripped {len(rip_now)} (all In2 segs; the '
      f'(73.875,11.625) via disc remains)', flush=True)

# ------------------------------------------------- 1. C49 shift E +0.5
print('=== C49 shift E to (70.5,19.5) ===', flush=True)
C49_OLD = (70.0, 19.5)
C49_NEW = (70.5, 19.5)


def find_pad(net, cx, cy=19.5):
    for l in range(3):
        for it in pool[l]:
            if it[0] == 'pad' and it[1] == net:
                cc = C(it)
                if abs(cc[0] - cx) < 0.01 and abs(cc[1] - cy) < 0.01:
                    return l, it
    raise AssertionError(f'pad {net} at ({cx},{cy}) not found')


for net, cx in (('+3V3A', 69.225), ('GND', 70.775)):
    l, it = find_pad(net, cx)
    pool[l].remove(it)
    kind, ntn, (ccx, ccy, hw_, hh, rot), clr = it
    pool[l].append(('pad', ntn, (ccx + 0.5, ccy, hw_, hh, rot), clr))
for l in range(3):
    for it in list(pool[l]):
        if it[0] == 'seg' and it[1] == '+3V3A':
            x1, y1, x2, y2, hw_ = it[2]
            if (abs(x2 - 69.225) < 0.01 and abs(y2 - 19.5) < 0.01
                    and abs(hw_ - 0.150) < 0.001):
                pool[l].remove(it)
                print(f'  C49 web end seg removed L{l}', flush=True)
ast = make_astar((66.0, 74.0, 15.0, 23.0), step=0.025)
J = ast('+3V3A', ((0,), 69.725, 19.5), (0, 69.225, 19.5), 0.15)
assert J is not None, 'C49 web A* NONE'
assert try_emit('c49_web_v3a', J, '+3V3A', 0.15), 'C49 web gate refused'
print('C49 moved; +3V3A web re-laid', flush=True)

# ------------------------------------------------- 2. DIR tail re-lay
print('=== ULPI_DIR long B seg re-lay (no dummies) ===', flush=True)
DIR_SEG = (71.375, 19.125, 68.875, 29.0)
n = 0
for it in list(pool[2]):
    if it[0] == 'seg' and it[1] == 'ULPI_DIR' \
            and tuple(R2(v) for v in it[2][:4]) == DIR_SEG:
        pool[2].remove(it)
        n += 1
assert n == 1, f'DIR seg rip {n} != 1'
a_dir = make_astar((68.3, 74.8, 18.6, 29.6), step=0.025)
J = a_dir('ULPI_DIR', ((2,), 71.375, 19.125), (2, 68.875, 29.0), 0.10)
assert J is not None, 'DIR re-lay NONE'
assert try_emit('dir_tail_relay', J, 'ULPI_DIR', 0.10), 'DIR gate refused'
print('DIR re-laid', flush=True)

# ------------------------------------------------- 3. XO bridge (dip)
print('=== XO bridge: multi-layer dip ===', flush=True)
a_dip = make_astar((66.5, 76.0, 14.5, 27.0), step=0.025)
J = a_dip('XO', ((2,), 71.875, 19.625), (1, 68.875, 20.375), 0.10)
assert J is not None, 'DIP A* NONE'
print(f'dip: vias={J["vias"]} '
      f'runs={[(r["layer"], len(r["pts"])) for r in J["runs"]]}',
      flush=True)
assert try_emit('xo_bridge', J, 'XO', 0.10), 'xo_bridge gate refused'
xo = frag_report('XO', (63, 94, 7, 29))
assert len(xo) == 1, f'XO fragments {len(xo)} != 1 after bridge'
print('XO BRIDGE CLOSED (fragments == 1)', flush=True)

# ------------------------------------------------- 4. RBIAS ride
print('=== RBIAS ride (split-layer) ===', flush=True)
# Plan: In2 up the staircase corridor, dive to B ~y16.4, B diagonal
# to the terminus via. (The full-In2 diagonal conflicts with the
# bridge's In2 S-band run; DIR's diagonal is B-only at the ride's
# In2 start, so the split separates the two journeys.)
a_rb = make_astar((67.0, 75.0, 10.5, 22.5), step=0.025)
rb_done = False
for dive in [(72.5, 17.15), (72.45, 17.2), (72.55, 17.1),
             (72.4, 17.3), (72.6, 17.0), (72.3, 17.4),
             (72.7, 16.8),
             (73.9, 16.4), (73.85, 16.2), (73.95, 16.6),
             (73.8, 16.0), (74.0, 16.9), (73.75, 15.7),
             (74.05, 17.2)]:
    J1 = a_rb('RBIAS', ((1,), 73.875, 11.625), (1, dive[0], dive[1]),
              0.125, layer_lock=(False, True, False))
    if J1 is None:
        print(f'  dive {dive}: In2 leg NONE', flush=True)
        continue
    J2 = a_rb('RBIAS', ((2,), dive[0], dive[1]), (2, 69.625, 20.625),
              0.125, layer_lock=(False, False, True))
    if J2 is None:
        print(f'  dive {dive}: B leg NONE', flush=True)
        continue
    J = dict(vias=[list(dive)], runs=J1['runs'] + J2['runs'])
    print(f'  dive {dive}: composed runs='
          f'{[(r["layer"], len(r["pts"])) for r in J["runs"]]}',
          flush=True)
    if try_emit('rbias_relay', J, 'RBIAS', 0.125):
        rb_done = True
        break
if not rb_done:
    for hw in (0.125, 0.10):
        J = a_rb('RBIAS', ((0, 1, 2), 73.875, 11.625),
                 (2, 69.625, 20.625), hw)
        print(f'  full-ML ride hw={hw}: ' +
              ('NONE' if J is None else
               f'vias={J["vias"]} runs={[(r["layer"], len(r["pts"])) for r in J["runs"]]}'),
              flush=True)
        if J is not None and try_emit('rbias_relay', J, 'RBIAS', hw):
            rb_done = True
            break
assert rb_done, 'RBIAS RIDE FAILED'
frag_report('RBIAS', (63, 80, 9, 26))

# ------------------------------------------------- 5. JOIN 2
print('=== JOIN 2: +3V3D stub ride ===', flush=True)
v3_before = frag_report('+3V3D', (60, 95, -8, 28))
astar_f = make_astar((68.8, 74.2, 19.2, 24.4), step=0.025)


def stub_ride(tag):
    for hw in (0.15, 0.125, 0.10):
        J = astar_f('+3V3D', (0, 72.375, 21.125), (0, 70.45, 22.925),
                    hw, layer_lock=(True, False, False))
        if J is None:
            print(f'  stub A* ({tag}) hw={hw}: NONE', flush=True)
            continue
        print(f'  stub A* ({tag}) hw={hw}: vias={J["vias"]} '
              f'runs={[(r["layer"], len(r["pts"])) for r in J["runs"]]}',
              flush=True)
        if try_emit('detour_+3V3D_stub', J, '+3V3D', hw):
            return True
    return False


join2_done = stub_ride('unmodified clk9')
if not join2_done:
    print('=== JOIN 2 phase B: re-plan arr_clk tail eastward ===',
          flush=True)
    old_clk9 = JOURNEYS['clk9']
    old_arr = JOURNEYS['arr_clk']
    old_clk9_items = journey_items_dense(old_clk9, 'CAP_CLK', hw=0.10)
    old_arr_items = journey_items_dense(old_arr, 'CAP_CLK', hw=0.10)
    ride_run = [r for r in old_clk9['runs'] if r['layer'] == 2][0]
    in2_run = [r for r in old_clk9['runs'] if r['layer'] == 1][0]
    f_tail = [r for r in old_clk9['runs']
              if r['layer'] == 0
              and tuple(r['pts'][0]) == (74.4, 22.9)][0]
    astar_e = make_astar((69.9, 73.5, 20.9, 22.6), step=0.025)
    for P in [(71.2, 21.8), (71.3, 21.75), (71.15, 21.9), (71.25, 21.7)]:
        JE = astar_e('CAP_CLK', ((1,), 70.1, 21.8), (1, P[0], P[1]),
                     0.10, layer_lock=(False, True, False))
        if JE is None:
            print(f'  extension A* to {P}: NONE', flush=True)
            continue
        ext_pts = [tuple(p) for p in JE['runs'][0]['pts']]
        print(f'  extension to {P}: {len(ext_pts)} pts', flush=True)
        for src_items in (old_clk9_items, old_arr_items):
            for l in range(3):
                for it in src_items[l]:
                    NEW[l].remove(it)
                    pool[l].remove(it)
        new_arr = dict(vias=[], runs=[dict(
            layer=1, pts=[list(p) for p in
                          [tuple(p) for p in old_arr['runs'][0]['pts']]
                          + ext_pts[1:]])])
        new_clk9 = dict(
            vias=[[64.75, 16.95], list(P), [73.25, 21.75], [74.4, 22.9]],
            runs=[ride_run,
                  dict(layer=0, pts=[list(P), [73.25, 21.75]]),
                  in2_run, f_tail])
        ok = True
        for name, JJ in (('arr_clk', new_arr), ('clk9', new_clk9)):
            if not try_emit(name, JJ, 'CAP_CLK', 0.10):
                ok = False
                break
        if ok and stub_ride(f'tail at {P}'):
            join2_done = True
            break
        for name, JJ in (('arr_clk', new_arr), ('clk9', new_clk9)):
            if name in JOURNEYS:
                its = journey_items_dense(JJ, 'CAP_CLK', hw=0.10)
                for l in range(3):
                    for it in its[l]:
                        if it in NEW[l]:
                            NEW[l].remove(it)
                        if it in pool[l]:
                            pool[l].remove(it)
                del JOURNEYS[name]
                NET_HW.pop(name, None)
        if 'detour_+3V3D_stub' in JOURNEYS:
            remove_journey('detour_+3V3D_stub')
        for l in range(3):
            for it in old_arr_items[l]:
                NEW[l].append(it)
                pool[l].append(it)
            for it in old_clk9_items[l]:
                NEW[l].append(it)
                pool[l].append(it)
        JOURNEYS['arr_clk'] = old_arr
        JOURNEYS['clk9'] = old_clk9
        NET_HW['arr_clk'] = ('CAP_CLK', 0.10)
        NET_HW['clk9'] = ('CAP_CLK', 0.10)
        print(f'  restored originals after P={P}', flush=True)
assert join2_done, 'JOIN 2 FAILED: stub ride not emitted'
v3_after = frag_report('+3V3D', (60, 95, -8, 28))
print(f'+3V3D sizes before={sorted((len(f["items"]) for f in v3_before), reverse=True)} '
      f'after={sorted((len(f["items"]) for f in v3_after), reverse=True)}',
      flush=True)

# ------------------------------------------------- 6. gate + save
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

print('=== final fragment counts ===', flush=True)
frag_report('CAP_CLK', (60, 80, -2, 28))
frag_report('CAP_DATA', (60, 80, -2, 28))
frag_report('XO', (63, 94, 7, 29))
frag_report('RBIAS', (63, 80, 9, 26))
frag_report('ULPI_DIR', (60, 82, -4, 32))

RIP2_OUT = {net: [list(x) for x in lst] for net, lst in B['rip2'].items()}
for net, lst in RIP_ADD.items():
    RIP2_OUT.setdefault(net, []).extend(lst)
out = dict(journeys=JOURNEYS, fixed=B['fixed'], rip2=RIP2_OUT,
           extra=B['extra'], arrivals=B['arrivals'],
           clk_via=(70.2, 1.8), exit_via=(69.075, 2.8), u9_shift=1.25,
           moves={'C49': {'from': list(C49_OLD), 'to': list(C49_NEW)}})
json.dump(out, open('scratch/work/av/build_av1.json', 'w'), indent=1)
pool_out = {str(l): [[it[0], it[1], list(it[2]), it[3]] for it in pool[l]]
            for l in range(3)}
json.dump(pool_out, open('scratch/work/av/pool_av1.json', 'w'))
print('saved build_av1.json + pool_av1.json', flush=True)
print('DESIGN COMPLETE', flush=True)

"""t_av4: close the two open CAP joins in the exact item model.

Base state: au93 model rebuilt exactly as t_au97_phase2y does
(build_au97 minus detour_RBIAS_tail, which this design supersedes).

JOIN 1 (XO bridge): rip RBIAS's 17 In2 diagonals + 2 tail segs
(rounded-coordinate match), A* a replacement RBIAS ride starting at
the existing via (73.875,11.625) and ending at the existing via
(69.625,20.625), then emit the XB10 XO dip and verify by effect
(XO fragments 2 -> 1).

JOIN 2 (+3V3D stub): first try an F-only A* from the decap fragment
terminal (72.375,21.125) to X2.4's pad (70.45,22.925) against the
unmodified clk9. If NONE, re-plan the arr_clk tail: move clk9's
(70.1,21.8) dive via east to a candidate P (In2 extension A*), then
retry the F ride. Verify by effect (+3V3D fragment merge).

Outputs: build_av1.json (manifest) + pool_av1.json (final pool
snapshot = the physical build's ground truth).
"""
import wx
_app = wx.App(False)
import sys, json, copy
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'av4'}
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
import t_ai_lib as L

R2 = lambda v: round(v, 3)


def rgeom(it):
    return tuple(R2(v) for v in it[2])


def frag_report(net, box):
    fr = fragments(net, box)
    print(f'fragments({net}) = {len(fr)} sizes '
          f'{sorted((len(f["items"]) for f in fr), reverse=True)}',
          flush=True)
    return fr


print('=== baseline fragment counts (au93-state model) ===', flush=True)
frag_report('XO', (63, 94, 7, 29))
v3_before = frag_report('+3V3D', (60, 95, -8, 28))
for net in ('CAP_CLK', 'CAP_DATA'):
    fr = frag_report(net, (60, 80, -2, 28))
    for f in fr:
        if len(f['items']) <= 2:
            for (l, it) in f['items']:
                print(f'  small fragment item: L{l} {L.fmt_it(it)}',
                      flush=True)
frag_report('RBIAS', (63, 80, 9, 26))

# ---------------------------------------------------------------- JOIN 1
print('=== JOIN 1: RBIAS staircase rip (rounded match) ===', flush=True)
STUB = (73.875, 11.625, 73.875, 12.875)
VERT = (73.875, 12.875, 73.875, 16.375)
rip_now, keep_vert = [], None
for it in list(pool[1]):
    if it[0] == 'seg' and it[1] == 'RBIAS':
        rg = rgeom(it)
        if rg == STUB:
            continue
        if rg == VERT:
            keep_vert = it
            continue
        rip_now.append(it)
print(f'staircase segs to rip now: {len(rip_now)} '
      f'(expect 19 = 17 diagonals + 2 tails)', flush=True)
assert len(rip_now) == 19, 'rip set size mismatch - aborting'
for it in rip_now:
    pool[1].remove(it)
RIP_ADD = {'RBIAS': [[it[0], it[1], list(it[2]), it[3]] for it in rip_now]}

def remove_journey(name):
    net, hw = NET_HW[name]
    its = journey_items_dense(JOURNEYS[name], net, hw=hw)
    for l in range(3):
        for it in its[l]:
            NEW[l].remove(it)
            pool[l].remove(it)
    del JOURNEYS[name]
    del NET_HW[name]


# XB10 as inherited CROSSES arr_data's In2 diagonal (70.5,21.0)->
# (72.3,19.2): the dip via must sit SW of that line. The dip is
# therefore A*-designed, not re-gated. Order: dip FIRST (maximal
# freedom), then the RBIAS ride routes around the real dip. If the
# ride then fails everywhere, fall back to reserving a dip corridor
# with dummy fences during the ride A*.
print('=== JOIN 1a: XO dip A* (dip first) ===', flush=True)
# t_av6 probe: the only viafit cells in the knot are a 7-cell lens
# at (73.90-73.95, 21.45-21.50); the dip must ride B NE to that via
# and return on In2 around the ULPI_NXT diagonal. Wide box.
astar_dip = make_astar((68.3, 74.6, 18.9, 26.3), step=0.025)


def dip_astar():
    J = astar_dip('XO', ((2,), 71.875, 19.625), (1, 68.875, 20.375),
                  0.10)
    if J is None:
        print('  dip A*: NONE', flush=True)
        return False
    print(f'  dip A*: vias={J["vias"]} '
          f'runs={[(r["layer"], len(r["pts"])) for r in J["runs"]]}',
          flush=True)
    if not try_emit('xo_bridge', J, 'XO', 0.10):
        return False
    fr = frag_report('XO', (63, 94, 7, 29))
    if len(fr) != 1:
        print('  dip emitted but XO fragments != 1 - removing',
              flush=True)
        remove_journey('xo_bridge')
        return False
    return True


xo_done = dip_astar()

print('=== JOIN 1b: RBIAS A* re-lay ===', flush=True)
astar_rb = make_astar((68.5, 74.75, 11.0, 21.5), step=0.025)
attempts = [
    (((0, 1, 2), 73.875, 11.625), 2, 0.125),
    (((0, 1, 2), 73.875, 11.625), 2, 0.10),
    (((2,), 73.875, 11.625), 2, 0.125),
    (((2,), 73.875, 11.625), 2, 0.10),
    (((0, 1, 2), 73.875, 11.625), 1, 0.125),
]


def rbias_ride():
    for start, glayer, hw in attempts:
        J = astar_rb('RBIAS', start, (glayer, 69.625, 20.625), hw)
        if J is None:
            print(f'  A* start={start[0]} goal_layer={glayer} '
                  f'hw={hw}: NONE', flush=True)
            continue
        print(f'  A* start={start[0]} goal_layer={glayer} hw={hw}: '
              f'vias={J["vias"]} '
              f'runs={[(r["layer"], len(r["pts"])) for r in J["runs"]]}',
              flush=True)
        if try_emit('rbias_relay', J, 'RBIAS', hw):
            used = [rgeom(it) for it in
                    journey_items_dense(J, 'RBIAS', hw=hw)[1]]
            if keep_vert is not None and rgeom(keep_vert) not in used:
                pool[1].remove(keep_vert)
                RIP_ADD['RBIAS'].append(
                    [keep_vert[0], keep_vert[1], list(keep_vert[2]),
                     keep_vert[3]])
                print('  vertical unused by ride - ripped too '
                      f'(total RBIAS rips: {len(RIP_ADD["RBIAS"])})',
                      flush=True)
            else:
                print('  ride uses the In2 vertical - it stays',
                      flush=True)
            return True
        print('  ride emit refused - next attempt', flush=True)
    return False


rb_done = rbias_ride()
if not rb_done and xo_done:
    print('=== JOIN 1 fallback: reserve dip corridor, ride, then dip ===',
          flush=True)
    remove_journey('xo_bridge')
    xo_done = False
    DUM = 'BLOCK_RSVD'
    dummies = []
    for l in range(3):
        dummies.append((l, ('via', DUM, (70.9, 20.0, 0.30), 0.2)))
    for a, b in (((71.875, 19.625), (70.9, 20.0)),
                 ((70.9, 20.0), (69.9, 19.8)),
                 ((69.9, 19.8), (68.875, 20.375))):
        dummies.append((2, ('seg', DUM, (a[0], a[1], b[0], b[1], 0.15),
                            0.2)))
        dummies.append((1, ('seg', DUM, (a[0], a[1], b[0], b[1], 0.15),
                            0.2)))
    for l, it in dummies:
        pool[l].append(it)
    rb_done = rbias_ride()
    for l, it in dummies:
        pool[l].remove(it)
    if rb_done:
        xo_done = dip_astar()
assert xo_done and rb_done, 'JOIN 1 FAILED: dip/ride pair not closed'
frag_report('RBIAS', (63, 80, 9, 26))
frag_report('XO', (63, 94, 7, 29))

# ---------------------------------------------------------------- JOIN 2
print('=== JOIN 2: +3V3D stub ride ===', flush=True)
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
              if r['layer'] == 0 and tuple(r['pts'][0]) == (74.4, 22.9)][0]
    astar_e = make_astar((69.9, 73.5, 20.9, 22.6), step=0.025)
    for P in [(71.2, 21.8), (71.3, 21.75), (71.15, 21.9), (71.25, 21.7)]:
        JE = astar_e('CAP_CLK', ((1,), 70.1, 21.8), (1, P[0], P[1]),
                     0.10, layer_lock=(False, True, False))
        if JE is None:
            print(f'  extension A* to {P}: NONE', flush=True)
            continue
        ext_pts = [tuple(p) for p in JE['runs'][0]['pts']]
        print(f'  extension to {P}: {len(ext_pts)} pts', flush=True)
        # remove old clk9 + arr_clk items
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
        if ok:
            print(f'  tail re-planned: dive via now at {P}', flush=True)
            if stub_ride(f'tail at {P}'):
                join2_done = True
                break
            print('  stub ride still fails with this P - restoring '
                  'original clk9/arr_clk', flush=True)
            for name, JJ in (('arr_clk', new_arr), ('clk9', new_clk9)):
                its = journey_items_dense(JJ, 'CAP_CLK', hw=0.10)
                for l in range(3):
                    for it in its[l]:
                        NEW[l].remove(it)
                        pool[l].remove(it)
                del JOURNEYS[name]
        else:
            print(f'  re-emit refused for P={P} - restoring originals',
                  flush=True)
            for l in range(3):
                for it in old_arr_items[l]:
                    NEW[l].append(it)
                    pool[l].append(it)
                for it in old_clk9_items[l]:
                    NEW[l].append(it)
                    pool[l].append(it)
            JOURNEYS['arr_clk'] = old_arr
            JOURNEYS['clk9'] = old_clk9
            continue
        # restore originals and try the next P
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
        for l in range(3):
            for it in old_arr_items[l]:
                NEW[l].append(it)
                pool[l].append(it)
            for it in old_clk9_items[l]:
                NEW[l].append(it)
                pool[l].append(it)
        JOURNEYS['arr_clk'] = old_arr
        JOURNEYS['clk9'] = old_clk9
assert join2_done, 'JOIN 2 FAILED: stub ride not emitted'
v3_after = frag_report('+3V3D', (60, 95, -8, 28))
sizes_before = sorted((len(f['items']) for f in v3_before), reverse=True)
sizes_after = sorted((len(f['items']) for f in v3_after), reverse=True)
print(f'+3V3D fragment sizes before={sizes_before} after={sizes_after}',
      flush=True)

# ---------------------------------------------------------------- gate
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

# ---------------------------------------------------------------- save
RIP2_OUT = {net: [list(x) for x in lst] for net, lst in B['rip2'].items()}
for net, lst in RIP_ADD.items():
    RIP2_OUT.setdefault(net, []).extend(lst)
out = dict(journeys=JOURNEYS, fixed=B['fixed'], rip2=RIP2_OUT,
           extra=B['extra'], arrivals=B['arrivals'],
           clk_via=(70.2, 1.8), exit_via=(69.075, 2.8), u9_shift=1.25)
json.dump(out, open('scratch/work/av/build_av1.json', 'w'), indent=1)
pool_out = {str(l): [[it[0], it[1], list(it[2]), it[3]] for it in pool[l]]
            for l in range(3)}
json.dump(pool_out, open('scratch/work/av/pool_av1.json', 'w'))
print('saved build_av1.json + pool_av1.json', flush=True)
print('t_av4 DONE', flush=True)

import wx
_app = wx.App(False)
import sys, json
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'av37'}
src = open('scratch/work/au/t_au97_phase2y.py').read()
exec(src.split("# 1. RBIAS tail re-lay")[0], g)
pool = g['pool']
NEW = g['NEW']
JOURNEYS = g['JOURNEYS']
NET_HW = g['NET_HW']
make_astar = g['make_astar']
journey_items_dense = g['journey_items_dense']
try_emit = g['try_emit']
fragments = g['fragments']
def frag_report(net, box):
    fr = fragments(net, box)
    print(f'fragments({net}) = {len(fr)} sizes '
          f'{sorted((len(f["items"]) for f in fr), reverse=True)}', flush=True)
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
              f'runs={[(r["layer"], len(r["pts"])) for r in J["runs"]]}', flush=True)
        if try_emit('detour_+3V3D_stub', J, '+3V3D', hw):
            return True
    return False
join2_done = stub_ride('unmodified clk9')
if not join2_done:
    print('=== phase B: re-plan arr_clk tail ===', flush=True)
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
            print(f'  extension to {P}: NONE', flush=True)
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
print('JOIN2', 'DONE' if join2_done else 'FAILED', flush=True)
if join2_done:
    frag_report('+3V3D', (60, 95, -8, 28))

"""t_au94: phase 2w - A* for the last two joins. Rebuild au93.
1. XO bridge: multi-layer A* (71.875,19.625) -> (68.875,20.375),
   box (67.5,73.5,17.5,22.5) step 0.025 hw 0.10.
2. +3V3D join: A* stub term (72.375,21.125) -> (70.45,22.8),
   box (69.0,73.2,20.3,23.6) step 0.025 hw 0.15, F-only then free.
Winners densified, exact-gated, emitted. Saves build_au94.json."""
import wx
_app = wx.App(False)
import sys, json, math
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'p2w'}
src71 = open('scratch/work/au/t_au71_phase2b.py').read()
exec(src71.split("NEW = {")[0], g)
pool = g['pool']
C = g['C']
journey_items_dense = g['journey_items_dense']
g['NEW'] = {0: [], 1: [], 2: []}
g['JOURNEYS'] = {}
exec(src71[src71.index("def item_margin"):src71.index("def fragments")],
     g)
exec(src71[src71.index("def fragments"):src71.index("def detour")]
     .replace("< 0.02", "< 0.04"), g)
NEW = g['NEW']
JOURNEYS = g['JOURNEYS']
item_margin = g['item_margin']
make_astar = g['make_astar']
fragments = g['fragments']
import t_ai_lib as L


def add_new(name, J, net, hw=0.10):
    JOURNEYS[name] = J
    for l, its in journey_items_dense(J, net, hw=hw).items():
        NEW[l] += its
        pool[l] += its


B = json.load(open('scratch/work/au/build_au93.json'))
RIP2 = {net: list(lst) for net, lst in B['rip2'].items()}
for net, lst in RIP2.items():
    for itj in lst:
        it = (itj[0], itj[1], tuple(itj[2]), itj[3])
        for l in range(3):
            if it in pool[l]:
                pool[l].remove(it)
EXTRA = []
for e in B['extra']:
    l = e[0]
    it = (e[1], e[2], tuple(e[3]), e[4])
    NEW[l].append(it)
    pool[l].append(it)
    EXTRA.append(e)
NET_HW = {'bheal': ('I2C_SCL', 0.10), 'clk9': ('CAP_CLK', 0.10),
          'clk_exit_frun': ('CAP_CLK', 0.10),
          'data_entry': ('CAP_DATA', 0.10),
          'data_tail': ('CAP_DATA', 0.10),
          'arr_data': ('CAP_DATA', 0.10), 'arr_clk': ('CAP_CLK', 0.10),
          'v3a_heal1': ('+3V3A', 0.10), 'v3a_heal2': ('+3V3A', 0.10),
          'detour_PG_3V3_1': ('PG_3V3', 0.125),
          'detour_PG_3V3_2': ('PG_3V3', 0.125),
          'detour_+3V3D_1': ('+3V3D', 0.15),
          'detour_+3V3D_2': ('+3V3D', 0.15),
          'detour_+3V3D_3': ('+3V3D', 0.15),
          'detour_+3V3D_4': ('+3V3D', 0.15),
          'detour_+3V3D_5': ('+3V3D', 0.15),
          'detour_+3V3D_L0': ('+3V3D', 0.15),
          'detour_+3V3D_L1': ('+3V3D', 0.15),
          'detour_+3V3D_L2': ('+3V3D', 0.15),
          'detour_+3V3D_L3': ('+3V3D', 0.15),
          'detour_XO_1': ('XO', 0.10), 'detour_XO_2': ('XO', 0.10),
          'dir_dive': ('ULPI_DIR', 0.10),
          'hop': ('I2C_SDA', 0.125),
          'scl_ffan': ('I2C_SCL', 0.10)}
for name, J in B['journeys'].items():
    net, hw = NET_HW[name]
    add_new(name, J, net, hw)
print('model rebuilt from au93', flush=True)


def gate_pairs(J, net, hw, top=3):
    its = journey_items_dense(J, net, hw=hw)
    out = []
    for l in range(3):
        for it in its[l]:
            for o in pool[l]:
                if o[1] == net:
                    continue
                m = item_margin(l, it, [o])
                if m < 0.05:
                    out.append((m, l, it, o))
    out.sort(key=lambda t: t[0])
    return out[:top]


# 1. XO bridge A*
astarXO = make_astar((67.5, 73.5, 17.5, 22.5), 0.025)
for starts, goal in (
        (((0, 1, 2), 71.875, 19.625), (1, 68.875, 20.375)),
        (((2,), 71.875, 19.625), (1, 68.875, 20.375)),
        (((0, 1, 2), 71.875, 19.625), (2, 72.625, 20.375))):
    J = astarXO('XO', starts, goal, hw=0.10)
    print(f'XO A* {starts[0]}->{goal}: '
          f'{"FOUND vias=%s" % (J["vias"],) if J else "NONE"}',
          flush=True)
    if J:
        J['runs'][0]['pts'][0] = [starts[1], starts[2]]
        J['runs'][-1]['pts'][-1] = [goal[1], goal[2]]
        p = gate_pairs(J, 'XO', 0.10)
        w = p[0][0] if p else 9.9
        print(f'   densified gate worst {w:+.3f}', flush=True)
        if w >= -0.001:
            add_new('xo_bridge', J, 'XO', 0.10)
            NET_HW['xo_bridge'] = ('XO', 0.10)
            print('xo_bridge EMITTED', flush=True)
            break
        else:
            for (m, l, it, o) in p:
                print(f'   {m:+.3f} L{l} {L.fmt_it(it)} vs '
                      f'{L.fmt_it(o)}', flush=True)
fr = fragments('XO', (60.0, 90.0, 4.0, 33.0))
print(f'XO fragments now: {len(fr)}', flush=True)
# 2. +3V3D join A*
astar3 = make_astar((69.0, 73.2, 20.3, 23.6), 0.025)
for lock, hw in (((True, False, False), 0.15),
                 (None, 0.15),
                 (None, 0.125)):
    J = astar3('+3V3D', ((0, 1, 2), 72.375, 21.125), (0, 70.45, 22.8),
               hw=hw, layer_lock=lock)
    print(f'+3V3D A* lock {lock} hw {hw}: '
          f'{"FOUND vias=%s" % (J["vias"],) if J else "NONE"}',
          flush=True)
    if J:
        J['runs'][0]['pts'][0] = [72.375, 21.125]
        J['runs'][-1]['pts'][-1] = [70.45, 22.8]
        p = gate_pairs(J, '+3V3D', hw)
        w = p[0][0] if p else 9.9
        print(f'   densified gate worst {w:+.3f}', flush=True)
        if w >= -0.001:
            add_new('detour_+3V3D_stub', J, '+3V3D', hw)
            NET_HW['detour_+3V3D_stub'] = ('+3V3D', hw)
            print('detour_+3V3D_stub EMITTED', flush=True)
            break
        else:
            for (m, l, it, o) in p:
                print(f'   {m:+.3f} L{l} {L.fmt_it(it)} vs '
                      f'{L.fmt_it(o)}', flush=True)
fr = fragments('+3V3D', (50.0, 86.0, -2.0, 32.0))
print(f'+3V3D fragments now: {len(fr)}', flush=True)


def save(path):
    json.dump(dict(
        journeys=JOURNEYS,
        fixed={str(l): [[it[0], it[1], list(it[2]), it[3]]
                         for it in g['FIXED'][l]] for l in range(3)},
        rip2=RIP2, extra=EXTRA, arrivals=B['arrivals'],
        clk_via=(70.2, 1.8), exit_via=(69.075, 2.8), u9_shift=1.25),
        open(path, 'w'))
    print(f'saved {path}', flush=True)


bad = 0
for l in range(3):
    for nit in NEW[l]:
        m = item_margin(l, nit, pool[l])
        if m < -0.001:
            bad += 1
            if bad <= 15:
                print(f'GATE FAIL L{l} {m:+.3f} {L.fmt_it(nit)}',
                      flush=True)
print(f'full gate: {bad} failures', flush=True)
save('scratch/work/au/build_au94.json')
print('done', flush=True)

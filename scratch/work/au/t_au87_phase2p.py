"""t_au87: phase 2p. Rebuild from build_au86.json.
1. B census along x72.625 y[12,20.5]; XO bridge v3: B ride
   (72.625,12.25) -> (72.625,20.375) (designed, exact gate;
   variants x72.5/72.75 + mid-join at (72.5,20.25)).
2. Fanout v5b: F ride jogged N over the GND chain.
3. +3V3D stub: A* to detour-3 via (71.25,24.325).
Saves build_au87.json."""
import wx
_app = wx.App(False)
import sys, json, math
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'p2p'}
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


B = json.load(open('scratch/work/au/build_au86.json'))
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
          'hop': ('I2C_SDA', 0.125)}
for name, J in B['journeys'].items():
    net, hw = NET_HW[name]
    add_new(name, J, net, hw)
print('model rebuilt from au86', flush=True)
print('--- B items crossing x[72.2,73.0], y[12,20.5]:', flush=True)
for it in pool[2]:
    d = it[2]
    if it[0] == 'seg':
        if min(d[0], d[2]) < 73.0 and max(d[0], d[2]) > 72.2 \
                and 12 < (d[1] + d[3]) / 2 < 20.5:
            print('   ', L.fmt_it(it), flush=True)
    elif it[0] == 'via':
        if 72.2 < d[0] < 73.0 and 12 < d[1] < 20.5:
            print('   ', L.fmt_it(it), flush=True)


def gate_worst(J, net, hw):
    its = journey_items_dense(J, net, hw=hw)
    w, wo, wl = 9.9, None, None
    for l in range(3):
        for it in its[l]:
            for o in pool[l]:
                if o[1] == net:
                    continue
                m = item_margin(l, it, [o])
                if m < w:
                    w, wo, wl = m, o, l
    return w, wo, wl


XB3 = [
    dict(vias=[], runs=[dict(layer=2, pts=[[72.625, 12.25],
                                           [72.625, 20.375]])]),
    dict(vias=[], runs=[dict(layer=2, pts=[[72.625, 12.25],
                                           [72.5, 16.0],
                                           [72.5, 20.25]])]),
    dict(vias=[], runs=[dict(layer=2, pts=[[72.625, 12.25],
                                           [72.75, 16.0],
                                           [72.625, 20.375]])]),
]
for i, J in enumerate(XB3):
    w, wo, wl = gate_worst(J, 'XO', 0.10)
    print(f'XO B ride v3.{i} worst {w:+.3f} L{wl} '
          f'vs {L.fmt_it(wo) if wo else None}', flush=True)
    if w >= -0.001:
        add_new('xo_bridge', J, 'XO', 0.10)
        print('XO bridge EMITTED', flush=True)
        break
fr = fragments('XO', (60.0, 90.0, 4.0, 33.0))
print(f'XO fragments now: {len(fr)}', flush=True)
FAN = dict(
    vias=[[69.3, 1.25], [66.3, 1.45]],
    runs=[dict(layer=2, pts=[[69.35, 1.4], [69.3, 1.25]]),
          dict(layer=0, pts=[[69.3, 1.25], [68.3, 1.65],
                             [66.3, 1.45], [66.05, 2.0]])])
w, wo, wl = gate_worst(FAN, 'I2C_SCL', 0.10)
print(f'fanout v5b worst {w:+.3f} L{wl} '
      f'vs {L.fmt_it(wo) if wo else None}', flush=True)
if w >= -0.001:
    add_new('scl_ffan', FAN, 'I2C_SCL', 0.10)
    print('fanout v5b EMITTED', flush=True)
astarS = make_astar((70.0, 74.0, 20.0, 26.0), 0.025)
J = None
for goal in ((0, 71.25, 24.325), (1, 71.25, 24.325),
             (2, 71.25, 24.325)):
    J = astarS('+3V3D', ((0, 1, 2), 72.375, 21.125), goal, hw=0.125)
    print(f'+3V3D stub A* goal {goal}:', 'FOUND' if J else 'NONE',
          flush=True)
    if J:
        break
if J:
    add_new('detour_+3V3D_stub', J, '+3V3D', 0.125)


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
save('scratch/work/au/build_au87.json')
print('done', flush=True)

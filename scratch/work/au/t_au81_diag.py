"""t_au81: diagnostics in the au80 model state.
(a) XO B items near (71.875,19.625); XO In2 items near
    (68.875,20.375).
(b) B items x[65.5,70] y[0.5,2.5] (fanout B-ride fences).
(c) F/In2/B items x[68.5,71.5] y[0,2.5] (heal2 dive corridor).
(d) +3V3D detours with box y2."""
import wx
_app = wx.App(False)
import sys, json, math
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'p2k'}
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


B = json.load(open('scratch/work/au/build_au80.json'))
RIP2 = {net: list(lst) for net, lst in B['rip2'].items()}
for net, lst in RIP2.items():
    for itj in lst:
        it = (itj[0], itj[1], tuple(itj[2]), itj[3])
        for l in range(3):
            if it in pool[l]:
                pool[l].remove(it)
for e in B['extra']:
    l = e[0]
    it = (e[1], e[2], tuple(e[3]), e[4])
    NEW[l].append(it)
    pool[l].append(it)
NET_HW = {'bheal': ('I2C_SCL', 0.10), 'clk9': ('CAP_CLK', 0.10),
          'clk_exit_frun': ('CAP_CLK', 0.10),
          'data_entry': ('CAP_DATA', 0.10),
          'data_tail': ('CAP_DATA', 0.10),
          'arr_data': ('CAP_DATA', 0.10), 'arr_clk': ('CAP_CLK', 0.10),
          'v3a_heal1': ('+3V3A', 0.10),
          'detour_PG_3V3_1': ('PG_3V3', 0.125),
          'detour_PG_3V3_2': ('PG_3V3', 0.125),
          'detour_+3V3D_1': ('+3V3D', 0.15),
          'detour_+3V3D_2': ('+3V3D', 0.15),
          'detour_+3V3D_3': ('+3V3D', 0.15),
          'detour_XO_1': ('XO', 0.10), 'detour_XO_2': ('XO', 0.10),
          'hop': ('I2C_SDA', 0.125)}
for name, J in B['journeys'].items():
    net, hw = NET_HW[name]
    add_new(name, J, net, hw)
print('model rebuilt from au80', flush=True)
print('--- (a) XO B items near (71.875,19.625):', flush=True)
for it in pool[2]:
    if it[1] == 'XO' and math.hypot(C(it)[0] - 71.875,
                                    C(it)[1] - 19.625) < 3.0:
        print('   ', L.fmt_it(it), flush=True)
print('--- (a2) XO In2 items near (68.875,20.375):', flush=True)
for it in pool[1]:
    if it[1] == 'XO' and math.hypot(C(it)[0] - 68.875,
                                    C(it)[1] - 20.375) < 3.0:
        print('   ', L.fmt_it(it), flush=True)
print('--- (b) B items x[65.5,70] y[0.5,2.5]:', flush=True)
for it in pool[2]:
    cx, cy = C(it)
    if 65.5 < cx < 70 and 0.5 < cy < 2.5:
        print('   ', L.fmt_it(it), flush=True)
print('--- (c) items x[68.5,71.5] y[0,2.5] all layers:', flush=True)
for l in range(3):
    for it in pool[l]:
        cx, cy = C(it)
        if 68.5 < cx < 71.5 and 0 < cy < 2.5:
            print(f'    L{l}', L.fmt_it(it), flush=True)


def detour2(net, box, hw, layer_lock=None, step=0.05, maxpairs=30):
    astar = make_astar(box, step)
    bx0, bx1, by0, by1 = box
    n = 0
    while True:
        fr = fragments(net, box)
        if len(fr) <= 1:
            print(f'  {net}: connected', flush=True)
            return True
        pairs = []
        for i in range(len(fr)):
            for j in range(i + 1, len(fr)):
                for (l1, p1) in fr[i]['terms']:
                    for (l2, p2) in fr[j]['terms']:
                        if not (bx0 + 0.1 < p1[0] < bx1 - 0.1
                                and by0 + 0.1 < p1[1] < by1 - 0.1
                                and bx0 + 0.1 < p2[0] < bx1 - 0.1
                                and by0 + 0.1 < p2[1] < by1 - 0.1):
                            continue
                        pairs.append((math.hypot(p1[0] - p2[0],
                                                  p1[1] - p2[1]),
                                      (l1, p1), (l2, p2)))
        pairs.sort()
        done = False
        for (_, (l1, p1), (l2, p2)) in pairs[:maxpairs]:
            starts = (l1,) if layer_lock else (0, 1, 2)
            J = astar(net, (starts, p1[0], p1[1]), (l2, p2[0], p2[1]),
                      hw=hw, layer_lock=layer_lock)
            if J is not None:
                J['runs'][0]['pts'][0] = [p1[0], p1[1]]
                J['runs'][-1]['pts'][-1] = [p2[0], p2[1]]
                n += 1
                add_new(f'detour_{net}_{n}', J, net, hw)
                print(f'  {net}: detour {n} {p1} -> {p2} '
                      f'vias={J["vias"]}', flush=True)
                done = True
                break
        if not done:
            print(f'  {net}: NO detour for {len(fr)} fragments',
                  flush=True)
            return False
        if n > 14:
            return False


print('+3V3D detours (box y2):', flush=True)
detour2('+3V3D', (62.0, 80.0, 2.0, 29.0), 0.15)
json.dump(dict(
    journeys=JOURNEYS,
    fixed={str(l): [[it[0], it[1], list(it[2]), it[3]]
                     for it in g['FIXED'][l]] for l in range(3)},
    rip2=RIP2, extra=B['extra'], arrivals=B['arrivals'],
    clk_via=(70.2, 1.8), exit_via=(69.075, 2.8), u9_shift=1.25),
    open('scratch/work/au/build_au81.json', 'w'))
print('saved build_au81.json', flush=True)
print('done', flush=True)

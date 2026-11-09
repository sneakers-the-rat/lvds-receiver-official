"""t_au80: phase 2j. Rebuild from build_au79.json (rip applier
fixed: remove from ALL layers).
1. SCL fanout v4: B ride y~1.35 + designed rise via + F stub.
2. heal2 v4: two-stage B crossing of stub+hop.
3. Detours v4: boxes extended (+3V3D y4, XO y33).
Saves build_au80.json."""
import wx
_app = wx.App(False)
import sys, json, math
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'p2j'}
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


B = json.load(open('scratch/work/au/build_au79.json'))
RIP2 = {net: list(lst) for net, lst in B['rip2'].items()}
for net, lst in RIP2.items():
    n = 0
    for itj in lst:
        it = (itj[0], itj[1], tuple(itj[2]), itj[3])
        for l in range(3):
            if it in pool[l]:
                pool[l].remove(it)
                n += 1
    print(f'rip2 {net}: removed {n} layer-copies / {len(lst)} items',
          flush=True)
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
print('model rebuilt from au79', flush=True)


def gate_worst(J, net, hw):
    its = journey_items_dense(J, net, hw=hw)
    w, wo = 9.9, None
    for l in range(3):
        for it in its[l]:
            for o in pool[l]:
                if o[1] == net:
                    continue
                m = item_margin(l, it, [o])
                if m < w:
                    w, wo = m, o
    return w, wo


# 1. fanout v4
astarB = make_astar((64.0, 72.0, 0.0, 4.0), 0.025)
FAN = None
for goal in ((2, 66.3, 1.35), (2, 66.35, 1.30), (2, 66.25, 1.45)):
    J = astarB('I2C_SCL', ((2,), 69.35, 1.40), goal, hw=0.10,
               layer_lock=(False, False, True))
    print(f'fanout B ride goal {goal}:', 'FOUND' if J else 'NONE',
          flush=True)
    if J:
        gx, gy = goal[1], goal[2]
        J2 = dict(vias=J['vias'] + [[gx, gy]],
                  runs=J['runs'] + [dict(layer=0, pts=[[gx, gy],
                                                      [66.05, 2.0]])])
        w, wo = gate_worst(J2, 'I2C_SCL', 0.10)
        print(f'fanout v4 (ride+via+stub) worst {w:+.3f} '
              f'vs {L.fmt_it(wo) if wo else None}', flush=True)
        if w >= -0.001:
            FAN = J2
            break
if FAN:
    add_new('scl_ffan', FAN, 'I2C_SCL', 0.10)
    print('fanout v4 EMITTED', flush=True)
# 2. heal2 v4 two-stage
astarP = make_astar((66.0, 72.5, -0.5, 6.0), 0.025)
J1 = astarP('+3V3A', ((0, 1, 2), 71.375, 0.875), (2, 69.5, 1.5),
            hw=0.10)
print('heal2 stage1:', 'FOUND' if J1 else 'NONE', flush=True)
if J1:
    add_new('v3a_heal2a', J1, '+3V3A', 0.10)
    J2 = None
    for goal in ((0, 69.125, 4.375), (0, 68.6, 3.25)):
        J2 = astarP('+3V3A', ((2,), 69.5, 1.5), goal, hw=0.10)
        print(f'heal2 stage2 goal {goal}:', 'FOUND' if J2 else 'NONE',
              flush=True)
        if J2:
            break
    if J2:
        add_new('v3a_heal2b', J2, '+3V3A', 0.10)
        print('heal2 v4 EMITTED (two journeys)', flush=True)


def save(path):
    json.dump(dict(
        journeys=JOURNEYS,
        fixed={str(l): [[it[0], it[1], list(it[2]), it[3]]
                         for it in g['FIXED'][l]] for l in range(3)},
        rip2=RIP2, extra=EXTRA, arrivals=B['arrivals'],
        clk_via=(70.2, 1.8), exit_via=(69.075, 2.8), u9_shift=1.25),
        open(path, 'w'))
    print(f'saved {path}', flush=True)


save('scratch/work/au/build_au80_stageA.json')


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


for net, box in (('+3V3D', (60.0, 80.0, 4.0, 30.0)),
                 ('XO', (60.0, 90.0, 4.0, 33.0))):
    fr = fragments(net, box)
    print(f'{net}: {len(fr)} fragments', flush=True)
    for f in fr:
        print(f"   size {len(f['items'])} terms {f['terms'][:6]}",
              flush=True)
print('+3V3D detours v4:', flush=True)
detour2('+3V3D', (62.0, 80.0, 4.0, 29.0), 0.15)
print('XO detours v4:', flush=True)
detour2('XO', (62.0, 90.0, 6.0, 33.0), 0.10)
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
save('scratch/work/au/build_au80.json')
print('done', flush=True)

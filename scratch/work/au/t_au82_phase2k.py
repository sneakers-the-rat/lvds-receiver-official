"""t_au82: phase 2k. Rebuild from build_au80.json.
1. XO bridge (designed): In2 (69.875,19.375) -> via (70.9,19.5)
   -> B (71.875,19.625). Exact gate, variants.
2. SCL fanout v5 (designed): B stub, via (69.3,1.25), F ride
   over the PG vertical + HV band, via (66.3,1.45), F stub into
   the SCL pad. Exact gate, variant.
3. heal2: big-box A*; designed dive (70.9,1.0) + staged A*.
4. +3V3D detours box y2.
Saves build_au82.json."""
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
print('model rebuilt from au80', flush=True)


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


# 1. XO bridge
for (vx, vy) in ((70.9, 19.5), (70.8, 19.45), (71.0, 19.55)):
    J = dict(vias=[[vx, vy]],
             runs=[dict(layer=1, pts=[[69.875, 19.375], [vx, vy]]),
                   dict(layer=2, pts=[[vx, vy], [71.875, 19.625]])])
    w, wo = gate_worst(J, 'XO', 0.10)
    print(f'XO bridge via ({vx},{vy}) worst {w:+.3f} '
          f'vs {L.fmt_it(wo) if wo else None}', flush=True)
    if w >= -0.001:
        add_new('xo_bridge', J, 'XO', 0.10)
        print('XO bridge EMITTED', flush=True)
        break
fr = fragments('XO', (60.0, 90.0, 4.0, 33.0))
print(f'XO fragments now: {len(fr)}', flush=True)
# 2. fanout v5
FANV = [
    dict(vias=[[69.3, 1.25], [66.3, 1.45]],
         runs=[dict(layer=2, pts=[[69.35, 1.4], [69.3, 1.25]]),
               dict(layer=0, pts=[[69.3, 1.25], [66.3, 1.45],
                                  [66.05, 2.0]])]),
    dict(vias=[[69.35, 1.2], [66.35, 1.5]],
         runs=[dict(layer=2, pts=[[69.35, 1.4], [69.35, 1.2]]),
               dict(layer=0, pts=[[69.35, 1.2], [66.35, 1.5],
                                  [66.05, 2.0]])]),
]
for i, J in enumerate(FANV):
    w, wo = gate_worst(J, 'I2C_SCL', 0.10)
    print(f'fanout v5.{i} worst {w:+.3f} '
          f'vs {L.fmt_it(wo) if wo else None}', flush=True)
    if w >= -0.001:
        add_new('scl_ffan', J, 'I2C_SCL', 0.10)
        print('fanout v5 EMITTED', flush=True)
        break
# 3. heal2
astarBig = make_astar((66.0, 80.0, -6.0, 16.0), 0.05)
J = astarBig('+3V3A', ((0, 1, 2), 71.375, 0.875), (0, 69.125, 4.375),
             hw=0.10)
print('heal2 big-box:', 'FOUND' if J else 'NONE', flush=True)
if J:
    add_new('v3a_heal2', J, '+3V3A', 0.10)
else:
    JD = dict(vias=[[70.9, 1.0]],
              runs=[dict(layer=0, pts=[[71.375, 0.875], [70.9, 1.0]])])
    w, wo = gate_worst(JD, '+3V3A', 0.10)
    print(f'heal2 dive worst {w:+.3f} '
          f'vs {L.fmt_it(wo) if wo else None}', flush=True)
    if w >= -0.001:
        add_new('v3a_heal2_dive', JD, '+3V3A', 0.10)
        astarB2 = make_astar((68.0, 72.0, 0.0, 3.0), 0.025)
        J = astarB2('+3V3A', ((2,), 70.9, 1.0), (2, 69.5, 1.5),
                    hw=0.10, layer_lock=(False, False, True))
        print('heal2 B ride:', 'FOUND' if J else 'NONE', flush=True)
        if J:
            add_new('v3a_heal2_bride', J, '+3V3A', 0.10)
            astarP = make_astar((66.0, 72.5, -0.5, 6.0), 0.025)
            J = astarP('+3V3A', ((2,), 69.5, 1.5), (0, 69.125, 4.375),
                       hw=0.10)
            print('heal2 stage3:', 'FOUND' if J else 'NONE',
                  flush=True)
            if J:
                add_new('v3a_heal2_s3', J, '+3V3A', 0.10)


def save(path):
    json.dump(dict(
        journeys=JOURNEYS,
        fixed={str(l): [[it[0], it[1], list(it[2]), it[3]]
                         for it in g['FIXED'][l]] for l in range(3)},
        rip2=RIP2, extra=EXTRA, arrivals=B['arrivals'],
        clk_via=(70.2, 1.8), exit_via=(69.075, 2.8), u9_shift=1.25),
        open(path, 'w'))
    print(f'saved {path}', flush=True)


save('scratch/work/au/build_au82_stageA.json')


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
save('scratch/work/au/build_au82.json')
print('done', flush=True)

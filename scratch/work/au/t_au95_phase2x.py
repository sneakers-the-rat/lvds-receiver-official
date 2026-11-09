"""t_au95: phase 2x - all-pairs detour loops. Rebuild from au93
(au94's xo_bridge was a frag-96 self-join; evidence only).
XO: box (64,78,8,26) hw 0.10 step 0.025, pairs by distance.
+3V3D: box (66,79,16,28) hw 0.15/0.125 step 0.025.
Saves build_au95.json."""
import wx
_app = wx.App(False)
import sys, json, math
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'p2x'}
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


def gate_worst(J, net, hw):
    its = journey_items_dense(J, net, hw=hw)
    worst = (9.9, None, None)
    for l in range(3):
        for it in its[l]:
            for o in pool[l]:
                if o[1] == net:
                    continue
                m = item_margin(l, it, [o])
                if m < worst[0]:
                    worst = (m, o, l)
    return worst


def all_pairs_detour(net, box, hw, tag, step=0.025, maxpairs=14):
    astar = make_astar(box, step)
    bx0, bx1, by0, by1 = box
    fr = fragments(net, box)
    print(f'{net}: {len(fr)} fragments in box', flush=True)
    if len(fr) <= 1:
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
    print(f'{net}: {len(pairs)} terminal pairs', flush=True)
    for k, (_, (l1, p1), (l2, p2)) in enumerate(pairs[:maxpairs]):
        J = astar(net, ((0, 1, 2), p1[0], p1[1]), (l2, p2[0], p2[1]),
                  hw=hw)
        if J is None:
            print(f'  pair {k} {p1}->{p2}: NONE', flush=True)
            continue
        J['runs'][0]['pts'][0] = [p1[0], p1[1]]
        J['runs'][-1]['pts'][-1] = [p2[0], p2[1]]
        w, wo, wl = gate_worst(J, net, hw)
        print(f'  pair {k} {p1}->{p2}: FOUND gate {w:+.3f}',
              flush=True)
        if w >= -0.001:
            name = f'{tag}_{k}'
            add_new(name, J, net, hw)
            NET_HW[name] = (net, hw)
            print(f'  {name} EMITTED', flush=True)
            return True
    return False


ok1 = all_pairs_detour('XO', (64.0, 78.0, 8.0, 26.0), 0.10,
                       'xo_bridge')
fr = fragments('XO', (60.0, 90.0, 4.0, 33.0))
print(f'XO fragments now: {len(fr)}', flush=True)
ok2 = all_pairs_detour('+3V3D', (66.0, 79.0, 16.0, 28.0), 0.15,
                       'detour_+3V3D_stub')
if not ok2:
    ok2 = all_pairs_detour('+3V3D', (66.0, 79.0, 16.0, 28.0), 0.125,
                           'detour_+3V3D_stub')
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
save('scratch/work/au/build_au95.json')
print('done', flush=True)

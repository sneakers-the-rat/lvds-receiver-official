"""t_au78: phase 2h. Rebuild model from build_au77.json manifest;
hop re-run with exit via fenced; +3V3D/XO detours v2 (wider,
multi-layer); SCL fanout v3 (GND-chain rip variant); heal2;
full gate; fragments2 (pad-gap fixed); pad dumps. Saves
build_au78.json (complete: journeys + fixed + rip2 + extra)."""
import wx
_app = wx.App(False)
import sys, json, math
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'p2h'}
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


def add_new(name, J, net, hw=0.10):
    JOURNEYS[name] = J
    for l, its in journey_items_dense(J, net, hw=hw).items():
        NEW[l] += its
        pool[l] += its
item_margin = g['item_margin']
make_astar = g['make_astar']
fragments = g['fragments']
import t_ai_lib as L

B77 = json.load(open('scratch/work/au/build_au77.json'))
# apply au77 rip2
for net, lst in B77['rip2'].items():
    n = 0
    for itj in lst:
        it = (itj[0], itj[1], tuple(itj[2]), itj[3])
        for l in range(3):
            if it in pool[l]:
                pool[l].remove(it)
                n += 1
                break
    print(f'rip2 {net}: removed {n}/{len(lst)}', flush=True)
# extra items: exit via + B join (not journeys in au77 manifest)
EXTRA = []
for l in range(3):
    it = ('via', 'CAP_CLK', (69.075, 2.8, 0.25), 0.2)
    NEW[l].append(it)
    pool[l].append(it)
    EXTRA.append([l] + [it[0], it[1], list(it[2]), it[3]])
bj = ('seg', 'CAP_CLK', (69.075, 2.8, 69.55, 2.7, 0.10), 0.2)
NEW[2].append(bj)
pool[2].append(bj)
EXTRA.append([2] + [bj[0], bj[1], list(bj[2]), bj[3]])
# journeys from au77 (except hop - re-run below)
NET_HW = {'bheal': ('I2C_SCL', 0.10), 'clk9': ('CAP_CLK', 0.10),
          'clk_exit_frun': ('CAP_CLK', 0.10),
          'data_entry': ('CAP_DATA', 0.10),
          'data_tail': ('CAP_DATA', 0.10),
          'arr_data': ('CAP_DATA', 0.10), 'arr_clk': ('CAP_CLK', 0.10),
          'v3a_heal1': ('+3V3A', 0.10),
          'detour_PG_3V3_1': ('PG_3V3', 0.125),
          'detour_PG_3V3_2': ('PG_3V3', 0.125)}
for name, J in B77['journeys'].items():
    if name == 'hop':
        continue
    net, hw = NET_HW[name]
    add_new(name, J, net, hw)
print('model rebuilt from au77', flush=True)
# pad connection dumps
for net, (px, py) in (('CAP_DATA', (71.338, 2.25)),
                      ('CAP_CLK', (76.525, 25.385))):
    print(f'--- {net} items near ({px},{py}) on F:', flush=True)
    for it in pool[0]:
        if it[1] != net:
            continue
        d = it[2]
        if it[0] == 'seg' and (math.hypot(d[0] - px, d[1] - py) < 1.8
                               or math.hypot(d[2] - px, d[3] - py) < 1.8):
            print('   ', L.fmt_it(it), flush=True)
        if it[0] == 'pad' and math.hypot(d[0] - px, d[1] - py) < 0.01:
            print('    PAD', L.fmt_it(it), flush=True)
# hop re-run with exit via fenced
astarPocket = make_astar((66.0, 72.5, -0.5, 6.0), 0.025)
J = astarPocket('I2C_SDA', ((0, 1, 2), 69.05, 2.05), (1, 71.125, 1.875),
                hw=0.125)
print('hop re-run:', 'FOUND' if J else 'NONE', flush=True)
if J:
    add_new('hop', J, 'I2C_SDA', 0.125)
    its = journey_items_dense(J, 'I2C_SDA', hw=0.125)
    w = min(item_margin(l, it, pool[l]) for l in range(3)
            for it in its[l])
    print(f'hop worst margin {w:+.3f}', flush=True)


def save(path):
    json.dump(dict(
        journeys=JOURNEYS,
        fixed={str(l): [[it[0], it[1], list(it[2]), it[3]]
                         for it in g['FIXED'][l]] for l in range(3)},
        rip2=B77['rip2'], extra=EXTRA,
        arrivals=B77['arrivals'], clk_via=(70.2, 1.8),
        exit_via=(69.075, 2.8), u9_shift=1.25),
        open(path, 'w'))
    print(f'saved {path}', flush=True)


save('scratch/work/au/build_au78_stageA.json')


def detour2(net, box, hw, layer_lock=None, step=0.025, maxpairs=20):
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


for net, box in (('+3V3D', (60.0, 80.0, 10.0, 30.0)),
                 ('XO', (60.0, 90.0, 4.0, 28.0))):
    fr = fragments(net, box)
    print(f'{net}: {len(fr)} fragments in wide box', flush=True)
    for f in fr:
        print(f"   size {len(f['items'])} terms {f['terms'][:5]}",
              flush=True)
print('+3V3D detours v2:', flush=True)
detour2('+3V3D', (62.0, 79.0, 12.0, 29.0), 0.15)
print('XO detours v2:', flush=True)
detour2('XO', (62.0, 90.0, 6.0, 27.0), 0.10)
save('scratch/work/au/build_au78_stageB.json')
# SCL fanout v3
astarF = astarPocket
J = None
for goal in ((0, 66.025, 2.1), (0, 66.45, 2.1), (0, 66.3, 2.05)):
    J = astarF('I2C_SCL', ((0, 1, 2), 69.35, 1.40), goal, hw=0.10)
    print(f'fanout goal {goal}:', 'FOUND' if J else 'NONE', flush=True)
    if J:
        break
if J is None:
    # rip the GND F chain, retry, then heal GND
    chain = []
    for it in list(pool[0]):
        if it[0] == 'seg' and it[1] == 'GND':
            d = it[2]
            pts = {(round(d[0], 2), round(d[1], 2)),
                   (round(d[2], 2), round(d[3], 2))}
            if pts & {(68.9, 0.85), (68.2, 1.15), (67.85, 1.22)} \
                    and len(pts & {(68.9, 0.85), (68.2, 1.15),
                                   (67.85, 1.22)}) == 2:
                chain.append(it)
    print(f'GND chain segs found: {len(chain)}', flush=True)
    for it in chain:
        pool[0].remove(it)
    for goal in ((0, 66.025, 2.1), (0, 66.45, 2.1), (0, 66.3, 2.05)):
        J = astarF('I2C_SCL', ((0, 1, 2), 69.35, 1.40), goal, hw=0.10)
        print(f'fanout (chain ripped) goal {goal}:',
              'FOUND' if J else 'NONE', flush=True)
        if J:
            break
    if J:
        add_new('scl_ffan', J, 'I2C_SCL', 0.10)
        JG = astarF('GND', ((0,), 68.9, 0.85), (0, 67.85, 1.22),
                    hw=0.10)
        print('GND chain heal:', 'FOUND' if JG else 'NONE', flush=True)
        if JG:
            add_new('gnd_chain_heal', JG, 'GND', 0.10)
        B77['rip2']['GND'] = [[it[0], it[1], list(it[2]), it[3]]
                              for it in chain]
    else:
        for it in chain:
            pool[0].append(it)
        print('fanout still NONE - chain restored', flush=True)
else:
    add_new('scl_ffan', J, 'I2C_SCL', 0.10)
J = astarF('+3V3A', ((0, 1, 2), 71.375, 0.875), (0, 69.125, 4.375),
           hw=0.10)
print('heal2 v3:', 'FOUND' if J else 'NONE', flush=True)
if J:
    add_new('v3a_heal2', J, '+3V3A', 0.10)
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
save('scratch/work/au/build_au78.json')
print('done', flush=True)

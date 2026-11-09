"""t_au79: phase 2i. Rebuild from build_au78.json.
1. arr gate fix: iterative rip of XO/+3V3D/PG items conflicting
   with the placed arrivals (partner-attributed).
2. Census + detour retries for +3V3D (5) and XO (3).
3. U9 pad map + fanout variants (SDA stub rip; TMP ablation is
   diagnostic only).
4. heal2 hand-path exact gate + emit if clean.
Saves build_au79.json."""
import wx
_app = wx.App(False)
import sys, json, math
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'p2i'}
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


B = json.load(open('scratch/work/au/build_au78.json'))
RIP2 = {net: list(lst) for net, lst in B['rip2'].items()}
for net, lst in RIP2.items():
    n = 0
    for itj in lst:
        it = (itj[0], itj[1], tuple(itj[2]), itj[3])
        for l in range(3):
            if it in pool[l]:
                pool[l].remove(it)
                n += 1
                break
    print(f'rip2 {net}: removed {n}/{len(lst)}', flush=True)
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
print('model rebuilt from au78', flush=True)

# 1. iterative rip loop for the arrivals
ARR = {}
for nm in ('arr_data', 'arr_clk'):
    net, hw = NET_HW[nm]
    ARR[nm] = journey_items_dense(B['journeys'][nm], net, hw=hw)
for itn in range(20):
    worst = None
    for nm, its in ARR.items():
        for l in range(3):
            for it in its[l]:
                others = [o for o in pool[l] if o[1] in
                          ('XO', '+3V3D', 'PG_3V3') and o not in NEW[l]]
                for o in others:
                    m = item_margin(l, it, [o])
                    if m < -0.001 and (worst is None or m < worst[0]):
                        worst = (m, l, it, o)
    if worst is None:
        print(f'arrivals gate clean after {itn} extra rips', flush=True)
        break
    m, l, it, o = worst
    print(f'rip {m:+.3f} {L.fmt_it(o)} (vs {L.fmt_it(it)})', flush=True)
    pool[l].remove(o)
    RIP2.setdefault(o[1], []).append([o[0], o[1], list(o[2]), o[3]])


def save(path):
    json.dump(dict(
        journeys=JOURNEYS,
        fixed={str(l): [[it[0], it[1], list(it[2]), it[3]]
                         for it in g['FIXED'][l]] for l in range(3)},
        rip2=RIP2, extra=EXTRA, arrivals=B['arrivals'],
        clk_via=(70.2, 1.8), exit_via=(69.075, 2.8), u9_shift=1.25),
        open(path, 'w'))
    print(f'saved {path}', flush=True)


save('scratch/work/au/build_au79_stageA.json')


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


for net, box in (('+3V3D', (60.0, 80.0, 10.0, 30.0)),
                 ('XO', (60.0, 90.0, 4.0, 28.0))):
    fr = fragments(net, box)
    print(f'{net}: {len(fr)} fragments', flush=True)
    for f in fr:
        print(f"   size {len(f['items'])} terms {f['terms'][:6]}",
              flush=True)
print('+3V3D detours v3:', flush=True)
detour2('+3V3D', (62.0, 79.0, 12.0, 29.0), 0.15, step=0.025)
print('XO detours v3:', flush=True)
detour2('XO', (62.0, 90.0, 6.0, 27.0), 0.10, step=0.05)
save('scratch/work/au/build_au79_stageB.json')
# 3. U9 pad map
print('--- U9 pads (post-shift pool):', flush=True)
for it in pool[0]:
    if it[0] == 'pad' and 65.0 < it[2][0] < 69.5 and 0.5 < it[2][1] < 4.5:
        print('   ', L.fmt_it(it), flush=True)
print('--- U9-area F segs x[64,70] y[0,5]:', flush=True)
for it in pool[0]:
    if it[0] == 'seg' and 64 < C(it)[0] < 70 and 0 < C(it)[1] < 5:
        print('   ', L.fmt_it(it), flush=True)
# fanout variant: rip SDA F stub, retry, re-lay stub after
astarF = make_astar((66.0, 72.5, -0.5, 6.0), 0.025)
stub = [it for it in pool[0] if it[0] == 'seg' and it[1] == 'I2C_SDA'
        and abs(it[2][0] - 67.975) < 0.01 and abs(it[2][1] - 2.1) < 0.01]
print(f'SDA stub segs: {len(stub)}', flush=True)
for it in stub:
    pool[0].remove(it)
J = None
for goal in ((0, 66.025, 2.1), (0, 66.45, 2.1), (0, 66.3, 2.05)):
    J = astarF('I2C_SCL', ((0, 1, 2), 69.35, 1.40), goal, hw=0.10)
    print(f'fanout (no SDA stub) goal {goal}:',
          'FOUND' if J else 'NONE', flush=True)
    if J:
        break
if J:
    add_new('scl_ffan', J, 'I2C_SCL', 0.10)
    JS = astarF('I2C_SDA', ((0,), 67.975, 2.1), (0, 69.05, 2.05),
                hw=0.10)
    print('SDA stub re-lay:', 'FOUND' if JS else 'NONE', flush=True)
    if JS:
        add_new('sda_stub2', JS, 'I2C_SDA', 0.10)
    else:
        for it in stub:
            pool[0].append(it)
        print('stub restored verbatim (may conflict - gate will say)',
              flush=True)
else:
    for it in stub:
        pool[0].append(it)
    print('fanout still NONE - stub restored', flush=True)
# 4. heal2 hand path
HP = [(71.375, 0.875), (70.45, 1.2), (69.9, 1.0), (69.45, 0.8),
      (68.7, 0.95), (68.4, 2.2), (68.7, 3.6), (69.125, 4.375)]
HJ = dict(vias=[], runs=[dict(layer=0,
                              pts=[[x, y] for (x, y) in HP])])
its = journey_items_dense(HJ, '+3V3A', hw=0.10)
w = 9.9
wo = None
for it in its[0]:
    for o in pool[0]:
        if o[1] == '+3V3A':
            continue
        m = item_margin(0, it, [o])
        if m < w:
            w, wo = m, o
print(f'heal2 hand path worst {w:+.3f} vs {L.fmt_it(wo) if wo else None}',
      flush=True)
if w >= -0.001:
    add_new('v3a_heal2', HJ, '+3V3A', 0.10)
    print('heal2 hand path EMITTED', flush=True)
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
save('scratch/work/au/build_au79.json')
print('done', flush=True)

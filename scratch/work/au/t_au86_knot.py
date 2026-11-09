"""t_au86: the XO knot + DIR dive to B + stub detours.
1. Knot census: all nets x[69.5,73] y[17.5,21.5] on L1/L2;
   RBIAS/DP_PHY items anywhere near.
2. XO bridge family scan: via grid x[69.8,72.2] y[18.2,20.8]
   step 0.1; approaches sampled on frag-44 In2 staircase segs;
   joins sampled on frag-96 B staircase segs; exact gate
   (local pool, winner re-gated full).
3. DIR dive to B (designed) + fanout v5 emit.
4. +3V3D stub: A* local 0.025 hw0.125 to two main terms;
   designed v6b fallback.
Saves build_au86.json."""
import wx
_app = wx.App(False)
import sys, json, math
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'p2o'}
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


B = json.load(open('scratch/work/au/build_au83.json'))
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
          'hop': ('I2C_SDA', 0.125)}
for name, J in B['journeys'].items():
    net, hw = NET_HW[name]
    add_new(name, J, net, hw)
print('model rebuilt from au83', flush=True)
print('--- knot census L1/L2 x[69.5,73] y[17.5,21.5]:', flush=True)
for l in (1, 2):
    for it in pool[l]:
        cx, cy = C(it)
        if 69.5 < cx < 73 and 17.5 < cy < 21.5:
            print(f'    L{l}', L.fmt_it(it), flush=True)
print('--- RBIAS/DP_PHY items (any layer, x[68,76] y[14,24]):',
      flush=True)
for l in range(3):
    for it in pool[l]:
        if it[1] in ('RBIAS', 'DP_PHY') and 68 < C(it)[0] < 76 \
                and 14 < C(it)[1] < 24:
            print(f'    L{l}', L.fmt_it(it), flush=True)


def gate_worst(J, net, hw, poolx=None):
    its = journey_items_dense(J, net, hw=hw)
    w, wo = 9.9, None
    for l in range(3):
        src = pool[l] if poolx is None else poolx[l]
        for it in its[l]:
            for o in src:
                if o[1] == net:
                    continue
                m = item_margin(l, it, [o])
                if m < w:
                    w, wo = m, o
    return w, wo


# 2. XO bridge family scan
FR44 = [((70.375, 17.625), (70.375, 18.875)),
        ((70.375, 18.875), (70.125, 19.125)),
        ((70.125, 19.125), (69.875, 19.375)),
        ((69.875, 19.375), (69.625, 19.625)),
        ((69.625, 19.625), (69.375, 19.875)),
        ((69.375, 19.875), (69.125, 20.125)),
        ((69.125, 20.125), (68.875, 20.375))]
FR96 = [((71.875, 19.625), (72.125, 19.875)),
        ((72.125, 19.875), (72.375, 20.125)),
        ((72.375, 20.125), (72.625, 20.375)),
        ((72.625, 20.375), (72.625, 24.625))]


def samples(segs, step=0.3):
    out = []
    for (a, b) in segs:
        n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / step))
        for i in range(n + 1):
            t = i / n
            out.append((round(a[0] + t * (b[0] - a[0]), 3),
                        round(a[1] + t * (b[1] - a[1]), 3)))
    return out


AP = samples(FR44)
JN = samples(FR96)
local = {l: [o for o in pool[l]
             if 67.5 < C(o)[0] < 74.5 and 16.0 < C(o)[1] < 23.0]
         for l in range(3)}
best = []
vx = 69.8
while vx <= 72.21:
    vy = 18.2
    while vy <= 20.81:
        for a in AP[::3]:
            for jn in JN[::3]:
                J = dict(vias=[[round(vx, 2), round(vy, 2)]],
                         runs=[dict(layer=1, pts=[[a[0], a[1]],
                                                  [round(vx, 2),
                                                   round(vy, 2)]]),
                               dict(layer=2, pts=[[round(vx, 2),
                                                   round(vy, 2)],
                                                  [jn[0], jn[1]]])])
                w, _ = gate_worst(J, 'XO', 0.10, poolx=local)
                if w >= -0.001:
                    best.append((w, round(vx, 2), round(vy, 2), a, jn))
        vy += 0.2
    vx += 0.2
print(f'XO bridge scan: {len(best)} candidates >= -0.001 (local)',
      flush=True)
best.sort(reverse=True)
for cand in best[:5]:
    print('   ', cand, flush=True)
if best:
    w0, vx, vy, a, jn = best[0]
    J = dict(vias=[[vx, vy]],
             runs=[dict(layer=1, pts=[[a[0], a[1]], [vx, vy]]),
                   dict(layer=2, pts=[[vx, vy], [jn[0], jn[1]]])])
    w, wo = gate_worst(J, 'XO', 0.10)
    print(f'XO bridge winner full gate {w:+.3f} '
          f'vs {L.fmt_it(wo) if wo else None}', flush=True)
    if w >= -0.001:
        add_new('xo_bridge', J, 'XO', 0.10)
        print('XO bridge EMITTED', flush=True)
fr = fragments('XO', (60.0, 90.0, 4.0, 33.0))
print(f'XO fragments now: {len(fr)}', flush=True)
# 3. DIR dive to B + fanout v5
DIRSEG = None
for it in pool[1]:
    if it[0] == 'seg' and it[1] == 'ULPI_DIR' \
            and abs(it[2][0] - 59.875) < 0.01 \
            and abs(it[2][2] - 67.5) < 0.01:
        DIRSEG = it
print('DIR In2 seg found:', DIRSEG is not None, flush=True)
JD = dict(vias=[[64.0, 3.66], [67.5, 0.125]],
          runs=[dict(layer=1, pts=[[59.875, 7.875], [64.0, 3.66]]),
                dict(layer=2, pts=[[64.0, 3.66], [65.5, 0.9],
                                   [67.5, 0.125]])])
if DIRSEG is not None:
    pool[1].remove(DIRSEG)
    w, wo = gate_worst(JD, 'ULPI_DIR', 0.10)
    print(f'DIR dive-to-B worst {w:+.3f} '
          f'vs {L.fmt_it(wo) if wo else None}', flush=True)
    if w >= -0.001:
        add_new('dir_dive', JD, 'ULPI_DIR', 0.10)
        RIP2.setdefault('ULPI_DIR', []).append(
            [DIRSEG[0], DIRSEG[1], list(DIRSEG[2]), DIRSEG[3]])
        print('DIR dive EMITTED', flush=True)
        FAN = dict(
            vias=[[69.3, 1.25], [66.3, 1.45]],
            runs=[dict(layer=2, pts=[[69.35, 1.4], [69.3, 1.25]]),
                  dict(layer=0, pts=[[69.3, 1.25], [66.3, 1.45],
                                     [66.05, 2.0]])])
        w, wo = gate_worst(FAN, 'I2C_SCL', 0.10)
        print(f'fanout v5 (post DIR dive) worst {w:+.3f} '
              f'vs {L.fmt_it(wo) if wo else None}', flush=True)
        if w >= -0.001:
            add_new('scl_ffan', FAN, 'I2C_SCL', 0.10)
            print('fanout v5 EMITTED', flush=True)
    else:
        pool[1].append(DIRSEG)
        print('DIR dive rejected - seg restored', flush=True)
# 4. +3V3D stub
astarS = make_astar((71.0, 80.0, 19.0, 26.0), 0.025)
J = None
for goal in ((1, 74.625, 24.375), (1, 78.375, 20.125)):
    J = astarS('+3V3D', ((0, 1, 2), 72.375, 21.125), goal, hw=0.125)
    print(f'+3V3D stub A* goal {goal}:', 'FOUND' if J else 'NONE',
          flush=True)
    if J:
        break
if J:
    add_new('detour_+3V3D_stub', J, '+3V3D', 0.125)
else:
    JV = dict(vias=[[74.55, 21.4]],
              runs=[dict(layer=0, pts=[[72.375, 21.125],
                                       [74.55, 21.4]]),
                    dict(layer=1, pts=[[74.55, 21.4], [74.5, 23.0],
                                       [74.625, 24.375]])])
    w, wo = gate_worst(JV, '+3V3D', 0.15)
    print(f'+3V3D stub v6b worst {w:+.3f} '
          f'vs {L.fmt_it(wo) if wo else None}', flush=True)
    if w >= -0.001:
        add_new('detour_+3V3D_stub', JV, '+3V3D', 0.15)


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
save('scratch/work/au/build_au86.json')
print('done', flush=True)

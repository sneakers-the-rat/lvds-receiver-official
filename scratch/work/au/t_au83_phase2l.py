"""t_au83: phase 2l. Rebuild from build_au82.json.
1. XO bridge v2 (designed variants).
2. ULPI_DIR dive (designed): F to (64.0,3.66), via, In2 via
   (65.5,0.9) to (67.5,0.125), via. Rip the old F seg; then
   fanout v5 re-gate + emit.
3. +3V3D detours v5: per-pair LOCAL-box A*.
Saves build_au83.json."""
import wx
_app = wx.App(False)
import sys, json, math
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'p2l'}
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


B = json.load(open('scratch/work/au/build_au82.json'))
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
          'detour_XO_1': ('XO', 0.10), 'detour_XO_2': ('XO', 0.10),
          'hop': ('I2C_SDA', 0.125)}
for name, J in B['journeys'].items():
    net, hw = NET_HW[name]
    add_new(name, J, net, hw)
print('model rebuilt from au82', flush=True)


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


# 1. XO bridge v2
XB = [
    dict(vias=[[71.3, 18.3]],
         runs=[dict(layer=1, pts=[[70.375, 17.625], [71.3, 18.3]]),
               dict(layer=2, pts=[[71.3, 18.3], [72.05, 19.8]])]),
    dict(vias=[[69.9, 18.6]],
         runs=[dict(layer=1, pts=[[69.875, 19.375], [69.9, 18.6]]),
               dict(layer=2, pts=[[69.9, 18.6], [72.0, 19.75]])]),
    dict(vias=[[71.55, 18.15]],
         runs=[dict(layer=1, pts=[[70.375, 17.625], [71.55, 18.15]]),
               dict(layer=2, pts=[[71.55, 18.15], [72.05, 19.8]])]),
]
for i, J in enumerate(XB):
    w, wo, wl = gate_worst(J, 'XO', 0.10)
    print(f'XO bridge v2.{i} worst {w:+.3f} L{wl} '
          f'vs {L.fmt_it(wo) if wo else None}', flush=True)
    if w >= -0.001:
        add_new('xo_bridge', J, 'XO', 0.10)
        print('XO bridge EMITTED', flush=True)
        break
fr = fragments('XO', (60.0, 90.0, 4.0, 33.0))
print(f'XO fragments now: {len(fr)}', flush=True)
# 2. DIR dive + fanout v5
DIRSEG = None
for it in pool[0]:
    if it[0] == 'seg' and it[1] == 'ULPI_DIR' \
            and abs(it[2][0] - 59.875) < 0.01 \
            and abs(it[2][2] - 67.5) < 0.01:
        DIRSEG = it
print('DIR seg found:', DIRSEG is not None, flush=True)
JD = dict(vias=[[64.0, 3.66], [67.5, 0.125]],
          runs=[dict(layer=0, pts=[[59.875, 7.875], [64.0, 3.66]]),
                dict(layer=1, pts=[[64.0, 3.66], [65.5, 0.9],
                                   [67.5, 0.125]])])
if DIRSEG is not None:
    pool[0].remove(DIRSEG)
    w, wo, wl = gate_worst(JD, 'ULPI_DIR', 0.10)
    print(f'DIR dive worst {w:+.3f} L{wl} '
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
        w, wo, wl = gate_worst(FAN, 'I2C_SCL', 0.10)
        print(f'fanout v5 (post DIR dive) worst {w:+.3f} L{wl} '
              f'vs {L.fmt_it(wo) if wo else None}', flush=True)
        if w >= -0.001:
            add_new('scl_ffan', FAN, 'I2C_SCL', 0.10)
            print('fanout v5 EMITTED', flush=True)
    else:
        pool[0].append(DIRSEG)
        print('DIR dive rejected - seg restored', flush=True)


def save(path):
    json.dump(dict(
        journeys=JOURNEYS,
        fixed={str(l): [[it[0], it[1], list(it[2]), it[3]]
                         for it in g['FIXED'][l]] for l in range(3)},
        rip2=RIP2, extra=EXTRA, arrivals=B['arrivals'],
        clk_via=(70.2, 1.8), exit_via=(69.075, 2.8), u9_shift=1.25),
        open(path, 'w'))
    print(f'saved {path}', flush=True)


save('scratch/work/au/build_au83_stageA.json')
# 3. +3V3D detours v5: per-pair local boxes
BOXW = (50.0, 86.0, -2.0, 32.0)
for n in range(14):
    fr = fragments('+3V3D', BOXW)
    if len(fr) <= 1:
        print('+3V3D: connected', flush=True)
        break
    pairs = []
    for i in range(len(fr)):
        for j in range(i + 1, len(fr)):
            for (l1, p1) in fr[i]['terms']:
                for (l2, p2) in fr[j]['terms']:
                    pairs.append((math.hypot(p1[0] - p2[0],
                                              p1[1] - p2[1]),
                                  (l1, p1), (l2, p2)))
    pairs.sort()
    done = False
    for (_, (l1, p1), (l2, p2)) in pairs[:10]:
        lb = (min(p1[0], p2[0]) - 3.0, max(p1[0], p2[0]) + 3.0,
              min(p1[1], p2[1]) - 3.0, max(p1[1], p2[1]) + 3.0)
        astar = make_astar(lb, 0.05)
        J = astar('+3V3D', ((0, 1, 2), p1[0], p1[1]),
                  (l2, p2[0], p2[1]), hw=0.15)
        if J is not None:
            J['runs'][0]['pts'][0] = [p1[0], p1[1]]
            J['runs'][-1]['pts'][-1] = [p2[0], p2[1]]
            add_new(f'detour_+3V3D_L{n}', J, '+3V3D', 0.15)
            print(f'  +3V3D local detour {n} {p1} -> {p2} '
                  f'vias={J["vias"]}', flush=True)
            done = True
            break
    if not done:
        print(f'+3V3D: NO local detour for {len(fr)} fragments',
              flush=True)
        for f in fr:
            print(f"   size {len(f['items'])} terms {f['terms'][:6]}",
                  flush=True)
        break
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
save('scratch/work/au/build_au83.json')
print('done', flush=True)

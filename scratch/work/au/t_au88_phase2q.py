"""t_au88: phase 2q - final model push. Rebuild from au87.
1. Fanout: attribution + nudge scan (via2 x stub-end grid).
2. XO bridge v4: B ride W column x71.2 joining frag-96's B
   staircase at (71.95,19.7). Variants x71.0/71.35.
3. +3V3D stub detour v7: F ride to (73.9,23.3), via, In2 to
   (74.625,24.375); B-cross variant.
Saves build_au88.json."""
import wx
_app = wx.App(False)
import sys, json, math
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'p2q'}
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


B = json.load(open('scratch/work/au/build_au87.json'))
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
print('model rebuilt from au87', flush=True)


def gate_pairs(J, net, hw, top=5):
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
    return out


def gate_worst(J, net, hw):
    p = gate_pairs(J, net, hw, top=1)
    return (p[0][0], p[0][3], p[0][1]) if p else (9.9, None, None)


# 1. fanout attribution + nudge scan
FAN0 = dict(
    vias=[[69.3, 1.25], [66.3, 1.45]],
    runs=[dict(layer=2, pts=[[69.35, 1.4], [69.3, 1.25]]),
          dict(layer=0, pts=[[69.3, 1.25], [68.3, 1.65],
                             [66.3, 1.45], [66.05, 2.0]])])
print('fanout v5b worst pairs:', flush=True)
for (m, l, it, o) in gate_pairs(FAN0, 'I2C_SCL', 0.10)[:5]:
    print(f'   {m:+.3f} L{l} {L.fmt_it(it)} vs {L.fmt_it(o)}',
          flush=True)
best = None
for vx in (66.25, 66.3, 66.35, 66.4, 66.45):
    for vy in (1.35, 1.45, 1.55, 1.6):
        for (ex, ey) in ((66.05, 2.0), (66.1, 2.05), (66.0, 1.95)):
            for ry in (1.65, 1.75):
                J = dict(
                    vias=[[69.3, 1.25], [vx, vy]],
                    runs=[dict(layer=2, pts=[[69.35, 1.4],
                                             [69.3, 1.25]]),
                          dict(layer=0, pts=[[69.3, 1.25],
                                             [68.3, ry], [vx, vy],
                                             [ex, ey]])])
                w, _, _ = gate_worst(J, 'I2C_SCL', 0.10)
                if w >= -0.001 and (best is None or w > best[0]):
                    best = (w, J)
                    print(f'fanout candidate via ({vx},{vy}) end '
                          f'({ex},{ey}) ride {ry}: {w:+.3f}',
                          flush=True)
if best:
    add_new('scl_ffan', best[1], 'I2C_SCL', 0.10)
    print(f'fanout EMITTED (worst {best[0]:+.3f})', flush=True)
# 2. XO bridge v4
for xv in (71.2, 71.0, 71.35):
    J = dict(vias=[], runs=[dict(layer=2, pts=[
        [72.125, 9.875], [xv, 14.0], [xv, 19.0], [71.95, 19.7]])])
    w, wo, wl = gate_worst(J, 'XO', 0.10)
    print(f'XO B ride x{xv} worst {w:+.3f} L{wl} '
          f'vs {L.fmt_it(wo) if wo else None}', flush=True)
    if w >= -0.001:
        add_new('xo_bridge', J, 'XO', 0.10)
        print('XO bridge EMITTED', flush=True)
        break
fr = fragments('XO', (60.0, 90.0, 4.0, 33.0))
print(f'XO fragments now: {len(fr)}', flush=True)
# 3. +3V3D stub v7
JV7 = dict(vias=[[73.9, 23.3]],
           runs=[dict(layer=0, pts=[[72.375, 21.125], [73.9, 23.3]]),
                 dict(layer=1, pts=[[73.9, 23.3],
                                     [74.625, 24.375]])])
print('stub v7 worst pairs:', flush=True)
for (m, l, it, o) in gate_pairs(JV7, '+3V3D', 0.15)[:5]:
    print(f'   {m:+.3f} L{l} {L.fmt_it(it)} vs {L.fmt_it(o)}',
          flush=True)
w, wo, wl = gate_worst(JV7, '+3V3D', 0.15)
if w >= -0.001:
    add_new('detour_+3V3D_stub', JV7, '+3V3D', 0.15)
    print('stub v7 EMITTED', flush=True)
else:
    JV7b = dict(vias=[[73.9, 23.3], [74.3, 24.2]],
                runs=[dict(layer=0, pts=[[72.375, 21.125],
                                         [73.9, 23.3]]),
                      dict(layer=2, pts=[[73.9, 23.3], [74.3, 24.2]]),
                      dict(layer=1, pts=[[74.3, 24.2],
                                         [74.625, 24.375]])])
    w, wo, wl = gate_worst(JV7b, '+3V3D', 0.15)
    print(f'stub v7b worst {w:+.3f} L{wl} '
          f'vs {L.fmt_it(wo) if wo else None}', flush=True)
    if w >= -0.001:
        add_new('detour_+3V3D_stub', JV7b, '+3V3D', 0.15)
        print('stub v7b EMITTED', flush=True)


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
save('scratch/work/au/build_au88.json')
print('done', flush=True)

"""t_au92: phase 2u. Rebuild from au91.
1. Fanout v9: flat ride y1.63, stub x66.15 vertical.
2. XO bridge v8: F column x71.9 from frag-96 term, via
   (71.9,20.2), In2 dip S of arr_data to frag-44's end.
3. +3V3D join ride: F from stub term (72.375,21.125) NW to
   X2.4 pad (70.45,22.925), crossing y21.7 at x71.2.
Saves build_au92.json."""
import wx
_app = wx.App(False)
import sys, json, math
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'p2u'}
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
fragments = g['fragments']
import t_ai_lib as L


def add_new(name, J, net, hw=0.10):
    JOURNEYS[name] = J
    for l, its in journey_items_dense(J, net, hw=hw).items():
        NEW[l] += its
        pool[l] += its


B = json.load(open('scratch/work/au/build_au91.json'))
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
print('model rebuilt from au91', flush=True)


def gate_pairs(J, net, hw, top=4):
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
    return out[:top]


def try_emit(name, J, net, hw):
    p = gate_pairs(J, net, hw)
    print(f'{name} worst pairs:', flush=True)
    for (m, l, it, o) in p:
        print(f'   {m:+.3f} L{l} {L.fmt_it(it)} vs {L.fmt_it(o)}',
              flush=True)
    if not p or p[0][0] >= -0.001:
        add_new(name, J, net, hw)
        NET_HW[name] = (net, hw)
        print(f'{name} EMITTED', flush=True)
        return True
    return False


FAN9 = dict(
    vias=[[69.3, 1.25]],
    runs=[dict(layer=2, pts=[[69.35, 1.4], [69.3, 1.25]]),
          dict(layer=0, pts=[[69.3, 1.25], [68.3, 1.63], [66.5, 1.63],
                             [66.15, 1.45], [66.15, 2.1]])])
try_emit('scl_ffan', FAN9, 'I2C_SCL', 0.10)
XB8 = dict(vias=[[71.9, 20.2]],
           runs=[dict(layer=0, pts=[[71.625, 25.625], [71.9, 25.3],
                                    [71.9, 20.2]]),
                 dict(layer=1, pts=[[71.9, 20.2], [71.0, 19.5],
                                    [69.6, 19.55], [68.875, 20.375]])])
try_emit('xo_bridge', XB8, 'XO', 0.10)
fr = fragments('XO', (60.0, 90.0, 4.0, 33.0))
print(f'XO fragments now: {len(fr)}', flush=True)
J3 = dict(vias=[], runs=[dict(layer=0, pts=[
    [72.375, 21.125], [71.6, 21.35], [71.2, 21.9], [70.6, 22.6],
    [70.45, 22.8]])])
try_emit('detour_+3V3D_stub', J3, '+3V3D', 0.15)
fr = fragments('+3V3D', (50.0, 86.0, -2.0, 32.0))
print(f'+3V3D fragments now: {len(fr)}', flush=True)
fr = fragments('I2C_SCL', (55.0, 90.0, -12.0, 33.0))
print(f'SCL fragments now: {len(fr)}', flush=True)


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
save('scratch/work/au/build_au92.json')
print('done', flush=True)

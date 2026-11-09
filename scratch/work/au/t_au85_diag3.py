"""t_au85: diagnostics 3 in the au83 model state.
(a) XO items x[74,84] y[14,20] (any layer) - find the E break.
(b) ULPI_DIR segs on ALL layers, endpoints in x[55,72] y[-1,9].
(c) +3V3D stub detour v6 (designed): F (72.375,21.125) ->
    (74.9,21.5), via, In2 -> (74.625,24.375). Exact gate."""
import wx
_app = wx.App(False)
import sys, json, math
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'p2n'}
src71 = open('scratch/work/au/t_au71_phase2b.py').read()
exec(src71.split("NEW = {")[0], g)
pool = g['pool']
C = g['C']
journey_items_dense = g['journey_items_dense']
g['NEW'] = {0: [], 1: [], 2: []}
g['JOURNEYS'] = {}
exec(src71[src71.index("def item_margin"):src71.index("def fragments")],
     g)
NEW = g['NEW']
JOURNEYS = g['JOURNEYS']
item_margin = g['item_margin']
import t_ai_lib as L


def add_new(name, J, net, hw=0.10):
    JOURNEYS[name] = J
    for l, its in journey_items_dense(J, net, hw=hw).items():
        NEW[l] += its
        pool[l] += its


B = json.load(open('scratch/work/au/build_au83.json'))
for net, lst in B['rip2'].items():
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
          'data_tail': ('CAP_DATA', 0.10),
          'arr_data': ('CAP_DATA', 0.10), 'arr_clk': ('CAP_CLK', 0.10),
          'data_entry': ('CAP_DATA', 0.10),
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
print('--- (a) XO items x[74,84] y[14,20]:', flush=True)
for l in range(3):
    for it in pool[l]:
        if it[1] == 'XO' and 74 < C(it)[0] < 84 and 14 < C(it)[1] < 20:
            print(f'    L{l}', L.fmt_it(it), flush=True)
print('--- (b) ULPI_DIR segs all layers, endpoints in box:',
      flush=True)
for l in range(3):
    for it in pool[l]:
        if it[0] == 'seg' and it[1] == 'ULPI_DIR':
            d = it[2]
            if (55 < d[0] < 72 and -1 < d[1] < 9) or \
                    (55 < d[2] < 72 and -1 < d[3] < 9):
                print(f'    L{l}', L.fmt_it(it), flush=True)
# (c) +3V3D stub detour v6
J = dict(vias=[[74.9, 21.5]],
         runs=[dict(layer=0, pts=[[72.375, 21.125], [74.9, 21.5]]),
               dict(layer=1, pts=[[74.9, 21.5], [74.625, 24.375]])])
its = journey_items_dense(J, '+3V3D', hw=0.15)
w, wo, wl = 9.9, None, None
for l in range(3):
    for it in its[l]:
        for o in pool[l]:
            if o[1] == '+3V3D':
                continue
            m = item_margin(l, it, [o])
            if m < w:
                w, wo, wl = m, o, l
print(f'+3V3D stub detour v6 worst {w:+.3f} L{wl} '
      f'vs {L.fmt_it(wo) if wo else None}', flush=True)
print('done', flush=True)

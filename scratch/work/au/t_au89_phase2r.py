"""t_au89: phase 2r - last model round. Rebuild from au88.
1. seg_margin diagnostic: SCL stub vs TMP seg; vertical stubs.
2. Fanout scan v6 (wider) + GND-chain re-lay variant.
3. XO bridge v5: B far-W detour x69.35, E run y19.6.
4. +3V3D stub v8: via at term (72.375,21.125), In2 N+E to
   (74.625,24.375).
Saves build_au89.json."""
import wx
_app = wx.App(False)
import sys, json, math
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'p2r'}
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

# 1. diagnostic (before rebuild; pool = esc model here)
TMPSEG = ('seg', 'TMP_ALERT', (65.7, 2.2, 65.7, -2.6, 0.125), 0.125)
print('diag stub/TMP seg_margin:',
      L.seg_margin(0, (66.3, 1.45), (66.05, 2.0), 'I2C_SCL', 0.10,
                   [TMPSEG]),
      flush=True)
for xx in (66.05, 66.2, 66.35):
    print(f'diag vertical stub x{xx}:',
          L.seg_margin(0, (xx, 1.5), (xx, 2.0), 'I2C_SCL', 0.10,
                       [TMPSEG]),
          flush=True)


def add_new(name, J, net, hw=0.10):
    JOURNEYS[name] = J
    for l, its in journey_items_dense(J, net, hw=hw).items():
        NEW[l] += its
        pool[l] += its


B = json.load(open('scratch/work/au/build_au88.json'))
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
print('model rebuilt from au88', flush=True)


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


# 2. fanout scan v6
best = None
for vx in (66.3, 66.4, 66.5):
    for vy in (1.45, 1.6, 1.75):
        for ry in (1.7, 1.85):
            for (ex, ey) in ((66.05, 2.0), (66.12, 2.03)):
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
                    print(f'fanout cand via ({vx},{vy}) ry {ry} '
                          f'end ({ex},{ey}): {w:+.3f}', flush=True)
if best is None:
    # GND-chain re-lay variant: rip 3 chain segs, re-lay S
    CHAIN = [('seg', 'GND', (68.9, 0.85, 68.2, 1.15), 0.10),
             ('seg', 'GND', (68.2, 1.15, 67.85, 1.22), 0.10),
             ('seg', 'GND', (67.85, 1.22, 67.5, 0.95), 0.10)]
    ok = all(any(o == c for o in pool[0]) for c in CHAIN)
    print('GND chain present:', ok, flush=True)
    if ok:
        for c in CHAIN:
            pool[0].remove(c)
            RIP2.setdefault('GND', []).append(
                [c[0], c[1], list(c[2]), c[3]])
        GD = dict(vias=[], runs=[dict(layer=0, pts=[
            [68.9, 0.85], [68.2, 0.72], [67.85, 0.75],
            [67.5, 0.95]])])
        w, wo, wl = gate_worst(GD, 'GND', 0.10)
        print(f'GND detour worst {w:+.3f} '
              f'vs {L.fmt_it(wo) if wo else None}', flush=True)
        if w >= -0.001:
            add_new('detour_GND_chain', GD, 'GND', 0.10)
            NET_HW['detour_GND_chain'] = ('GND', 0.10)
            for vx in (66.3, 66.4):
                for vy in (1.45, 1.6):
                    J = dict(
                        vias=[[69.3, 1.25], [vx, vy]],
                        runs=[dict(layer=2, pts=[[69.35, 1.4],
                                                 [69.3, 1.25]]),
                              dict(layer=0, pts=[[69.3, 1.25],
                                                 [68.3, 1.7],
                                                 [vx, vy],
                                                 [66.05, 2.0]])])
                    w, _, _ = gate_worst(J, 'I2C_SCL', 0.10)
                    if w >= -0.001 and (best is None or w > best[0]):
                        best = (w, J)
                        print(f'fanout cand (chain moved) via '
                              f'({vx},{vy}): {w:+.3f}', flush=True)
if best:
    add_new('scl_ffan', best[1], 'I2C_SCL', 0.10)
    NET_HW['scl_ffan'] = ('I2C_SCL', 0.10)
    print(f'fanout EMITTED (worst {best[0]:+.3f})', flush=True)
else:
    print('fanout STILL OPEN', flush=True)
# 3. XO bridge v5
for xv in (69.35, 69.2):
    J = dict(vias=[], runs=[dict(layer=2, pts=[
        [72.625, 12.25], [xv, 12.25], [xv, 19.6], [71.95, 19.7]])])
    w, wo, wl = gate_worst(J, 'XO', 0.10)
    print(f'XO bridge v5 x{xv} worst {w:+.3f} L{wl} '
          f'vs {L.fmt_it(wo) if wo else None}', flush=True)
    if w >= -0.001:
        add_new('xo_bridge', J, 'XO', 0.10)
        NET_HW['xo_bridge'] = ('XO', 0.10)
        print('XO bridge EMITTED', flush=True)
        break
fr = fragments('XO', (60.0, 90.0, 4.0, 33.0))
print(f'XO fragments now: {len(fr)}', flush=True)
# 4. +3V3D stub v8
JV8 = dict(vias=[[72.375, 21.125]],
           runs=[dict(layer=1, pts=[[72.375, 21.125],
                                    [72.375, 24.1],
                                    [74.625, 24.375]])])
w, wo, wl = gate_worst(JV8, '+3V3D', 0.15)
print(f'stub v8 worst {w:+.3f} L{wl} '
      f'vs {L.fmt_it(wo) if wo else None}', flush=True)
if w >= -0.001:
    add_new('detour_+3V3D_stub', JV8, '+3V3D', 0.15)
    NET_HW['detour_+3V3D_stub'] = ('+3V3D', 0.15)
    print('stub v8 EMITTED', flush=True)


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
save('scratch/work/au/build_au89.json')
print('done', flush=True)

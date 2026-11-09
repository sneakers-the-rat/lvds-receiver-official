"""t_av13: CAP landing design v3 - coordinated 3-fence re-lay for
the XO dip.

Diagnosis (t_av6/t_av10 probes, t_av11 attempts): the dip via lens
is pinched by C49's GND pad (F, shortfall 0.375 at the best point),
RBIAS's terminus via (69.625,20.625) (In2/B, shortfall 0.254 at
(69.95,20.25) / 0.001 at (70.3,20.3)) and ULPI_DIR's long B seg
(B, shortfall ~0.03). No single change opens it. Combined:

1. C49 shifts E +0.5: centre (70.0,19.5) -> (70.5,19.5); +3V3A web
   re-laid by A*; GND pad is zone-fed (no web).
2. RBIAS terminus via moves (69.625,20.625) -> (69.45,20.85) (it
   overlaps RBIAS's own pad rect corner - same net, legal); its F
   tail seg re-laid (69.45,20.85)->(69.425,21.0).
3. ULPI_DIR's long B seg (71.375,19.125)->(68.875,29.0) re-laid
   by B-only A* with the dip via bubble + dip B approach reserved
   by dummy fences.
4. Dip: via candidates scanned from the XO field (viafit cells in
   the knot box); for each, B run (stub->via) and In2 run
   (via->goal) by layer-locked A*; first full success wins.
5. RBIAS ride A* to the NEW terminus via; staircase vertical
   bookkeeping as before.
6. +3V3D stub join (t_av11 logic, phase B included).
7. Full gate; fragment verification; save build_av1.json (moves:
   C49) + pool_av1.json.
"""
import wx
_app = wx.App(False)
import sys, json, math
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'av13'}
src = open('scratch/work/au/t_au97_phase2y.py').read()
exec(src.split("# 1. RBIAS tail re-lay")[0], g)
pool = g['pool']
NEW = g['NEW']
JOURNEYS = g['JOURNEYS']
NET_HW = g['NET_HW']
B = g['B']
fragments = g['fragments']
make_astar = g['make_astar']
journey_items_dense = g['journey_items_dense']
item_margin = g['item_margin']
try_emit = g['try_emit']
gate_pairs = g['gate_pairs']
import t_ai_lib as L
import numpy as np

R2 = lambda v: round(v, 3)


def rgeom(it):
    return tuple(R2(v) for v in it[2])


def frag_report(net, box):
    fr = fragments(net, box)
    print(f'fragments({net}) = {len(fr)} sizes '
          f'{sorted((len(f["items"]) for f in fr), reverse=True)}',
          flush=True)
    return fr


def remove_journey(name):
    net, hw = NET_HW[name]
    its = journey_items_dense(JOURNEYS[name], net, hw=hw)
    for l in range(3):
        for it in its[l]:
            NEW[l].remove(it)
            pool[l].remove(it)
    del JOURNEYS[name]
    del NET_HW[name]


def gate_items(tag, items_by_layer, net):
    worst = 9.9
    for l in range(3):
        for it in items_by_layer[l]:
            m = item_margin(l, it, pool[l])
            if m < worst:
                worst = m
    print(f'  {tag} worst margin {worst:+.3f}', flush=True)
    return worst >= -0.001


# ------------------------------------------------------------- rip 19
STUB = (73.875, 11.625, 73.875, 12.875)
VERT = (73.875, 12.875, 73.875, 16.375)
rip_now, keep_vert = [], None
for it in list(pool[1]):
    if it[0] == 'seg' and it[1] == 'RBIAS':
        rg = rgeom(it)
        if rg == STUB:
            continue
        if rg == VERT:
            keep_vert = it
            continue
        rip_now.append(it)
assert len(rip_now) == 19, f'rip set {len(rip_now)} != 19'
for it in rip_now:
    pool[1].remove(it)
RIP_ADD = {'RBIAS': [[it[0], it[1], list(it[2]), it[3]] for it in rip_now]}
print(f'RBIAS staircase: ripped {len(rip_now)}', flush=True)
dir_before = frag_report('ULPI_DIR', (60, 82, -4, 32))

# ------------------------------------------------- 1. C49 shift E +0.5
print('=== C49 shift E to (70.5,19.5) ===', flush=True)
C49_OLD = (70.0, 19.5)
C49_NEW = (70.5, 19.5)
PADS_OLD = {'+3V3A': (69.225, 19.5), 'GND': (70.775, 19.5)}
pad_items = {}
for net, (px, py) in PADS_OLD.items():
    for it in pool[0]:
        if it[0] == 'pad' and it[1] == net and \
                abs(it[2][0] - px) < 0.01 and abs(it[2][1] - py) < 0.01:
            pad_items[net] = it
    assert net in pad_items, net
for net in PADS_OLD:
    pool[0].remove(pad_items[net])
for net, dx in (('+3V3A', -0.775), ('GND', 0.775)):
    pool[0].append(('pad', net,
                    (C49_NEW[0] + dx, C49_NEW[1], 0.450, 0.475, 0.0),
                    pad_items[net][3]))


def web_relay(net, new_xy, old_xy):
    a = make_astar((min(new_xy[0], old_xy[0]) - 1.5,
                    max(new_xy[0], old_xy[0]) + 1.5,
                    min(new_xy[1], old_xy[1]) - 1.5,
                    max(new_xy[1], old_xy[1]) + 1.5), step=0.025)
    for gl in (0, 2, 1):
        J = a(net, ((0, 1, 2), new_xy[0], new_xy[1]),
              (gl, old_xy[0], old_xy[1]), 0.10)
        if J is not None:
            return J
    return None


J = web_relay('+3V3A', (C49_NEW[0] - 0.775, C49_NEW[1]),
              PADS_OLD['+3V3A'])
assert J is not None, 'C49 +3V3A web re-lay: NONE'
assert try_emit('c49_web_v3a', J, '+3V3A', 0.10), 'C49 web gate refused'
print('C49 moved; +3V3A web re-laid', flush=True)

# --------------------------------------- 2. (RBIAS via move DROPPED)
# t_av14 probe: the (69.45,20.85) spot is fenced by CAP_DATA's In2
# W run (-0.085). Not needed: with C49 shifted E, the dip via at
# (70.45,20.25) clears the OLD RBIAS via by 0.906 (field +0.406).

# ------------------------------------------------- 3. DIR tail re-lay
print('=== ULPI_DIR long B seg re-lay (dip corridor reserved) ===',
      flush=True)
DIP_VIA_GUESS = (70.45, 20.25)
dir_seg = None
for it in pool[2]:
    if it[0] == 'seg' and it[1] == 'ULPI_DIR' and \
            rgeom(it) == (71.375, 19.125, 68.875, 29.0, 0.1):
        dir_seg = it
assert dir_seg is not None, 'DIR long B seg not found'
pool[2].remove(dir_seg)
RIP_ADD.setdefault('ULPI_DIR', []).append(
    [dir_seg[0], dir_seg[1], list(dir_seg[2]), dir_seg[3]])
DUM = 'BLOCK_RSVD'
dummies = []
# Reserve ONLY the dip via's own bubble (r0.25): its track
# exclusion (0.55) is exactly the clearance the real via needs.
# A fatter reservation seals DIR's only thread (t_av17 isolation).
for l in range(3):
    dummies.append((l, ('via', DUM, (DIP_VIA_GUESS[0], DIP_VIA_GUESS[1],
                                     0.30), 0.2)))
for l, it in dummies:
    pool[l].append(it)
a_dir = make_astar((68.3, 72.2, 18.6, 29.6), step=0.025)
JD = a_dir('ULPI_DIR', ((2,), 71.375, 19.125), (2, 68.875, 29.0), 0.10,
           layer_lock=(False, False, True))
for l, it in dummies:
    pool[l].remove(it)
assert JD is not None, 'DIR tail re-lay: NONE'
print(f'  DIR A*: vias={JD["vias"]} '
      f'runs={[(r["layer"], len(r["pts"])) for r in JD["runs"]]}',
      flush=True)
assert try_emit('dir_tail_relay', JD, 'ULPI_DIR', 0.10), \
    'DIR tail gate refused'
frag_report('ULPI_DIR', (60, 82, -4, 32))

# ------------------------------------------------- 4. the dip
print('=== dip via scan (XO fields, current pool) ===', flush=True)
NET = 'XO'
myclr = L.netclass(NET)[1]
box = (68.3, 72.6, 18.9, 21.6)
X0, X1, Y0, Y1 = box
step = 0.025
xs = np.arange(X0, X1 + 1e-9, step)
ys = np.arange(Y0, Y1 + 1e-9, step)
GX, GY = np.meshgrid(xs, ys)


def dfun(it):
    kind, d = it[0], it[2]
    if kind == 'pad':
        cx, cy, hw, hh, rot = d
        dx, dy = GX - cx, GY - cy
        c, s = math.cos(-rot), math.sin(-rot)
        lx, ly = dx * c - dy * s, dx * s + dy * c
        return np.hypot(np.maximum(np.abs(lx) - hw, 0.0),
                        np.maximum(np.abs(ly) - hh, 0.0))
    if kind == 'seg':
        x1, y1, x2, y2, hw = d
        px, py = GX - x1, GY - y1
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else np.clip((px * dx + py * dy) / L2, 0, 1)
        return np.hypot(px - t * dx, py - t * dy) - hw
    return np.hypot(GX - d[0], GY - d[1]) - d[2]


G = {}
for l in range(3):
    f = np.full(GX.shape, 9.9)
    for it in pool[l]:
        if it[1] == NET:
            continue
        req = max(myclr, it[3])
        f = np.minimum(f, dfun(it) - req)
    G[l] = f
minf = np.minimum(np.minimum(G[0], G[1]), G[2])
viafit = minf >= 0.25
trackB = G[2] >= 0.10
trackI = G[1] >= 0.10
cells = []
for iy in range(len(ys)):
    for ix in range(len(xs)):
        if viafit[iy, ix] and trackB[iy, ix] and trackI[iy, ix]:
            cells.append((float(xs[ix]), float(ys[iy])))
print(f'viafit+track cells in knot: {len(cells)}', flush=True)
if not cells:
    flat = [(float(minf[iy, ix]), float(xs[ix]), float(ys[iy]),
             float(G[0][iy, ix]), float(G[1][iy, ix]),
             float(G[2][iy, ix]))
            for iy in range(len(ys)) for ix in range(len(xs))]
    flat.sort(reverse=True)
    print('top cells by min-field (minf, x, y, F, In2, B):',
          flush=True)
    for row in flat[:15]:
        print(f'   {row[0]:+.3f} ({row[1]:.3f},{row[2]:.3f}) '
              f'F={row[3]:+.3f} In2={row[4]:+.3f} B={row[5]:+.3f}',
              flush=True)
# rank: closest to the guess first
cells.sort(key=lambda p: (p[0] - DIP_VIA_GUESS[0]) ** 2
           + (p[1] - DIP_VIA_GUESS[1]) ** 2)
for c in cells[:12]:
    print(f'   via candidate {c}', flush=True)

a_dip = make_astar((68.3, 74.6, 18.9, 26.3), step=0.025)
dip_done = False
for (vx, vy) in cells[:14]:
    JB = a_dip('XO', ((2,), 71.875, 19.625), (2, vx, vy), 0.10,
               layer_lock=(False, False, True))
    if JB is None:
        print(f'  via ({vx:.3f},{vy:.3f}): B run NONE', flush=True)
        continue
    JI = a_dip('XO', ((1,), vx, vy), (1, 68.875, 20.375), 0.10,
               layer_lock=(False, True, False))
    if JI is None:
        print(f'  via ({vx:.3f},{vy:.3f}): In2 run NONE', flush=True)
        continue
    J = dict(vias=[[vx, vy]], runs=JB['runs'] + JI['runs'])
    print(f'  via ({vx:.3f},{vy:.3f}): runs '
          f'{[(r["layer"], len(r["pts"])) for r in J["runs"]]}',
          flush=True)
    if try_emit('xo_bridge', J, 'XO', 0.10):
        fr = frag_report('XO', (63, 94, 7, 29))
        if len(fr) == 1:
            dip_done = True
            print(f'DIP CLOSED via ({vx:.3f},{vy:.3f})', flush=True)
            break
        remove_journey('xo_bridge')
    print('  dip attempt failed - next candidate', flush=True)
assert dip_done, 'DIP FAILED: no via candidate closed XO'

# ------------------------------------------------- 5. RBIAS ride
print('=== RBIAS A* re-lay to terminus (69.625,20.625) ===',
      flush=True)
astar_rb = make_astar((68.5, 74.75, 11.0, 21.5), step=0.025)
attempts = [
    (((0, 1, 2), 73.875, 11.625), 2, 0.125),
    (((0, 1, 2), 73.875, 11.625), 2, 0.10),
    (((2,), 73.875, 11.625), 2, 0.125),
    (((2,), 73.875, 11.625), 2, 0.10),
    (((0, 1, 2), 73.875, 11.625), 1, 0.125),
]
rb_done = False
for start, glayer, hw in attempts:
    J = astar_rb('RBIAS', start, (glayer, 69.625, 20.625), hw)
    if J is None:
        print(f'  A* start={start[0]} goal_layer={glayer} hw={hw}: '
              f'NONE', flush=True)
        continue
    print(f'  A* start={start[0]} goal_layer={glayer} hw={hw}: '
          f'vias={J["vias"]} '
          f'runs={[(r["layer"], len(r["pts"])) for r in J["runs"]]}',
          flush=True)
    if try_emit('rbias_relay', J, 'RBIAS', hw):
        used = [rgeom(it) for it in
                journey_items_dense(J, 'RBIAS', hw=hw)[1]]
        if keep_vert is not None and rgeom(keep_vert) not in used:
            pool[1].remove(keep_vert)
            RIP_ADD['RBIAS'].append(
                [keep_vert[0], keep_vert[1], list(keep_vert[2]),
                 keep_vert[3]])
            print('  vertical unused - ripped too '
                  f'(total RBIAS rips: {len(RIP_ADD["RBIAS"])})',
                  flush=True)
        else:
            print('  ride uses the In2 vertical - it stays',
                  flush=True)
        rb_done = True
        break
    print('  ride emit refused - next attempt', flush=True)
assert rb_done, 'RBIAS RIDE FAILED'
frag_report('RBIAS', (63, 80, 9, 26))

# ------------------------------------------------- 6. JOIN 2
print('=== JOIN 2: +3V3D stub ride ===', flush=True)
v3_before = frag_report('+3V3D', (60, 95, -8, 28))
astar_f = make_astar((68.8, 74.2, 19.2, 24.4), step=0.025)


def stub_ride(tag):
    for hw in (0.15, 0.125, 0.10):
        J = astar_f('+3V3D', (0, 72.375, 21.125), (0, 70.45, 22.925),
                    hw, layer_lock=(True, False, False))
        if J is None:
            print(f'  stub A* ({tag}) hw={hw}: NONE', flush=True)
            continue
        print(f'  stub A* ({tag}) hw={hw}: vias={J["vias"]} '
              f'runs={[(r["layer"], len(r["pts"])) for r in J["runs"]]}',
              flush=True)
        if try_emit('detour_+3V3D_stub', J, '+3V3D', hw):
            return True
    return False


join2_done = stub_ride('unmodified clk9')
if not join2_done:
    print('=== JOIN 2 phase B: re-plan arr_clk tail eastward ===',
          flush=True)
    old_clk9 = JOURNEYS['clk9']
    old_arr = JOURNEYS['arr_clk']
    old_clk9_items = journey_items_dense(old_clk9, 'CAP_CLK', hw=0.10)
    old_arr_items = journey_items_dense(old_arr, 'CAP_CLK', hw=0.10)
    ride_run = [r for r in old_clk9['runs'] if r['layer'] == 2][0]
    in2_run = [r for r in old_clk9['runs'] if r['layer'] == 1][0]
    f_tail = [r for r in old_clk9['runs']
              if r['layer'] == 0 and tuple(r['pts'][0]) == (74.4, 22.9)][0]
    astar_e = make_astar((69.9, 73.5, 20.9, 22.6), step=0.025)
    for P in [(71.2, 21.8), (71.3, 21.75), (71.15, 21.9), (71.25, 21.7)]:
        JE = astar_e('CAP_CLK', ((1,), 70.1, 21.8), (1, P[0], P[1]),
                     0.10, layer_lock=(False, True, False))
        if JE is None:
            print(f'  extension A* to {P}: NONE', flush=True)
            continue
        ext_pts = [tuple(p) for p in JE['runs'][0]['pts']]
        print(f'  extension to {P}: {len(ext_pts)} pts', flush=True)
        for src_items in (old_clk9_items, old_arr_items):
            for l in range(3):
                for it in src_items[l]:
                    NEW[l].remove(it)
                    pool[l].remove(it)
        new_arr = dict(vias=[], runs=[dict(
            layer=1, pts=[list(p) for p in
                          [tuple(p) for p in old_arr['runs'][0]['pts']]
                          + ext_pts[1:]])])
        new_clk9 = dict(
            vias=[[64.75, 16.95], list(P), [73.25, 21.75], [74.4, 22.9]],
            runs=[ride_run,
                  dict(layer=0, pts=[list(P), [73.25, 21.75]]),
                  in2_run, f_tail])
        ok = True
        for name, JJ in (('arr_clk', new_arr), ('clk9', new_clk9)):
            if not try_emit(name, JJ, 'CAP_CLK', 0.10):
                ok = False
                break
        if ok and stub_ride(f'tail at {P}'):
            join2_done = True
            break
        for name, JJ in (('arr_clk', new_arr), ('clk9', new_clk9)):
            if name in JOURNEYS:
                its = journey_items_dense(JJ, 'CAP_CLK', hw=0.10)
                for l in range(3):
                    for it in its[l]:
                        if it in NEW[l]:
                            NEW[l].remove(it)
                        if it in pool[l]:
                            pool[l].remove(it)
                del JOURNEYS[name]
                NET_HW.pop(name, None)
        if 'detour_+3V3D_stub' in JOURNEYS:
            remove_journey('detour_+3V3D_stub')
        for l in range(3):
            for it in old_arr_items[l]:
                NEW[l].append(it)
                pool[l].append(it)
            for it in old_clk9_items[l]:
                NEW[l].append(it)
                pool[l].append(it)
        JOURNEYS['arr_clk'] = old_arr
        JOURNEYS['clk9'] = old_clk9
        NET_HW['arr_clk'] = ('CAP_CLK', 0.10)
        NET_HW['clk9'] = ('CAP_CLK', 0.10)
        print(f'  restored originals after P={P}', flush=True)
assert join2_done, 'JOIN 2 FAILED: stub ride not emitted'
v3_after = frag_report('+3V3D', (60, 95, -8, 28))
print(f'+3V3D sizes before={sorted((len(f["items"]) for f in v3_before), reverse=True)} '
      f'after={sorted((len(f["items"]) for f in v3_after), reverse=True)}',
      flush=True)

# ------------------------------------------------- 7. gate + save
print('=== full gate (au97 semantics) ===', flush=True)
fails = []
for l in range(3):
    for it in NEW[l]:
        m = item_margin(l, it, pool[l])
        if m < -0.001:
            fails.append((m, l, it))
print(f'full gate fails: {len(fails)}', flush=True)
for (m, l, it) in fails[:12]:
    print(f'   {m:+.3f} L{l} {L.fmt_it(it)}', flush=True)
assert not fails, 'full gate failed - do not build from this model'

print('=== final fragment counts ===', flush=True)
frag_report('CAP_CLK', (60, 80, -2, 28))
frag_report('CAP_DATA', (60, 80, -2, 28))
frag_report('XO', (63, 94, 7, 29))
frag_report('RBIAS', (63, 80, 9, 26))
frag_report('ULPI_DIR', (60, 82, -4, 32))

RIP2_OUT = {net: [list(x) for x in lst] for net, lst in B['rip2'].items()}
for net, lst in RIP_ADD.items():
    RIP2_OUT.setdefault(net, []).extend(lst)
out = dict(journeys=JOURNEYS, fixed=B['fixed'], rip2=RIP2_OUT,
           extra=B['extra'], arrivals=B['arrivals'],
           clk_via=(70.2, 1.8), exit_via=(69.075, 2.8), u9_shift=1.25,
           moves={'C49': {'from': list(C49_OLD), 'to': list(C49_NEW)}})
json.dump(out, open('scratch/work/av/build_av1.json', 'w'), indent=1)
pool_out = {str(l): [[it[0], it[1], list(it[2]), it[3]] for it in pool[l]]
            for l in range(3)}
json.dump(pool_out, open('scratch/work/av/pool_av1.json', 'w'))
print('saved build_av1.json + pool_av1.json', flush=True)
print('t_av13 DONE', flush=True)

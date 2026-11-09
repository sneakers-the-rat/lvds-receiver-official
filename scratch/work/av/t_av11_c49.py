"""t_av11: CAP landing design v2 - move C49 to open the XO dip via
lens, then dip, RBIAS ride, +3V3D stub join; full gate; save
build_av1.json + pool_av1.json.

C49 (70.0,19.5): pad1 +3V3A (69.225,19.5), pad2 GND (70.775,19.5).
Its GND pad rect x[70.325,71.225] y[19.025,19.975] is the binding
F fence for every dip via candidate (t_av6 probe). Scan candidate
centres on a 0.25 grid, rank by pad margin, and for each: apply the
move in the model, re-lay C49's webs, run the dip A*; the first
candidate that closes XO wins.
"""
import wx
_app = wx.App(False)
import sys, json, math
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'av11'}
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
import t_ai_lib as L

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

# ------------------------------------------------------------- C49 webs
print('=== C49 incident webs (au93-state pool) ===', flush=True)
C49_OLD = (70.0, 19.5)
PADS_OLD = {'+3V3A': (69.225, 19.5), 'GND': (70.775, 19.5)}
pad_items = {}
for net, (px, py) in PADS_OLD.items():
    for it in pool[0]:
        if it[0] == 'pad' and it[1] == net and \
                abs(it[2][0] - px) < 0.01 and abs(it[2][1] - py) < 0.01:
            pad_items[net] = it
    print(f'  pad {net}: {L.fmt_it(pad_items[net])}', flush=True)
    for l in range(3):
        for it in pool[l]:
            if it[1] == net and it[0] == 'seg':
                d = it[2]
                for (ex, ey) in ((d[0], d[1]), (d[2], d[3])):
                    if abs(ex - px) < 0.8 and abs(ey - py) < 0.8:
                        print(f'    near L{l} {L.fmt_it(it)}', flush=True)
                        break

# ------------------------------------------------------------- C49 scan
print('=== C49 site scan ===', flush=True)
scan_pool = [it for it in pool[0]
             if it not in (pad_items['+3V3A'], pad_items['GND'])]
PHW, PHH = 0.450, 0.475


def item_bbox(it):
    d = it[2]
    if it[0] == 'seg':
        return (min(d[0], d[2]) - d[4], max(d[0], d[2]) + d[4],
                min(d[1], d[3]) - d[4], max(d[1], d[3]) + d[4])
    if it[0] == 'via':
        return (d[0] - d[2], d[0] + d[2], d[1] - d[2], d[1] + d[2])
    r = math.hypot(d[2], d[3])
    return (d[0] - r, d[0] + r, d[1] - r, d[1] + r)


BBOXES = [(item_bbox(it), it) for it in scan_pool]


def pad_margin(cx, cy, net):
    x0, x1, y0, y1 = cx - PHW, cx + PHW, cy - PHH, cy + PHH
    local = [it for (bb, it) in BBOXES
             if bb[0] < x1 + 1.0 and bb[1] > x0 - 1.0
             and bb[2] < y1 + 1.0 and bb[3] > y0 - 1.0]
    pts = []
    nx = int((x1 - x0) / 0.05)
    for i in range(nx + 1):
        x = x0 + i * 0.05
        pts.append((x, y0))
        pts.append((x, y1))
    ny = int((y1 - y0) / 0.05)
    for i in range(ny + 1):
        y = y0 + i * 0.05
        pts.append((x0, y))
        pts.append((x1, y))
    m = 9.9
    for (x, y) in pts:
        mm, _ = L.pt_margin(0, x, y, net, 0.0, local)
        if mm < m:
            m = mm
    return m


def scan_at(gx, gy):
    if abs(gx - C49_OLD[0]) < 0.01 and abs(gy - C49_OLD[1]) < 0.01:
        return None
    m1 = pad_margin(gx - 0.775, gy, '+3V3A')
    m2 = pad_margin(gx + 0.775, gy, 'GND')
    if m1 >= 0.03 and m2 >= 0.03:
        return (min(m1, m2), gx, gy, m1, m2)
    return None


cands = []
gx = 65.5
while gx <= 76.5:
    gy = 13.5
    while gy <= 25.5:
        c = scan_at(gx, gy)
        if c:
            cands.append(c)
        gy += 0.5
    gx += 0.5
cands.sort(reverse=True)
print(f'coarse legal centres: {len(cands)}', flush=True)
refined = []
for c in cands[:6]:
    for dx in (-0.25, 0.0, 0.25):
        for dy in (-0.25, 0.0, 0.25):
            cc = scan_at(round(c[1] + dx, 2), round(c[2] + dy, 2))
            if cc:
                refined.append(cc)
seen = {}
for c in cands + refined:
    seen[(c[1], c[2])] = c
cands = sorted(seen.values(), reverse=True)
print(f'legal centres after refine: {len(cands)}', flush=True)
for c in cands[:15]:
    print(f'   centre ({c[1]:.2f},{c[2]:.2f}) min={c[0]:+.3f} '
          f'v3a={c[3]:+.3f} gnd={c[4]:+.3f}', flush=True)

# ------------------------------------------------------------- dip A*
astar_dip = make_astar((68.3, 74.6, 18.9, 26.3), step=0.025)


def dip_astar():
    J = astar_dip('XO', ((2,), 71.875, 19.625), (1, 68.875, 20.375),
                  0.10)
    if J is None:
        print('  dip A*: NONE', flush=True)
        return False
    print(f'  dip A*: vias={J["vias"]} '
          f'runs={[(r["layer"], len(r["pts"])) for r in J["runs"]]}',
          flush=True)
    if not try_emit('xo_bridge', J, 'XO', 0.10):
        return False
    fr = frag_report('XO', (63, 94, 7, 29))
    if len(fr) != 1:
        print('  dip emitted but XO fragments != 1 - removing',
              flush=True)
        remove_journey('xo_bridge')
        return False
    return True


def web_relay(net, new_xy, old_xy):
    """A* a replacement web for a moved C49 pad: new pad -> old point
    (the web's remaining endpoint). Multi-layer, F preferred."""
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


print('=== C49 move attempts ===', flush=True)
move_done = None
for (mn, gx, gy, m1, m2) in cands[:10]:
    print(f'-- candidate centre ({gx:.2f},{gy:.2f}) min margin '
          f'{mn:+.3f}', flush=True)
    # apply move in the model
    for net in PADS_OLD:
        pool[0].remove(pad_items[net])
    new_pads = {}
    for net, dx in (('+3V3A', -0.775), ('GND', 0.775)):
        it = ('pad', net, (gx + dx, gy, PHW, PHH, 0.0),
              pad_items[net][3])
        pool[0].append(it)
        new_pads[net] = it
    ok = True
    made = []
    # GND pad is zone-fed (no incident segs in the census above):
    # no web journey for GND - the fill must cover the new site,
    # arbitrated by check_pcb on the built board.
    for net, dx in (('+3V3A', -0.775),):
        J = web_relay(net, (gx + dx, gy), PADS_OLD[net])
        if J is None:
            print(f'   web re-lay {net}: NONE', flush=True)
            ok = False
            break
        name = 'c49_web_' + ('v3a' if net == '+3V3A' else 'gnd')
        if try_emit(name, J, net, 0.10):
            made.append(name)
        else:
            print(f'   web re-lay {net}: gate refused', flush=True)
            ok = False
            break
    if ok and dip_astar():
        move_done = (gx, gy)
        pad_items.update(new_pads)
        break
    # revert
    if 'xo_bridge' in JOURNEYS:
        remove_journey('xo_bridge')
    for name in made:
        remove_journey(name)
    for net in PADS_OLD:
        pool[0].remove(new_pads[net])
        pool[0].append(pad_items[net])
    print('   reverted', flush=True)
assert move_done is not None, 'C49 MOVE FAILED: no candidate closed XO'
print(f'C49 MOVED to {move_done}', flush=True)
frag_report('+3V3A', (60, 95, -8, 28))

# ------------------------------------------------------------- RBIAS ride
print('=== RBIAS A* re-lay ===', flush=True)
astar_rb = make_astar((68.5, 74.75, 11.0, 21.5), step=0.025)
attempts = [
    (((0, 1, 2), 73.875, 11.625), 2, 0.125),
    (((0, 1, 2), 73.875, 11.625), 2, 0.10),
    (((2,), 73.875, 11.625), 2, 0.125),
    (((2,), 73.875, 11.625), 2, 0.10),
    (((0, 1, 2), 73.875, 11.625), 1, 0.125),
]


def rbias_ride():
    for start, glayer, hw in attempts:
        J = astar_rb('RBIAS', start, (glayer, 69.625, 20.625), hw)
        if J is None:
            print(f'  A* start={start[0]} goal_layer={glayer} '
                  f'hw={hw}: NONE', flush=True)
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
            return True
        print('  ride emit refused - next attempt', flush=True)
    return False


assert rbias_ride(), 'RBIAS RIDE FAILED after C49 move + dip'
frag_report('RBIAS', (63, 80, 9, 26))

# ------------------------------------------------------------- JOIN 2
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
        # restore originals
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

# ------------------------------------------------------------- gate
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

# ------------------------------------------------------------- save
RIP2_OUT = {net: [list(x) for x in lst] for net, lst in B['rip2'].items()}
for net, lst in RIP_ADD.items():
    RIP2_OUT.setdefault(net, []).extend(lst)
out = dict(journeys=JOURNEYS, fixed=B['fixed'], rip2=RIP2_OUT,
           extra=B['extra'], arrivals=B['arrivals'],
           clk_via=(70.2, 1.8), exit_via=(69.075, 2.8), u9_shift=1.25,
           moves={'C49': {'from': list(C49_OLD),
                          'to': list(move_done)}})
json.dump(out, open('scratch/work/av/build_av1.json', 'w'), indent=1)
pool_out = {str(l): [[it[0], it[1], list(it[2]), it[3]] for it in pool[l]]
            for l in range(3)}
json.dump(pool_out, open('scratch/work/av/pool_av1.json', 'w'))
print('saved build_av1.json + pool_av1.json', flush=True)
print('t_av11 DONE', flush=True)

"""t_aw9: H5 v3 - ride first, DM_PHY staircase span ablated, dip,
DM_PHY re-lay last in leftover space; then REFCLK relay, +3V3D X2
links, join 2, full gate, save build_aw1.json.
Usage: t_aw9_h5.py CX CY ROT (X2 far site)."""
import wx
_app = wx.App(False)
import sys, json, math
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'aw9'}
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
C = g['C']
import t_ai_lib as L
from router import dist_to_item

CX, CY, ROT = float(sys.argv[1]), float(sys.argv[2]), int(sys.argv[3])
print(f'=== H5 v3 at X2 site ({CX},{CY}) rot{ROT} ===', flush=True)
R2 = lambda v: round(v, 3)

def frag_report(net, box):
    fr = fragments(net, box)
    print(f'fragments({net}) = {len(fr)} sizes '
          f'{sorted((len(f["items"]) for f in fr), reverse=True)}',
          flush=True)
    return fr

def pad_margin(net, cx, cy, hw, hh, layer=0):
    x0, x1, y0, y1 = cx - hw, cx + hw, cy - hh, cy + hh
    pts = [(cx, cy)]
    n = 10
    for i in range(n + 1):
        t = i / n
        pts.append((x0 + (x1 - x0) * t, y0))
        pts.append((x0 + (x1 - x0) * t, y1))
        pts.append((x0, y0 + (y1 - y0) * t))
        pts.append((x1, y0 + (y1 - y0) * t))
    worst = (9e9, None)
    for o in pool[layer]:
        if o[1] == net:
            continue
        clr = L.pair_clr(net, o[1])
        for (px, py) in pts:
            d = dist_to_item(o, px, py) - clr
            if d < worst[0]:
                worst = (d, o)
    return worst

print('--- baseline fragments ---', flush=True)
base_xo = frag_report('XO', (63, 94, 7, 29))
base_v3 = frag_report('+3V3D', (60, 95, -8, 28))
base_clk = frag_report('CAP_CLK', (60, 80, -2, 28))
base_dat = frag_report('CAP_DATA', (60, 80, -2, 28))
base_ref = frag_report('REFCLK', (60, 80, 9, 42))
base_dm = frag_report('DM_PHY', (60, 82, -4, 32))

RIP_ADD = {}
def rip_rounded(l, net, geo4, kind='seg'):
    n = 0
    for it in list(pool[l]):
        if it[0] != kind or it[1] != net:
            continue
        if kind == 'seg':
            key = tuple(R2(v) for v in it[2][:4])
            want = tuple(R2(v) for v in geo4)
        else:
            key = (R2(it[2][0]), R2(it[2][1]))
            want = (R2(geo4[0]), R2(geo4[1]))
        if key == want:
            pool[l].remove(it)
            n += 1
    assert n == 1, f'rip {kind} {net} {geo4} L{l}: {n} victims'
    RIP_ADD.setdefault(net, []).append([kind, net, list(geo4), 0.2])
    return n

# 1. staircase rip
rip19 = [it for it in pool[1] if it[0] == 'seg' and it[1] == 'RBIAS']
assert len(rip19) == 19
for it in rip19:
    pool[1].remove(it)
    RIP_ADD.setdefault('RBIAS', []).append(
        [it[0], it[1], list(it[2]), it[3]])
print('RBIAS staircase ripped (19)', flush=True)

# 2. shrink
def shrink_pad(net, old_cx, new_cx, cy=18.0):
    for l in range(3):
        for it in list(pool[l]):
            if it[0] == 'pad' and it[1] == net:
                cc = C(it)
                if abs(cc[0] - old_cx) < 0.01 and abs(cc[1] - cy) < 0.01:
                    pool[l].remove(it)
                    pool[l].append(('pad', net,
                                     (new_cx, cy, 0.28, 0.31, 0), it[3]))
                    return True
    return False
for net, o, n in [('PHY_1V8', 71.725, 72.02), ('GND', 73.275, 72.98),
                  ('+3V3A', 67.975, 68.27), ('GND', 69.525, 69.23)]:
    assert shrink_pad(net, o, n)
print('C22+C24 shrunk (board-true 0402)', flush=True)

# 3. X2 move (pads) + REFCLK via/segs rip
PADS0 = [('+3V3D', -1.05, 0.825), ('GND', 1.05, 0.825),
         ('REFCLK', 1.05, -0.825), ('+3V3D', -1.05, -0.825)]
def offs(dx, dy):
    if ROT == 0:
        return dx, dy, 0.65, 0.55
    return -dy, dx, 0.55, 0.65
old_pads = []
for l in range(3):
    for it in list(pool[l]):
        if it[0] == 'pad' and (R2(it[2][0]), R2(it[2][1])) in \
                {(70.45, 24.575), (72.55, 24.575), (72.55, 22.925),
                 (70.45, 22.925)}:
            pool[l].remove(it)
            old_pads.append(it)
assert len(old_pads) == 4
new_pads = {}
for (net, dx, dy) in PADS0:
    ox, oy, hw, hh = offs(dx, dy)
    pool[0].append(('pad', net, (CX + ox, CY + oy, hw, hh, 0), 0.2))
    new_pads.setdefault(net, []).append((CX + ox, CY + oy))
    m, o = pad_margin(net, CX + ox, CY + oy, hw, hh)
    print(f'  X2 pad {net} at ({CX + ox:.3f},{CY + oy:.3f}) margin {m:+.3f}',
          flush=True)
    assert m >= -0.001, 'moved X2 pad not copper-legal'
for l in range(3):
    rip_rounded(l, 'REFCLK', (71.875, 23.375), kind='via')
rip_rounded(0, 'REFCLK', (72.3, 22.925, 72.55, 22.925))
rip_rounded(0, 'REFCLK', (71.875, 23.375, 72.3, 22.925))
print('X2 pads moved; REFCLK via + F segs ripped', flush=True)

# 4. RBIAS ride (composed solo form)
print('=== RBIAS ride (composed) ===', flush=True)
a_rb = make_astar((67.0, 75.5, 10.5, 22.5), step=0.025)
J1 = a_rb('RBIAS', ((1,), 73.875, 11.625), (1, 69.925, 20.475),
          0.125, layer_lock=(False, True, False))
assert J1 is not None, 'ride In2 leg NONE'
J2 = a_rb('RBIAS', ((2,), 69.925, 20.475), (2, 69.625, 20.625),
          0.125, layer_lock=(False, False, True))
assert J2 is not None, 'ride B hop NONE'
Jr = dict(vias=[[69.925, 20.475]], runs=J1['runs'] + J2['runs'])
assert try_emit('rbias_relay', Jr, 'RBIAS', 0.125), 'ride gate refused'
rb = frag_report('RBIAS', (63, 80, 9, 26))
assert len(rb) == 1
print('RBIAS RIDE CLOSED', flush=True)

# 5. ablate DM_PHY staircase span in the crossing box
print('=== DM_PHY span ablation ===', flush=True)
ABL_BOX = (69.5, 73.0, 19.5, 23.5)
abl = []
for it in list(pool[1]):
    if it[0] == 'seg' and it[1] == 'DM_PHY':
        x1, y1, x2, y2, hw = it[2]
        cxm, cym = (x1 + x2) / 2, (y1 + y2) / 2
        if ABL_BOX[0] < cxm < ABL_BOX[1] and ABL_BOX[2] < cym < ABL_BOX[3]:
            abl.append(it)
print(f'DM_PHY In2 segs in box: {len(abl)}', flush=True)
for it in abl:
    print(f'   ablate {L.fmt_it(it)}', flush=True)
ends = set()
for it in abl:
    pool[1].remove(it)
    RIP_ADD.setdefault('DM_PHY', []).append(
        [it[0], it[1], list(it[2]), it[3]])
    ends.add((R2(it[2][0]), R2(it[2][1])))
    ends.add((R2(it[2][2]), R2(it[2][3])))
# severed endpoints = endpoints not shared by 2 ablated segs and not
# endpoints of remaining DM_PHY segs... identify: endpoints whose
# point still touches remaining DM_PHY copper
remaining_pts = set()
for it in pool[1]:
    if it[0] == 'seg' and it[1] == 'DM_PHY':
        remaining_pts.add((R2(it[2][0]), R2(it[2][1])))
        remaining_pts.add((R2(it[2][2]), R2(it[2][3])))
    if it[0] == 'via' and it[1] == 'DM_PHY':
        remaining_pts.add((R2(it[2][0]), R2(it[2][1])))
severed = sorted(e for e in ends if e in remaining_pts)
print(f'severed endpoints touching remaining copper: {severed}',
      flush=True)
dm_mid = frag_report('DM_PHY', (60, 82, -4, 32))

# 6. XO dip
print('=== XO F dip (DM_PHY span ablated) ===', flush=True)
a_dip = make_astar((66.0, 76.0, 16.5, 27.5), step=0.025)
J = a_dip('XO', ((0,), 71.625, 25.625), (1, 68.875, 20.375), 0.10)
assert J is not None, 'DIP NONE even with DM_PHY span ablated'
print(f'dip: vias={J["vias"]} '
      f'runs={[(r["layer"], len(r["pts"])) for r in J["runs"]]}',
      flush=True)
assert try_emit('xo_bridge', J, 'XO', 0.10), 'dip gate refused'
xo = frag_report('XO', (63, 94, 7, 29))
assert len(xo) == 1, f'XO fragments {len(xo)} != 1'
print('XO BRIDGE CLOSED', flush=True)

# 7. DM_PHY re-lay between severed endpoints (t_aw10 variant search)
print('=== DM_PHY re-lay (variant search) ===', flush=True)
assert len(severed) == 2, f'severed endpoints {len(severed)} != 2'
(a, b) = severed
dm_hw = abl[0][2][4] if abl else 0.125

# dump the dip geometry per layer so the fence is on record
dipJ = JOURNEYS['xo_bridge']
for r in dipJ['runs']:
    pts = r['pts']
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    print(f"dip run L{r['layer']}: n={len(pts)} "
          f"x[{min(xs):.2f},{max(xs):.2f}] y[{min(ys):.2f},{max(ys):.2f}] "
          f"first={pts[0]} last={pts[-1]}", flush=True)
print(f'dip vias: {dipJ["vias"]}', flush=True)

def dm_try(tag, ast, start, goal, hw):
    Jv = ast('DM_PHY', start, goal, hw)
    print(f'  DM {tag}: {"FOUND" if Jv else "NONE"}', flush=True)
    return Jv

def compose(tag, legs):
    """legs: list of journeys; merge vias+runs."""
    vias, runs = [], []
    for Jv in legs:
        if Jv is None:
            return None
        vias += [list(v) for v in Jv['vias']]
        runs += Jv['runs']
    print(f'  DM {tag}: composed vias={vias} '
          f'runs={[(r["layer"], len(r["pts"])) for r in runs]}',
          flush=True)
    return dict(vias=vias, runs=runs)

Jdm = None
DM_BOX = (64.0, 79.0, 15.0, 29.0)
a_dm = make_astar(DM_BOX, step=0.025)
# V1: ML start, goal In2, both widths, wider box than t_aw9
for hw in (dm_hw, 0.10):
    Jdm = dm_try(f'V1 ML->In2 hw{hw}', a_dm, ((0, 1, 2), a[0], a[1]),
                 (1, b[0], b[1]), hw)
    if Jdm:
        dm_hw = hw
        break
# V2: goal on F / B
if Jdm is None:
    for gl in (0, 2):
        Jdm = dm_try(f'V2 ML->L{gl}', a_dm, ((0, 1, 2), a[0], a[1]),
                     (gl, b[0], b[1]), dm_hw)
        if Jdm:
            break
# V3: waypoint relays (east, south, north detours), ML legs
if Jdm is None:
    WPS = [('east', [(1, 74.75, 21.75), (1, 74.75, 20.25)]),
           ('eastF', [(0, 74.75, 21.75), (0, 74.75, 20.25)]),
           ('south', [(1, 73.75, 17.25), (1, 71.0, 17.25)]),
           ('north', [(1, 71.0, 25.75), (1, 74.5, 25.75)])]
    for tag, wps in WPS:
        legs = []
        cur = ((0, 1, 2), a[0], a[1])
        ok = True
        for (wl, wx, wy) in wps:
            Jv = a_dm('DM_PHY', cur, (wl, wx, wy), dm_hw)
            if Jv is None:
                ok = False
                break
            legs.append(Jv)
            cur = ((0, 1, 2), wx, wy)
        if ok:
            Jv = a_dm('DM_PHY', cur, (1, b[0], b[1]), dm_hw)
            if Jv is not None:
                legs.append(Jv)
                Jdm = compose(f'V3-{tag}', legs)
                break
        print(f'  DM V3-{tag}: NONE', flush=True)

if Jdm is None:
    # Branch B: remove the dip, re-lay DM on an east detour that keeps
    # the dip corridor (x<=73, y19..22) clear, then re-run the dip.
    print('=== Branch B: DM east detour first, dip second ===',
          flush=True)
    its = journey_items_dense(dipJ, 'XO', hw=0.10)
    for l in range(3):
        for it in its[l]:
            if it in NEW[l]:
                NEW[l].remove(it)
            if it in pool[l]:
                pool[l].remove(it)
    del JOURNEYS['xo_bridge']
    NET_HW.pop('xo_bridge', None)
    xo_mid = frag_report('XO', (63, 94, 7, 29))
    assert len(xo_mid) == 2, 'dip removal did not restore XO frags'
    WPS_B = [('eastIn2', [(1, 74.75, 22.5), (1, 75.25, 20.0)]),
             ('eastML', [(0, 74.75, 22.5), (2, 75.25, 20.0)]),
             ('farEast', [(1, 76.25, 23.0), (1, 76.25, 19.5)])]
    for tag, wps in WPS_B:
        legs = []
        cur = ((0, 1, 2), a[0], a[1])
        ok = True
        for (wl, wx, wy) in wps:
            Jv = a_dm('DM_PHY', cur, (wl, wx, wy), dm_hw)
            if Jv is None:
                ok = False
                break
            legs.append(Jv)
            cur = ((0, 1, 2), wx, wy)
        if ok:
            Jv = a_dm('DM_PHY', cur, (1, b[0], b[1]), dm_hw)
            if Jv is not None:
                legs.append(Jv)
                Jdm = compose(f'B-{tag}', legs)
                break
        print(f'  DM B-{tag}: NONE', flush=True)
    assert Jdm is not None, 'DM_PHY re-lay NONE in all variants + branch B'
    assert try_emit('dmphy_relay', Jdm, 'DM_PHY', dm_hw), \
        'DM_PHY gate refused (branch B)'
    NET_HW['dmphy_relay'] = ('DM_PHY', dm_hw)
    dm = frag_report('DM_PHY', (60, 82, -4, 32))
    assert len(dm) == len(base_dm), 'DM_PHY fragment count changed'
    print('DM_PHY RE-LAID (branch B detour)', flush=True)
    # re-run the dip against the detoured DM
    a_dip2 = make_astar((66.0, 76.0, 16.5, 27.5), step=0.025)
    J2 = a_dip2('XO', ((0,), 71.625, 25.625), (1, 68.875, 20.375), 0.10)
    assert J2 is not None, 'DIP NONE after DM branch-B detour'
    print(f'dip2: vias={J2["vias"]} '
          f'runs={[(r["layer"], len(r["pts"])) for r in J2["runs"]]}',
          flush=True)
    assert try_emit('xo_bridge', J2, 'XO', 0.10), 'dip2 gate refused'
    xo = frag_report('XO', (63, 94, 7, 29))
    assert len(xo) == 1, f'XO fragments {len(xo)} != 1 after dip2'
    print('XO BRIDGE CLOSED (branch B)', flush=True)
else:
    assert try_emit('dmphy_relay', Jdm, 'DM_PHY', dm_hw), \
        'DM_PHY gate refused'
    NET_HW['dmphy_relay'] = ('DM_PHY', dm_hw)
    dm = frag_report('DM_PHY', (60, 82, -4, 32))
    assert len(dm) == len(base_dm), 'DM_PHY fragment count changed'
    print('DM_PHY RE-LAID', flush=True)

# 8. REFCLK relay
print('=== REFCLK relay ===', flush=True)
ref_pad = new_pads['REFCLK'][0]
a_ref = make_astar((67.0, 78.5, 20.0, 34.0), step=0.025)
Jref = a_ref('REFCLK', ((1,), 71.125, 23.375),
             (0, ref_pad[0], ref_pad[1]), 0.10)
assert Jref is not None, 'REFCLK relay NONE'
assert try_emit('refclk_relay', Jref, 'REFCLK', 0.10), 'REFCLK gate refused'
ref_now = frag_report('REFCLK', (60, 80, 9, 42))
assert len(ref_now) == len(base_ref), 'REFCLK fragment count changed'
print('REFCLK RELAY CLOSED', flush=True)

# 9. +3V3D X2 links
print('=== +3V3D X2 links ===', flush=True)
a_v3 = make_astar((67.0, 78.5, 19.5, 34.0), step=0.025)
VIA_GOALS = [(0, 71.125, 24.375), (1, 71.125, 24.375),
             (2, 71.125, 24.375)]
def astar_goals(ast, net, start, goals, hw):
    for gg in goals:
        Jv = ast(net, start, gg, hw)
        if Jv is not None:
            return Jv, gg
    return None, None
for i, (px, py) in enumerate(new_pads['+3V3D']):
    goals = [(0, 70.45, 22.425), (0, 70.2, 24.575)] + VIA_GOALS
    Jv, gg = astar_goals(a_v3, '+3V3D', ((0,), px, py), goals, 0.125)
    assert Jv is not None, f'X2 +3V3D pad ({px},{py}) link NONE'
    assert try_emit(f'x2_v3a_{i}', Jv, '+3V3D', 0.125), 'X2 link refused'
    print(f'  X2 +3V3D pad ({px:.2f},{py:.2f}) linked via goal {gg}',
          flush=True)
frag_report('+3V3D', (60, 95, -8, 28))

# 10. join 2 (t_aw11 campaign: new goals / pad start / C28 move)
print('=== JOIN 2: +3V3D stub (t_aw11 campaign) ===', flush=True)
C28_MOVE = None
a_j2 = make_astar((68.0, 79.0, 18.0, 34.0), step=0.025)
link_pts = []
seen_lp = set()
for nm in ('x2_v3a_0', 'x2_v3a_1'):
    for r in JOURNEYS[nm]['runs']:
        for p in r['pts'][::10]:
            key = (r['layer'], R2(p[0]), R2(p[1]))
            if key not in seen_lp:
                seen_lp.add(key)
                link_pts.append(key)

def stub_goals(sx, sy):
    gs = ([(0, new_pads['+3V3D'][0][0], new_pads['+3V3D'][0][1]),
           (0, new_pads['+3V3D'][1][0], new_pads['+3V3D'][1][1]),
           (0, 76.525, 24.115), (0, 70.45, 22.425),
           (0, 70.2, 24.575)] + VIA_GOALS + link_pts)
    gs.sort(key=lambda gg: (gg[1] - sx) ** 2 + (gg[2] - sy) ** 2)
    return gs

def stub_try(tag, start):
    sx, sy = start[1], start[2]
    for hw in (0.125, 0.10, 0.15):
        for gg in stub_goals(sx, sy):
            Jv = a_j2('+3V3D', start, gg, hw)
            if Jv is not None:
                print(f'  stub ({tag}) hw={hw} goal={gg}: '
                      f'vias={Jv["vias"]} '
                      f'runs={[(r["layer"], len(r["pts"])) for r in Jv["runs"]]}',
                      flush=True)
                if try_emit('detour_+3V3D_stub', Jv, '+3V3D', hw):
                    return True
    print(f'  stub ({tag}): NONE at all widths/goals', flush=True)
    return False

join2 = stub_try('A-term', ((0,), 72.375, 21.125))
if not join2:
    print('=== JOIN 2-B: rip stub segs, start at C28 pad ===',
          flush=True)
    fr = fragments('+3V3D', (70.0, 78.0, 18.0, 26.0))
    stub_fr = None
    for f in fr:
        for it in f['items']:
            if it[0] == 'pad' and abs(C(it)[0] - 72.725) < 0.01 \
                    and abs(C(it)[1] - 20.5) < 0.01:
                stub_fr = f
    assert stub_fr is not None, 'stub fragment not found by pad'
    print('  stub fragment items: '
          f'{[L.fmt_it(it) for it in stub_fr["items"]]}', flush=True)
    for it in list(stub_fr['items']):
        if it[0] == 'seg':
            for l in range(3):
                if it in pool[l]:
                    pool[l].remove(it)
            RIP_ADD.setdefault('+3V3D', []).append(
                [it[0], it[1], list(it[2]), it[3]])
    join2 = stub_try('B-pad', ((0,), 72.725, 20.5))
if not join2:
    print('=== JOIN 2-C: C28 relocation scan ===', flush=True)
    for l in range(3):
        for it in list(pool[l]):
            if it[0] == 'pad' and \
                    (R2(it[2][0]), R2(it[2][1])) in \
                    {(72.725, 20.5), (74.275, 20.5)}:
                pool[l].remove(it)
    cands = []
    cx = 73.0
    while cx <= 75.01:
        cy = 19.25
        while cy <= 23.26:
            if not (abs(cx - 73.5) < 0.01 and abs(cy - 20.5) < 0.01):
                cands.append((cx, cy))
            cy += 0.25
        cx += 0.25
    cands.sort(key=lambda cc: (cc[0] - 73.5) ** 2 + (cc[1] - 20.5) ** 2)
    for (cx, cy) in cands:
        if cx + 1.0 > 76.0:
            continue
        p_v3 = (cx - 0.775, cy)
        p_gnd = (cx + 0.775, cy)
        m1, _o1 = pad_margin('+3V3D', p_v3[0], p_v3[1], 0.45, 0.475)
        m2, _o2 = pad_margin('GND', p_gnd[0], p_gnd[1], 0.45, 0.475)
        if m1 < -0.001 or m2 < -0.001:
            continue
        pad_v3 = ('pad', '+3V3D', (p_v3[0], p_v3[1], 0.45, 0.475, 0), 0.2)
        pad_gnd = ('pad', 'GND', (p_gnd[0], p_gnd[1], 0.45, 0.475, 0), 0.2)
        pool[0].append(pad_v3)
        pool[0].append(pad_gnd)
        ok = False
        for hw in (0.125, 0.10):
            for gg in stub_goals(p_v3[0], p_v3[1]):
                Jv = a_j2('+3V3D', ((0,), p_v3[0], p_v3[1]), gg, hw)
                if Jv is not None and \
                        try_emit('detour_+3V3D_stub', Jv, '+3V3D', hw):
                    print(f'  C28 -> ({cx:.2f},{cy:.2f}) pads '
                          f'{p_v3}/{p_gnd} margins {m1:+.3f}/{m2:+.3f} '
                          f'stub hw={hw} goal={gg}', flush=True)
                    ok = True
                    break
            if ok:
                break
        if ok:
            C28_MOVE = {'from': [73.5, 20.5], 'to': [cx, cy], 'rot': 0,
                        'pads': {'+3V3D': list(p_v3), 'GND': list(p_gnd)}}
            join2 = True
            break
        pool[0].remove(pad_v3)
        pool[0].remove(pad_gnd)
    if not join2:
        print('  C28 scan: no legal+routable centre', flush=True)
if not join2:
    print('=== JOIN 2 fence census (box 70.5,76.5,18.5,25.5) ===',
          flush=True)
    for l in range(3):
        for it in pool[l]:
            cc = C(it)
            if 70.5 <= cc[0] <= 76.5 and 18.5 <= cc[1] <= 25.5:
                print(f'   L{l} {L.fmt_it(it)}', flush=True)
assert join2, 'JOIN 2 FAILED all t_aw11 campaigns'
v3 = frag_report('+3V3D', (60, 95, -8, 28))
assert len(v3) == len(base_v3) - 1, \
    f'+3V3D fragments {len(base_v3)} -> {len(v3)}, expected -1'
print('JOIN 2 CLOSED', flush=True)

# 11. full gate
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

print('=== final fragments ===', flush=True)
frag_report('CAP_CLK', (60, 80, -2, 28))
frag_report('CAP_DATA', (60, 80, -2, 28))
frag_report('XO', (63, 94, 7, 29))
frag_report('RBIAS', (63, 80, 9, 26))
frag_report('+3V3D', (60, 95, -8, 28))
frag_report('REFCLK', (60, 80, 9, 42))
frag_report('DM_PHY', (60, 82, -4, 32))

RIP2_OUT = {net: [list(x) for x in lst] for net, lst in B['rip2'].items()}
for net, lst in RIP_ADD.items():
    RIP2_OUT.setdefault(net, []).extend(lst)
out = dict(journeys=JOURNEYS, fixed=B['fixed'], rip2=RIP2_OUT,
           extra=B['extra'], arrivals=B['arrivals'],
           clk_via=(70.2, 1.8), exit_via=(69.075, 2.8), u9_shift=1.25,
           moves={'X2': {'from': [71.5, 23.75], 'to': [CX, CY],
                         'rot': ROT}},
           shrinks={'C22': {'pads': [[72.02, 18.0], [72.98, 18.0]],
                            'size': [0.56, 0.62]},
                    'C24': {'pads': [[68.27, 18.0], [69.23, 18.0]],
                            'size': [0.56, 0.62]}},
           x2_pads={net: [list(p) for p in ps]
                    for net, ps in new_pads.items()})
if C28_MOVE:
    out['moves']['C28'] = C28_MOVE
json.dump(out, open('scratch/work/aw/build_aw1.json', 'w'), indent=1)
print('saved build_aw1.json', flush=True)
print('H5 v3 MODEL COMPLETE', flush=True)

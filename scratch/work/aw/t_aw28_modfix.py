"""t_aw28: model fixes on the t_aw18 end state.
Replay cache + t_aw18 mutations (stub rip, C28 0402 pads, stub emit),
then:
 M0 TMP_ALERT fixed vertical x65.7 -> x65.45 (short vs shifted U9 pads)
 M1 SDA fixed via (69.05,2.05) -> (69.05,2.45); hop journey re-run
    (PG_3V3 B staircase clearance)
 M2 RBIAS: replace dive-via+B-hop ride with a direct In2 leg to the
    existing via (69.625,20.625) (hole_near_hole vs that via)
 M3 SCL bridge: In2 (67.875,5.125) -> fixed via (69.35,1.4)
    (W chain orphaned by the au71 diag rip)
Manifest rip2 additions: REFCLK staircase seg, XO B spur chain (8).
Saves build_aw1.json (backup build_aw1_v1.json) + state_aw2.pkl."""
import wx
_app = wx.App(False)
import sys, json, pickle, copy
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'aw28'}
src = open('scratch/work/au/t_au97_phase2y.py').read()
exec(src.split("# 1. RBIAS tail re-lay")[0], g)
st = pickle.load(open('scratch/work/aw/state_aw.pkl', 'rb'))
_ns = {id(g): g}
for _fn in (g['fragments'], g['item_margin'], g['make_astar'],
            g['try_emit'], g['journey_items_dense']):
    _ns[id(_fn.__globals__)] = _fn.__globals__
for _d in _ns.values():
    _d['pool'] = st['pool']
    _d['NEW'] = st['NEW']
    _d['JOURNEYS'] = st['JOURNEYS']
    _d['NET_HW'] = st['NET_HW']
pool = st['pool']
NEW = st['NEW']
JOURNEYS = st['JOURNEYS']
NET_HW = st['NET_HW']
B = json.load(open('scratch/work/aw/build_aw1.json'))
RIP_ADD = st['RIP_ADD']
fragments = g['fragments']
make_astar = g['make_astar']
journey_items_dense = g['journey_items_dense']
item_margin = g['item_margin']
try_emit = g['try_emit']
C = g['C']
R2 = lambda v: round(v, 3)


def frag_report(net, box):
    fr = fragments(net, box)
    print(f'fragments({net}) = {len(fr)} sizes '
          f'{sorted((len(f["items"]) for f in fr), reverse=True)}',
          flush=True)
    return fr


def rip_journey(name):
    net, hw = NET_HW[name]
    J = JOURNEYS[name]
    its = journey_items_dense(J, net, hw=hw)
    n = 0
    for l in range(3):
        for it in its[l]:
            if it in pool[l]:
                pool[l].remove(it)
                n += 1
            if it in NEW[l]:
                NEW[l].remove(it)
    del JOURNEYS[name]
    print(f'ripped journey {name}: {n} items', flush=True)
    return J


# ---------- replay t_aw18 mutations ----------
fr = fragments('+3V3D', (70.0, 78.0, 18.0, 26.0))
stub_fr = None
for f in fr:
    for (ll, it) in f['items']:
        if it[0] == 'pad' and abs(C(it)[0] - 72.725) < 0.01 \
                and abs(C(it)[1] - 20.5) < 0.01:
            stub_fr = f
assert stub_fr is not None
for (ll, it) in list(stub_fr['items']):
    if it[0] == 'seg':
        if it in pool[ll]:
            pool[ll].remove(it)
        RIP_ADD.setdefault('+3V3D', []).append(
            [it[0], it[1], list(it[2]), it[3]])
for l in range(3):
    for it in list(pool[l]):
        if it[0] == 'pad' and (R2(it[2][0]), R2(it[2][1])) in \
                {(72.725, 20.5), (74.275, 20.5)}:
            pool[l].remove(it)
pool[0].append(('pad', '+3V3D', (72.77, 20.75, 0.28, 0.31, 0), 0.2))
pool[0].append(('pad', 'GND', (73.73, 20.75, 0.28, 0.31, 0), 0.2))
NET_HW['detour_+3V3D_stub'] = ('+3V3D', 0.125)
for _k, _v in {'rbias_relay': ('RBIAS', 0.125),
               'xo_bridge': ('XO', 0.10),
               'dmphy_relay': ('DM_PHY', 0.10),
               'refclk_relay': ('REFCLK', 0.10),
               'hop': ('I2C_SDA', 0.125)}.items():
    NET_HW.setdefault(_k, _v)
assert try_emit('detour_+3V3D_stub', B['journeys']['detour_+3V3D_stub'],
                '+3V3D', NET_HW['detour_+3V3D_stub'][1]), 'stub replay'
print('t_aw18 state replayed', flush=True)
assert len(frag_report('XO', (63, 94, 7, 29))) == 1
v3 = frag_report('+3V3D', (55, 97, -12, 40))
assert len(v3) == 4, v3

# ---------- M0: TMP_ALERT x65.7 -> x65.45 ----------
TMP_MAP = {
    (65.7, 3.15, 65.7, 2.2): (65.45, 3.15, 65.45, 2.2),
    (65.7, 2.2, 65.7, -2.6): (65.45, 2.2, 65.45, -2.6),
    (65.95, 3.35, 65.7, 3.15): (65.95, 3.35, 65.45, 3.15),
    (65.7, -2.6, 66.125, -3.125): (65.45, -2.6, 66.125, -3.125),
}
moved = 0
for l in range(3):
    for i, it in enumerate(pool[l]):
        if it[0] == 'seg' and it[1] == 'TMP_ALERT':
            key = tuple(R2(v) for v in it[2][:4])
            if key in TMP_MAP:
                ng = TMP_MAP[key] + (it[2][4],)
                pool[l][i] = ('seg', 'TMP_ALERT', ng, it[3])
                moved += 1
print(f'M0 pool segs moved: {moved}', flush=True)
assert moved == 4
fmoved = 0
for itj in B['fixed']['0']:
    if itj[0] == 'seg' and itj[1] == 'TMP_ALERT':
        key = tuple(R2(v) for v in itj[2][:4])
        if key in TMP_MAP:
            itj[2] = list(TMP_MAP[key]) + [itj[2][4]]
            fmoved += 1
print(f'M0 manifest fixed segs moved: {fmoved}', flush=True)
assert fmoved == 4
for l in range(3):
    for it in pool[l]:
        if it[0] == 'seg' and it[1] == 'TMP_ALERT' and \
                abs(it[2][0] - 65.45) < 0.01:
            m = item_margin(l, it, pool[l])
            print(f'  TMP seg {tuple(R2(v) for v in it[2][:4])} '
                  f'margin {m:+.3f}', flush=True)
            assert m >= -0.001

# ---------- M1: PG_3V3 B tail re-lay (SDA via stays at (69.05,2.05);
# the DRC clearance pair is PG track vs that via, actual 0.0846 -
# the binding feature is the staircase joint (68.625,1.875), 0.4596
# from the via vs 0.575 required. SDA via has NO legal alternative
# site: exit-via disc + clk_exit seg band + SCL via disc + PG band
# pack the pocket (t_aw31 probe). Re-lay PG's staircase tail +
# south vertical on B by A* - gate-legal by construction.) ----------
PG_RIP = [(68.375, 2.125, 68.625, 1.875), (68.625, 1.875, 68.625, -4.375)]
nrip = 0
for (x1, y1, x2, y2) in PG_RIP:
    for it in list(pool[2]):
        if it[0] == 'seg' and it[1] == 'PG_3V3' and \
                abs(it[2][0] - x1) < 0.01 and abs(it[2][1] - y1) < 0.01 \
                and abs(it[2][2] - x2) < 0.01 and \
                abs(it[2][3] - y2) < 0.01:
            pool[2].remove(it)
            nrip += 1
            B['rip2']['PG_3V3'].append(
                ['seg', 'PG_3V3', [x1, y1, x2, y2, 0.125], 0.2])
print(f'M1 PG pool segs ripped: {nrip}', flush=True)
assert nrip == 2
a_pg = make_astar((66.5, 70.5, -5.5, 3.2), step=0.025)
Jpg = a_pg('PG_3V3', ((2,), 68.375, 2.125), (2, 68.625, -4.375), 0.125,
           layer_lock=(False, False, True))
assert Jpg is not None, 'PG re-lay NONE'
NET_HW['pg_fix'] = ('PG_3V3', 0.125)
assert try_emit('pg_fix', Jpg, 'PG_3V3', 0.125), 'PG re-lay gate refused'
B['journeys']['pg_fix'] = Jpg
print('M1 PG tail re-laid (SDA via unmoved)', flush=True)

# ---------- M2: RBIAS direct In2 leg ----------
old_rb = rip_journey('rbias_relay')
a_rb = make_astar((67.0, 75.5, 10.5, 22.5), step=0.025)
Jd = a_rb('RBIAS', ((1,), 73.875, 11.625), (1, 69.625, 20.625), 0.125,
          layer_lock=(False, True, False))
if Jd is not None and try_emit('rbias_relay', Jd, 'RBIAS', 0.125):
    B['journeys']['rbias_relay'] = Jd
    print('M2 RBIAS direct In2 leg CLOSED (no dive via, no B hop)',
          flush=True)
else:
    print('M2 direct leg FAILED - restoring composed ride', flush=True)
    assert try_emit('rbias_relay', old_rb, 'RBIAS', 0.125)
    B['journeys']['rbias_relay'] = old_rb
rb = frag_report('RBIAS', (63, 80, 9, 26))
assert len(rb) == 1

# ---------- M3: SCL bridge ----------
# W chain's true E end is (66.875,6.75) - the (67.875,5.125) joint
# seg was ripped in the model AND on the board (t_aw33 forensics).
# data_entry's In2 diagonal + clk9's B diagonal fence the direct
# line; ML A* with layer/goal variants decides the crossing.
scl_before = frag_report('I2C_SCL', (60, 78, -6, 14))
# M3-pre: dip data_entry S. Rip it, fence its old In2 centreline
# (fat virtual segs, middle 70%) plus a parallel N fence, re-run
# In2-locked between its fixed endpoints, re-emit.
old_de = rip_journey('data_entry')
pts = old_de['runs'][0]['pts']
n = len(pts)
lo, hi = n // 7, n - n // 7
obs = []
for i in range(lo, hi - 1):
    (x1, y1), (x2, y2) = pts[i], pts[i + 1]
    it = ('seg', '__BLOCK__', (x1, y1, x2, y2, 0.45), 0.2)
    pool[1].append(it)
    obs.append(it)
for (x1, y1, x2, y2) in [(69.0, 4.55, 66.0, 7.35), (66.0, 7.35, 64.2, 6.9)]:
    it = ('seg', '__BLOCK__', (x1, y1, x2, y2, 0.3), 0.2)
    pool[1].append(it)
    obs.append(it)
a_de = make_astar((62.0, 72.0, -2.0, 14.0), step=0.025)
Jde = a_de('CAP_DATA', ((1,), 69.9, 3.175), (1, 63.85, 6.3), 0.1,
           layer_lock=(False, True, False))
if Jde is None:
    Jde = a_de('CAP_DATA', ((0, 1, 2), 69.9, 3.175), (1, 63.85, 6.3),
               0.1)
    print('M3-pre In2 dip NONE; ML dip: '
          f'{"FOUND" if Jde else "NONE"}', flush=True)
for it in obs:
    pool[1].remove(it)
bridge_ok = False
if Jde is not None and try_emit('data_entry', Jde, 'CAP_DATA', 0.1):
    B['journeys']['data_entry'] = Jde
    print('M3-pre data_entry dipped', flush=True)
    cd = frag_report('CAP_DATA', (58, 80, -4, 30))
    assert len(cd) == 3, 'CAP_DATA fragment count changed by the dip'
    a_sc = make_astar((62.0, 72.0, -2.0, 14.0), step=0.025)
    scl_hw = 0.1
    Jb = None
    for start in ((66.875, 6.75), (69.625, 12.625)):
        for goal in ((1, 69.35, 1.4), (2, 69.35, 1.4),
                     (0, 69.35, 1.4)):
            Jb = a_sc('I2C_SCL', ((0, 1, 2), start[0], start[1]),
                      goal, scl_hw)
            print(f'M3 ML start {start} goal {goal}: '
                  f'{"FOUND" if Jb else "NONE"}', flush=True)
            if Jb is not None:
                break
        if Jb is not None:
            break
    if Jb is not None:
        NET_HW['scl_bridge'] = ('I2C_SCL', scl_hw)
        if try_emit('scl_bridge', Jb, 'I2C_SCL', scl_hw):
            B['journeys']['scl_bridge'] = Jb
            scl_after = frag_report('I2C_SCL', (60, 78, -6, 14))
            assert len(scl_after) == len(scl_before) - 1, \
                'bridge did not merge the W chain fragment'
            bridge_ok = True
            print('M3 SCL bridge CLOSED', flush=True)
if not bridge_ok:
    # SCL bridge stays OPEN (full forensics: t_aw33/34/35/36/37 +
    # DISTRICT-STATUS-aw.md). Restore data_entry verbatim so the
    # manifest carries zero gratuitous change for the open item.
    if 'data_entry' in JOURNEYS:
        rip_journey('data_entry')
    assert try_emit('data_entry', old_de, 'CAP_DATA', 0.1), \
        'data_entry restore gate'
    B['journeys']['data_entry'] = old_de
    print('M3 SCL bridge OPEN - manifest saves without scl_bridge',
          flush=True)

# ---------- manifest rip2 additions ----------
B['rip2']['REFCLK'].append(
    ['seg', 'REFCLK', [71.125, 23.375, 71.875, 23.375, 0.1], 0.2])
chain = [(71.875, 19.625, 72.125, 19.875), (72.125, 19.875, 72.375, 20.125),
         (72.375, 20.125, 72.625, 20.375), (72.625, 20.375, 72.625, 24.625),
         (72.625, 24.625, 72.375, 24.875), (72.375, 24.875, 72.125, 25.125),
         (72.125, 25.125, 71.875, 25.375), (71.875, 25.375, 71.625, 25.625)]
for (x1, y1, x2, y2) in chain:
    B['rip2']['XO'].append(['seg', 'XO', [x1, y1, x2, y2, 0.125], 0.2])
print('rip2 additions recorded', flush=True)

# ---------- final fragment state ----------
frag_report('CAP_CLK', (58, 80, -4, 30))
frag_report('CAP_DATA', (58, 80, -4, 30))
frag_report('+3V3D', (55, 97, -12, 40))
frag_report('+3V3A', (60, 97, -12, 30))

import shutil
shutil.copy('scratch/work/aw/build_aw1.json',
            'scratch/work/aw/build_aw1_v1.json')
json.dump(B, open('scratch/work/aw/build_aw1.json', 'w'))
st2 = {'pool': pool, 'NEW': NEW, 'JOURNEYS': JOURNEYS,
       'NET_HW': {k: tuple(v) for k, v in NET_HW.items()}, 'B': B,
       'RIP_ADD': RIP_ADD, 'new_pads': st['new_pads']}
pickle.dump(st2, open('scratch/work/aw/state_aw2.pkl', 'wb'))
print('SAVED build_aw1.json (v2) + state_aw2.pkl', flush=True)
print('T_AW28 MODFIX COMPLETE', flush=True)

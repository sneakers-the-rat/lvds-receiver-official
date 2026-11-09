"""t_aw19: build exp241 from exp241esc + build_aw1.json.
Order: netcodes -> au71 RIPS predicates (seg/via only) -> rip2
(rounded match, victim-asserted) -> footprint ops (U9 -1.25x,
X2 -> (75.75,32.25), C22/C24/C28 -> C_0402_1005Metric) -> emit
fixed + extra + journeys + clk_via -> zone refill -> save ->
reload census diff (expected vs actual) + pad readback asserts."""
import wx
_app = wx.App(False)
import pcbnew, json, sys
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'scratch/work/au')
sys.path.insert(0, 'hw')
import t_ai_lib as L
import t_au1_lib as U
C = U.item_centre

SRC = 'hw/pdlvds_rx.exp241esc.kicad_pcb'
OUT = 'hw/pdlvds_rx.exp241.kicad_pcb'
LAY = {0: pcbnew.F_Cu, 1: pcbnew.In2_Cu, 2: pcbnew.B_Cu}
R2 = lambda v: round(v, 3)
_DEAD = []
board = pcbnew.LoadBoard(SRC)
B = json.load(open('scratch/work/aw/build_aw1.json'))

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
          'detour_+3V3D_L0': ('+3V3D', 0.15),
          'detour_+3V3D_L1': ('+3V3D', 0.15),
          'detour_+3V3D_L2': ('+3V3D', 0.15),
          'detour_+3V3D_L3': ('+3V3D', 0.15),
          'detour_XO_1': ('XO', 0.10), 'detour_XO_2': ('XO', 0.10),
          'dir_dive': ('ULPI_DIR', 0.10),
          'hop': ('I2C_SDA', 0.125),
          'scl_ffan': ('I2C_SCL', 0.10),
          # aw additions
          'rbias_relay': ('RBIAS', 0.125), 'xo_bridge': ('XO', 0.10),
          'dmphy_relay': ('DM_PHY', 0.10),
          'refclk_relay': ('REFCLK', 0.10),
          'x2_v3a_0': ('+3V3D', 0.125), 'x2_v3a_1': ('+3V3D', 0.125),
          'detour_+3V3D_stub': ('+3V3D', 0.125),
          'detour_+3V3D_4': ('+3V3D', 0.15),
          'detour_+3V3D_5': ('+3V3D', 0.15)}

def census(b):
    c = {}
    for tr in b.GetTracks():
        c[tr.GetNetname()] = c.get(tr.GetNetname(), 0) + 1
    return c

before = census(board)
print('tracks before:', sum(before.values()), flush=True)

# netcodes BEFORE any removal
nets = set(B['rip2'].keys())
for v in NET_HW.values():
    nets.add(v[0])
for lst in B['fixed'].values():
    for e in lst:
        nets.add(e[1])
for e in B['extra']:
    nets.add(e[2])
nets.add('CAP_CLK')
codes = {}
for n in nets:
    codes[n] = board.GetNetcodeFromNetname(n)
    assert codes[n] > 0, f'netcode missing for {n}'
print(f'netcodes captured: {len(codes)}', flush=True)

def track_items():
    out = []
    for t in board.GetTracks():
        net = t.GetNetname()
        clr = L.netclass(net)[1] if net else 0.2
        if isinstance(t, pcbnew.PCB_VIA):
            x, y = pcbnew.ToMM(t.GetPosition())
            r = pcbnew.ToMM(t.GetWidth()) / 2
            for li in range(3):
                out.append((li, ('via', net, (x, y, r), clr), t))
        else:
            if t.GetLayer() not in L.LAYERS_K:
                continue
            li = L.LAYERS_K.index(t.GetLayer())
            a = pcbnew.ToMM(t.GetStart())
            b = pcbnew.ToMM(t.GetEnd())
            w = pcbnew.ToMM(t.GetWidth())
            out.append((li, ('seg', net,
                             (a[0], a[1], b[0], b[1], w / 2), clr), t))
    return out

def near(it, x, y, tol=0.01):
    c = C(it)
    return abs(c[0] - x) < tol and abs(c[1] - y) < tol

DIAG_ENDS = {(67.875, 5.125), (69.375, 1.375), (68.875, 1.625)}
PREDS = [
    ('SCL via 69.375,1.375',
     lambda l, it: it[0] == 'via' and it[1] == 'I2C_SCL'
     and near(it, 69.375, 1.375)),
    ('SCL F segs pocket',
     lambda l, it: l == 0 and it[1] == 'I2C_SCL' and it[0] == 'seg'
     and 66.8 < C(it)[0] < 69.6 and 1.0 < C(it)[1] < 2.2),
    ('SCL In2 diag ends',
     lambda l, it: l == 1 and it[1] == 'I2C_SCL' and it[0] == 'seg'
     and ((round(it[2][0], 3), round(it[2][1], 3)) in DIAG_ENDS
          or (round(it[2][2], 3), round(it[2][3], 3)) in DIAG_ENDS)),
    ('SDA via 69.320,2.140',
     lambda l, it: it[0] == 'via' and it[1] == 'I2C_SDA'
     and near(it, 69.320, 2.140)),
    ('GND F seg end 68.25,3.5',
     lambda l, it: l == 0 and it[1] == 'GND' and it[0] == 'seg'
     and ((abs(it[2][0] - 68.25) < 0.01 and abs(it[2][1] - 3.5) < 0.01)
          or (abs(it[2][2] - 68.25) < 0.01
              and abs(it[2][3] - 3.5) < 0.01))),
    ('TMP_ALERT F segs W',
     lambda l, it: l == 0 and it[1] == 'TMP_ALERT' and it[0] == 'seg'
     and C(it)[0] < 67.3 and C(it)[1] > -3.2),
    ('+3V3A F seg 69.225,2.75',
     lambda l, it: l == 0 and it[1] == '+3V3A' and it[0] == 'seg'
     and abs(it[2][0] - 69.225) < 0.01 and abs(it[2][1] - 2.75) < 0.01
     and abs(it[2][2] - 69.475) < 0.01 and abs(it[2][3] - 2.75) < 0.01),
    ('CAP_CLK via esc 70.020,1.830',
     lambda l, it: it[0] == 'via' and it[1] == 'CAP_CLK'
     and near(it, 70.020, 1.830)),
    ('CAP_CLK F seg esc approach',
     lambda l, it: l == 0 and it[1] == 'CAP_CLK' and it[0] == 'seg'
     and C(it)[0] > 69.8 and C(it)[1] < 2.2),
    ('SDA In2 frag E',
     lambda l, it: l == 1 and it[1] == 'I2C_SDA' and it[0] == 'seg'
     and it[2][0] >= 71.1 and it[2][2] >= 71.1
     and 1.8 < it[2][1] < 4.2 and 1.8 < it[2][3] < 4.2),
]
items = track_items()
ripped = {}
pred_victims = []
pred_seen = set()
for name, pred in PREDS:
    vs = {}
    for (l, it, t) in items:
        if pred(l, it):
            vs[id(t)] = t
    print(f'predicate {name}: {len(vs)} victims', flush=True)
    for t in vs.values():
        if id(t) not in pred_seen:
            pred_seen.add(id(t))
            pred_victims.append(t)
            ripped[t.GetNetname()] = ripped.get(t.GetNetname(), 0) + 1
            _DEAD.append(t)
for t in pred_victims:
    board.Remove(t)
print(f'predicate rips removed: {len(pred_victims)}', flush=True)

# rip2 (rounded match)
items = track_items()
rip2_victims = []
rip2_seen = set()
for net, lst in B['rip2'].items():
    via_groups = {}
    for e in lst:
        kind, enet, geo = e[0], e[1], e[2]
        assert enet == net
        if kind == 'via':
            via_groups.setdefault((R2(geo[0]), R2(geo[1])), 0)
            via_groups[(R2(geo[0]), R2(geo[1]))] += 1
            continue
        key = tuple(sorted([(R2(geo[0]), R2(geo[1])),
                            (R2(geo[2]), R2(geo[3]))]))
        hits = []
        for (l, it, t) in items:
            if it[0] != 'seg' or it[1] != net or id(t) in rip2_seen:
                continue
            k2 = tuple(sorted([(R2(it[2][0]), R2(it[2][1])),
                               (R2(it[2][2]), R2(it[2][3]))]))
            if k2 == key:
                hits.append(t)
        assert len(hits) == 1, \
            f'rip2 seg {net} {geo}: {len(hits)} victims'
        rip2_seen.add(id(hits[0]))
        rip2_victims.append(hits[0])
        ripped[net] = ripped.get(net, 0) + 1
        _DEAD.append(hits[0])
    for (cx, cy), cnt in via_groups.items():
        hits = []
        for (l, it, t) in items:
            if it[0] != 'via' or it[1] != net or id(t) in rip2_seen:
                continue
            if (R2(it[2][0]), R2(it[2][1])) == (cx, cy) \
                    and all(h is not t for h in hits):
                hits.append(t)
        assert len(hits) == 1, \
            f'rip2 via {net} ({cx},{cy}) x{cnt}: {len(hits)} victims'
        rip2_seen.add(id(hits[0]))
        rip2_victims.append(hits[0])
        ripped[net] = ripped.get(net, 0) + 1
        _DEAD.append(hits[0])
for t in rip2_victims:
    board.Remove(t)
print(f'rip2 removed: {len(rip2_victims)} board items', flush=True)

# footprint ops
def get_fp(ref):
    for fp in board.GetFootprints():
        if fp.GetReference() == ref:
            return fp
    raise AssertionError(f'footprint {ref} not found')

u9 = get_fp('U9')
p = u9.GetPosition()
u9.SetPosition(pcbnew.VECTOR2I(p.x - pcbnew.FromMM(1.25), p.y))
print(f'U9 moved to {pcbnew.ToMM(u9.GetPosition())}', flush=True)

x2 = get_fp('X2')
x2.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(75.75),
                               pcbnew.FromMM(32.25)))
x2.SetOrientationDegrees(0)
print('X2 moved to (75.75,32.25)', flush=True)

def swap_0402(ref, centre):
    old = get_fp(ref)
    netmap = {}
    for pd in old.Pads():
        netmap[pd.GetNumber()] = pd.GetNet()
    new = pcbnew.FootprintLoad(
        '/usr/share/kicad/footprints/Capacitor_SMD.pretty',
        'C_0402_1005Metric')
    assert new, f'cannot load 0402 for {ref}'
    new.SetParent(board)
    new.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(centre[0]),
                                    pcbnew.FromMM(centre[1])))
    new.SetOrientation(old.GetOrientation())
    new.SetReference(old.GetReference())
    new.SetValue(old.GetValue())
    for pd in new.Pads():
        if pd.GetNumber() in netmap:
            pd.SetNet(netmap[pd.GetNumber()])
    board.Add(new)
    board.Remove(old)
    _DEAD.append(old)
    got = {}
    for pd in new.Pads():
        got[pd.GetNetname()] = tuple(
            round(v, 3) for v in pcbnew.ToMM(pd.GetPosition()))
    print(f'{ref} swapped to 0402 at {centre}: pads {got}', flush=True)
    return got

g22 = swap_0402('C22', (72.5, 18.0))
assert g22.get('PHY_1V8') == (72.02, 18.0), g22
assert g22.get('GND') == (72.98, 18.0), g22
g24 = swap_0402('C24', (68.75, 18.0))
assert g24.get('+3V3A') == (68.27, 18.0), g24
assert g24.get('GND') == (69.23, 18.0), g24
g28 = swap_0402('C28', (73.25, 20.75))
assert g28.get('+3V3D') == (72.77, 20.75), g28
assert g28.get('GND') == (73.73, 20.75), g28

# verify X2 pads vs manifest
want = {}
for net, ps in B['x2_pads'].items():
    for pp in ps:
        want[(round(pp[0], 3), round(pp[1], 3))] = net
got = {}
for pd in get_fp('X2').Pads():
    got[tuple(round(v, 3) for v in pcbnew.ToMM(pd.GetPosition()))] = \
        pd.GetNetname()
assert got == want, f'X2 pad readback mismatch: {got} vs {want}'
print('X2 pad readback matches manifest', flush=True)

# emits
emitted = {}
def add_seg(net, li, a, b, w):
    t = pcbnew.PCB_TRACK(board)
    t.SetNetCode(codes[net])
    t.SetLayer(LAY[li])
    t.SetWidth(pcbnew.FromMM(w))
    t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(a[0]),
                               pcbnew.FromMM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(b[0]),
                             pcbnew.FromMM(b[1])))
    board.Add(t)
    emitted[net] = emitted.get(net, 0) + 1

def add_via(net, x, y):
    v = pcbnew.PCB_VIA(board)
    v.SetNetCode(codes[net])
    v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x),
                                  pcbnew.FromMM(y)))
    v.SetWidth(pcbnew.FromMM(0.5))
    v.SetDrill(pcbnew.FromMM(0.3))
    board.Add(v)
    emitted[net] = emitted.get(net, 0) + 1

seen_vias = set()
def add_via_dedupe(net, x, y):
    key = (net, R2(x), R2(y))
    if key in seen_vias:
        return
    seen_vias.add(key)
    add_via(net, x, y)

for ls, lst in B['fixed'].items():
    li = int(ls)
    for e in lst:
        if e[0] == 'via':
            add_via_dedupe(e[1], e[2][0], e[2][1])
        else:
            add_seg(e[1], li, (e[2][0], e[2][1]), (e[2][2], e[2][3]),
                    2 * e[2][4])
for e in B['extra']:
    if e[1] == 'via':
        add_via_dedupe(e[2], e[3][0], e[3][1])
    else:
        add_seg(e[2], e[0], (e[3][0], e[3][1]), (e[3][2], e[3][3]),
                2 * e[3][4])
for name, J in B['journeys'].items():
    net, hw = NET_HW[name]
    for v in J['vias']:
        add_via_dedupe(net, v[0], v[1])
    for r in J['runs']:
        pts = r['pts']
        for i in range(len(pts) - 1):
            add_seg(net, r['layer'], pts[i], pts[i + 1], 2 * hw)
add_via_dedupe('CAP_CLK', B['clk_via'][0], B['clk_via'][1])
print(f'emitted tracks+vias: {sum(emitted.values())}', flush=True)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
board.Save(OUT)
print('saved', OUT, flush=True)

b2 = pcbnew.LoadBoard(OUT)
after = census(b2)
bad = 0
for n in sorted(set(before) | set(after)):
    exp = before.get(n, 0) - ripped.get(n, 0) + emitted.get(n, 0)
    if after.get(n, 0) != exp:
        print(f'CENSUS DIFF {n}: expected {exp}, actual '
              f'{after.get(n, 0)}', flush=True)
        bad += 1
print(f'census diffs: {bad}', flush=True)
assert bad == 0, 'reload census mismatch - investigate before DRC'
print('T_AW19 BUILD COMPLETE', flush=True)

import sys, json
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa

B = 'hw/pdlvds_rx.exp250.kicad_pcb'
b = pcbnew.LoadBoard(B)
MM = 1000000


def V(x, y):
    return pcbnew.VECTOR2I(int(round(x * MM)), int(round(y * MM)))


def mm(v):
    return (v.x / MM, v.y / MM)


D = json.load(open('scratch/work/ax/design214_ax252.json'))
FIX = json.load(open('scratch/work/ax/design251fix.json'))
C22C = FIX['c22_site']  # (cx, cy, rot)
NETS = ('ULPI_STP', 'XI', 'GND', 'PHY_1V8', 'I2C_SDA', 'HV_SHDN', 'PG_3V3')
nc = {n: b.GetNetcodeFromNetname(n) for n in NETS}
print('netcodes:', nc, flush=True)

F, I2, BK = pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu

# ---------------- C20 swap 0603 -> 0402 at (76.2,18.73) ----------------
old = None
for fp in b.GetFootprints():
    if fp.GetReference() == 'C20':
        old = fp
assert old is not None
netmap = {}
refpos = None
for p in old.Pads():
    netmap[p.GetNumber()] = p.GetNetname()
for f in old.Fields():
    if f.GetName() == 'Reference':
        refpos = mm(f.GetPosition())
print('C20 old pads:', netmap, 'refdes at', refpos, flush=True)
assert netmap == {'1': 'XI', '2': 'GND'}, netmap
new = pcbnew.FootprintLoad('/usr/share/kicad/footprints/Capacitor_SMD.pretty',
                           'C_0402_1005Metric')
new.SetPosition(V(76.2, 18.73))
new.SetOrientation(pcbnew.EDA_ANGLE(0, pcbnew.DEGREES_T))
new.SetReference('C20')
new.SetValue(old.GetValue())
b.Add(new)
b.Remove(old)
# nets AFTER Add (v1 bug: SetNetCode before Add did not stick)
for p in new.Pads():
    p.SetNetCode(nc[netmap[p.GetNumber()]])
for f in new.Fields():
    if f.GetName() == 'Reference' and refpos is not None:
        f.SetPosition(V(*refpos))
for p in new.Pads():
    print('C20 new pad', p.GetNumber(), p.GetNetname(), mm(p.GetPosition()),
          flush=True)
    assert p.GetNetname() == netmap[p.GetNumber()]

# ---------------- C22 move -> scan winner site ----------------
cx, cy, rot = C22C
c22pads = {}
for fp in b.GetFootprints():
    if fp.GetReference() == 'C22':
        fieldpos = {f.GetName(): mm(f.GetPosition()) for f in fp.Fields()}
        fp.SetPosition(V(cx, cy))
        if rot == 90:
            fp.SetOrientation(pcbnew.EDA_ANGLE(
                fp.GetOrientationDegrees() + 90, pcbnew.DEGREES_T))
        for p in fp.Pads():
            c22pads[p.GetNetname()] = mm(p.GetPosition())
            print('C22 pad', p.GetNumber(), p.GetNetname(),
                  mm(p.GetPosition()), flush=True)
# the scan's web must start on the PHY pad, wherever rotation put it
_w0 = FIX['c22_web']['runs'][0]['pts'][0]
_pp = c22pads['PHY_1V8']
assert abs(_w0[0] - _pp[0]) < 0.06 and abs(_w0[1] - _pp[1]) < 0.06, \
    ('C22 web start vs PHY pad', _w0, _pp)
print('C22 web start matches PHY pad at', _pp, flush=True)

# ---------------- rips (collect ALL victims first) ----------------
def isseg(t, net, a, bb_, layer):
    if not isinstance(t, pcbnew.PCB_TRACK) or isinstance(t, pcbnew.PCB_VIA):
        return False
    if t.GetNetname() != net or t.GetLayer() != layer:
        return False
    s, e = mm(t.GetStart()), mm(t.GetEnd())
    return ((abs(s[0] - a[0]) < 0.01 and abs(s[1] - a[1]) < 0.01
             and abs(e[0] - bb_[0]) < 0.01 and abs(e[1] - bb_[1]) < 0.01)
            or (abs(e[0] - a[0]) < 0.01 and abs(e[1] - a[1]) < 0.01
                and abs(s[0] - bb_[0]) < 0.01
                and abs(s[1] - bb_[1]) < 0.01))


def isvia(t, net, x, y):
    if not isinstance(t, pcbnew.PCB_VIA) or t.GetNetname() != net:
        return False
    p = mm(t.GetPosition())
    return abs(p[0] - x) < 0.01 and abs(p[1] - y) < 0.01


specs = [
    ('PHY B arm1', lambda t: isseg(t, 'PHY_1V8', (77.8, 16.2), (73.4, 16.2), BK), 1),
    ('PHY B arm2', lambda t: isseg(t, 'PHY_1V8', (73.4, 16.2), (72.9, 16.9), BK), 1),
    ('PHY B arm3', lambda t: isseg(t, 'PHY_1V8', (72.9, 16.9), (72.125, 17.625), BK), 1),
    ('PHY B arm4', lambda t: isseg(t, 'PHY_1V8', (72.125, 17.625), (71.375, 17.625), BK), 1),
    ('PHY F tail1', lambda t: isseg(t, 'PHY_1V8', (71.375, 17.625), (71.725, 17.75), F), 1),
    ('PHY F tail2', lambda t: isseg(t, 'PHY_1V8', (71.725, 17.75), (71.725, 18.0), F), 1),
    ('via PHY 71.375', lambda t: isvia(t, 'PHY_1V8', 71.375, 17.625), 1),
    ('via GND 76.487', lambda t: isvia(t, 'GND', 76.487, 9.139), 1),
    ('PHY loop1', lambda t: isseg(t, 'PHY_1V8', (77.35, 10.0), (76.8, 10.988), BK), 1),
    ('PHY loop2', lambda t: isseg(t, 'PHY_1V8', (77.869, 10.056), (77.35, 10.0), BK), 1),
    ('PHY loop3', lambda t: isseg(t, 'PHY_1V8', (76.8, 10.988), (76.8, 14.988), BK), 1),
    ('PHY loop4', lambda t: isseg(t, 'PHY_1V8', (76.8, 14.988), (77.8, 16.2), BK), 1),
    ('PHY stub F', lambda t: isseg(t, 'PHY_1V8', (77.25, 10.75), (77.869, 10.056), F), 1),
    ('via PHY 77.869', lambda t: isvia(t, 'PHY_1V8', 77.869, 10.056), 1),
    ('HV s01', lambda t: isseg(t, 'HV_SHDN', (69.875, -2.375), (70.125, -2.125), I2), 1),
    ('HV s02', lambda t: isseg(t, 'HV_SHDN', (70.125, -2.125), (70.7, -2.75), I2), 1),
    ('HV s03', lambda t: isseg(t, 'HV_SHDN', (69.875, -2.375), (69.625, -2.625), I2), 1),
    ('HV s04', lambda t: isseg(t, 'HV_SHDN', (69.625, -2.625), (69.375, -2.875), I2), 1),
    ('HV s05', lambda t: isseg(t, 'HV_SHDN', (69.375, -2.875), (69.125, -3.125), I2), 1),
    ('HV s06', lambda t: isseg(t, 'HV_SHDN', (69.125, -3.125), (68.875, -3.375), I2), 1),
    ('HV s07', lambda t: isseg(t, 'HV_SHDN', (68.875, -3.375), (68.875, -4.375), I2), 1),
    ('HV s08', lambda t: isseg(t, 'HV_SHDN', (68.875, -4.375), (68.625, -4.625), I2), 1),
    ('HV s09', lambda t: isseg(t, 'HV_SHDN', (68.625, -4.625), (68.375, -4.875), I2), 1),
    ('HV s10', lambda t: isseg(t, 'HV_SHDN', (68.375, -4.875), (68.125, -5.125), I2), 1),
    ('HV s11', lambda t: isseg(t, 'HV_SHDN', (68.125, -5.125), (68.125, -5.625), I2), 1),
    ('HV s12', lambda t: isseg(t, 'HV_SHDN', (68.125, -5.625), (68.04, -5.75), I2), 1),
    ('HV s13', lambda t: isseg(t, 'HV_SHDN', (68.04, -5.75), (68.04, -6.0), I2), 1),
]
rips = []
for name, pred, want in specs:
    v = [t for t in b.GetTracks() if pred(t)]
    print(f'{name}: {len(v)} victim(s), want {want}', flush=True)
    assert len(v) == want, name
    rips += v

sda = []
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA) or not isinstance(t, pcbnew.PCB_TRACK):
        continue
    if t.GetNetname() != 'I2C_SDA' or t.GetLayer() != BK:
        continue
    s, e = mm(t.GetStart()), mm(t.GetEnd())
    if all(69.8 <= p[0] <= 70.0 and -9.2 <= p[1] <= 0.9 for p in (s, e)):
        sda.append(t)
print('SDA B box victims:', len(sda), '(design pool items: 2)', flush=True)
rips += sda

pg = []
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA) or not isinstance(t, pcbnew.PCB_TRACK):
        continue
    if t.GetNetname() != 'PG_3V3' or t.GetLayer() != BK:
        continue
    s, e = mm(t.GetStart()), mm(t.GetEnd())
    if all(68.55 <= p[0] <= 69.45 and -5.13 <= p[1] <= 0.46 for p in (s, e)):
        pg.append(t)
print('PG B box victims:', len(pg), '(design pool items: 196)', flush=True)
assert len(pg) == 196, len(pg)
rips += pg

for t in rips:
    b.Remove(t)
print('total ripped:', len(rips), flush=True)

# ---------------- adds ----------------
def add_seg(net, layer, a, bb_, w=200000):
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(V(*a))
    t.SetEnd(V(*bb_))
    t.SetLayer(layer)
    t.SetWidth(w)
    t.SetNetCode(nc[net])
    b.Add(t)


def add_via(net, x, y):
    t = pcbnew.PCB_VIA(b)
    t.SetPosition(V(x, y))
    t.SetWidth(500000)
    t.SetDrill(300000)
    t.SetLayerPair(F, BK)
    t.SetViaType(pcbnew.VIATYPE_THROUGH)
    t.SetNetCode(nc[net])
    b.Add(t)


def add_journey(net, J, w=200000):
    n = 0
    for run in J['runs']:
        lay = (F, I2, BK)[run['layer']]
        pts = [tuple(p) for p in run['pts']]
        for a, bb_ in zip(pts, pts[1:]):
            add_seg(net, lay, a, bb_, w)
            n += 1
    for v in J['vias']:
        add_via(net, v[0], v[1])
    return n


# PHY_1V8 south loop re-lay (hw0.15, shifted); via nudged to (77.90,10.08)
add_seg('PHY_1V8', BK, (77.45, 10.1), (76.95, 11.05), 300000)
add_seg('PHY_1V8', BK, (76.95, 11.05), (76.95, 14.988), 300000)
add_seg('PHY_1V8', BK, (76.95, 14.988), (77.8, 16.2), 300000)
add_seg('PHY_1V8', F, (77.25, 10.75), (77.90, 10.08), 200000)
add_seg('PHY_1V8', BK, (77.90, 10.08), (77.45, 10.1), 300000)
add_via('PHY_1V8', 77.90, 10.08)
# C22 PHY feed web from the scan (F journey pad1 -> via (78.1,17.5))
print('C22 web segs', add_journey('PHY_1V8', FIX['c22_web'], 200000),
      flush=True)
# SDA B jog (hw0.125)
for a, bb_ in (((69.9, 0.82), (69.875, 0.625)),
               ((69.875, 0.625), (69.875, -1.3)),
               ((69.875, -1.3), (69.5, -1.675)),
               ((69.5, -1.675), (69.5, -3.0)),
               ((69.5, -3.0), (69.875, -3.375)),
               ((69.875, -3.375), (69.875, -9.125))):
    add_seg('I2C_SDA', BK, a, bb_, 250000)
print('HV journey segs', add_journey('HV_SHDN', D['hv_journey'], 250000),
      flush=True)
Jpg = json.loads(json.dumps(D['pg_journey']))
Jpg['runs'][-1]['pts'][-1] = [69.375, -5.125]
print('PG journey segs', add_journey('PG_3V3', Jpg, 250000), flush=True)
# STP F stub (t_ax147 verbatim) + dive via nudged to (76.065,17.96)
stub_pts = [(76.25, 16.45), (76.25, 16.5), (76.25, 16.55), (76.25, 16.6),
            (76.25, 16.65), (76.25, 16.7), (76.25, 16.75), (76.25, 16.8),
            (76.25, 16.85), (76.25, 16.9), (76.25, 16.95), (76.2, 17.0),
            (76.2, 17.05), (76.15, 17.1), (76.15, 17.15), (76.1, 17.2),
            (76.1, 17.25), (76.05, 17.3), (76.05, 17.35), (76.05, 17.4),
            (76.05, 17.45), (76.05, 17.5), (76.05, 17.55), (76.05, 17.6),
            (76.05, 17.65), (76.05, 17.7), (76.05, 17.75), (76.05, 17.8),
            (76.05, 17.85), (76.05, 17.9), (76.05, 17.95), (76.05, 18.0)]
for a, bb_ in zip(stub_pts, stub_pts[1:]):
    add_seg('ULPI_STP', F, a, bb_, 200000)
add_via('ULPI_STP', 76.065, 17.96)
# STP legs WITHOUT dedupe (v1 dedupe broke stage-joint endpoint
# coincidence -> DRC track_dangling at retraced joints)
tot = 0
for J in D['stp_legs']:
    tot += add_journey('ULPI_STP', J, 200000)
print('STP leg segs added:', tot, flush=True)

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save('hw/pdlvds_rx.exp251.kicad_pcb')
print('saved exp251 v2', flush=True)

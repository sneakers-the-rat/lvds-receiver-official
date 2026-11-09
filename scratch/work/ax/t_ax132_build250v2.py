import sys, json
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa

B = 'hw/pdlvds_rx.exp249.kicad_pcb'
b = pcbnew.LoadBoard(B)
MM = 1000000
def V(x, y):
    return pcbnew.VECTOR2I(int(round(x * MM)), int(round(y * MM)))
def mm(v):
    return (v.x / MM, v.y / MM)

D = json.load(open('scratch/work/ax/phy_design_ax131.json'))
nc = {n: b.GetNetcodeFromNetname(n)
      for n in ('PHY_1V8A', 'XO', '+3V3D', 'GND')}

# --- C16 move; C23 rotate + refdes move
for fp in b.GetFootprints():
    if fp.GetReference() == 'C16':
        fp.SetPosition(V(70.25, 13.0))
        fp.SetOrientation(pcbnew.EDA_ANGLE(180, pcbnew.DEGREES_T))
        for p in fp.Pads():
            print('C16 pad', p.GetNumber(), p.GetNetname(), mm(p.GetPosition()))
    if fp.GetReference() == 'C23':
        fp.SetOrientation(pcbnew.EDA_ANGLE(
            fp.GetOrientationDegrees() + 180, pcbnew.DEGREES_T))
        for p in fp.Pads():
            print('C23 pad', p.GetNumber(), p.GetNetname(), mm(p.GetPosition()))
        for f in fp.Fields():
            if f.GetName() == 'Reference':
                f.SetPosition(V(69.6, 17.2))
                print('C23 refdes -> (69.6,17.2)')

def isseg(t, net, a, bb_, layer):
    if not isinstance(t, pcbnew.PCB_TRACK) or isinstance(t, pcbnew.PCB_VIA):
        return False
    if t.GetNetname() != net or t.GetLayer() != layer:
        return False
    s, e = mm(t.GetStart()), mm(t.GetEnd())
    return ((abs(s[0]-a[0]) < 0.01 and abs(s[1]-a[1]) < 0.01
             and abs(e[0]-bb_[0]) < 0.01 and abs(e[1]-bb_[1]) < 0.01)
            or (abs(e[0]-a[0]) < 0.01 and abs(e[1]-a[1]) < 0.01
                and abs(s[0]-bb_[0]) < 0.01 and abs(s[1]-bb_[1]) < 0.01))
def isvia(t, net, x, y):
    if not isinstance(t, pcbnew.PCB_VIA) or t.GetNetname() != net:
        return False
    p = mm(t.GetPosition())
    return abs(p[0]-x) < 0.01 and abs(p[1]-y) < 0.01

F, I2, BK = pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu
specs = [
    ('seg +3V3D feed', lambda t: isseg(t, '+3V3D', (75.225, 9.75),
                                      (75.225, 9.5), F)),
    ('seg +3V3D twig', lambda t: isseg(t, '+3V3D', (75.225, 9.5),
                                      (74.875, 8.875), F)),
    ('via GND 71.8', lambda t: isvia(t, 'GND', 71.8, 14.9)),
    ('via XO notch', lambda t: isvia(t, 'XO', 76.0, 10.625)),
    ('seg XO B1', lambda t: isseg(t, 'XO', (76.0, 10.625),
                                  (74.125, 12.25), BK)),
    ('seg XO B2', lambda t: isseg(t, 'XO', (74.125, 12.25),
                                  (72.625, 12.25), BK)),
    ('seg XO F end', lambda t: isseg(t, 'XO', (76.5, 10.75),
                                     (76.0, 10.625), F)),
    ('via XO 72.625', lambda t: isvia(t, 'XO', 72.625, 12.25)),
    ('seg XO F vert', lambda t: isseg(t, 'XO', (72.625, 12.25),
                                      (72.625, 10.375), F)),
    ('seg +3V3D Bv1', lambda t: isseg(t, '+3V3D', (70.875, 15.875),
                                      (70.875, 15.125), BK)),
    ('seg +3V3D Bv2', lambda t: isseg(t, '+3V3D', (70.875, 15.125),
                                      (70.875, 14.125), BK)),
    ('seg +3V3D Bv3', lambda t: isseg(t, '+3V3D', (70.875, 14.125),
                                      (70.875, 12.625), BK)),
]
rips = []
for name, pred in specs:
    v = [t for t in b.GetTracks() if pred(t)]
    print(f'{name}: {len(v)} victim(s)')
    assert len(v) == 1, name
    rips += v
for t in rips:
    b.Remove(t)

for (x, y) in ((70.875, 12.625), (70.875, 15.875)):
    hit = [t for t in b.GetTracks() if isvia(t, '+3V3D', x, y)]
    assert len(hit) == 1
    hit[0].SetWidth(500000)
    hit[0].SetDrill(300000)
    print('resized +3V3D via', (x, y))

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
def add_journey(net, J):
    n = 0
    for run in J['runs']:
        lay = (F, I2, BK)[run['layer']]
        pts = [tuple(p) for p in run['pts']]
        for a, bb_ in zip(pts, pts[1:]):
            add_seg(net, lay, a, bb_)
            n += 1
    for v in J['vias']:
        add_via(net, v[0], v[1])
    return n

add_seg('+3V3D', F, (74.875, 8.875), (74.375, 8.125))
add_seg('+3V3D', BK, (70.875, 12.625), (70.875, 15.875))
add_seg('+3V3D', F, (71.025, 13.0), (70.875, 12.625))
print('XO journey segs', add_journey('XO', D['xo']))
add_seg('PHY_1V8A', F, (75.75, 11.5625), (75.72, 11.0))
add_seg('PHY_1V8A', F, (75.72, 11.0), (75.7375, 10.75))
add_via('PHY_1V8A', 75.7375, 10.75)
Bpts = [(75.7375, 10.75), (75.3, 11.35), (74.9, 11.75), (74.2, 12.25),
        (73.5, 12.55), (73.3, 12.2), (73.22, 11.94), (72.92, 11.62),
        (72.35, 11.65), (71.9, 11.95), (71.3, 12.1), (70.7, 11.85),
        (70.3, 12.15), (70.2, 12.5), (70.18, 12.75)]
for a, bb_ in zip(Bpts, Bpts[1:]):
    add_seg('PHY_1V8A', BK, a, bb_)
print('PHY tail segs', add_journey('PHY_1V8A', D['tail']))
add_via('PHY_1V8A', 71.48, 15.38)
add_seg('PHY_1V8A', F, (71.48, 15.38), (71.48, 15.15))
add_seg('PHY_1V8A', F, (71.48, 15.15), (71.525, 14.75))
print('GND journey segs', add_journey('GND', D['gnd']))

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save('hw/pdlvds_rx.exp250.kicad_pcb')
print('saved exp250 (v2)')

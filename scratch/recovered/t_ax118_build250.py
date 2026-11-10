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

D = json.load(open('scratch/work/ax/phy_design_ax117.json'))
nc = {n: b.GetNetcodeFromNetname(n)
      for n in ('PHY_1V8A', 'XO', '+3V3D', 'GND')}

# templates
vt = None
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA) and abs(t.GetWidth() - 500000) < 1000:
        vt = t
        break
print('via template w', vt.GetWidth(), 'drill', vt.GetDrill())
seg_t = {}
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_TRACK) and not isinstance(t, pcbnew.PCB_VIA):
        seg_t.setdefault(t.GetNetname(), t)

# --- C16 move (70.25,13.0) rot 180
c16 = None
for fp in b.GetFootprints():
    if fp.GetReference() == 'C16':
        c16 = fp
        break
print('C16 from', mm(c16.GetPosition()), 'orient',
      c16.GetOrientationDegrees())
c16.SetPosition(V(70.25, 13.0))
c16.SetOrientation(pcbnew.EDA_ANGLE(180, pcbnew.DEGREES_T))
for p in c16.Pads():
    print('  C16 pad', p.GetNumber(), p.GetNetname(), mm(p.GetPosition()))
# --- C23 rotate 180 in place
c23 = None
for fp in b.GetFootprints():
    if fp.GetReference() == 'C23':
        c23 = fp
        break
print('C23 from', mm(c23.GetPosition()), 'orient',
      c23.GetOrientationDegrees())
c23.SetOrientation(pcbnew.EDA_ANGLE(
    c23.GetOrientationDegrees() + 180, pcbnew.DEGREES_T))
for p in c23.Pads():
    print('  C23 pad', p.GetNumber(), p.GetNetname(), mm(p.GetPosition()))

# --- rips (collect all victims first)
def victims(pred):
    return [t for t in b.GetTracks() if pred(t)]
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
rips = []
rips += victims(lambda t: isseg(t, '+3V3D', (75.225, 9.75), (75.225, 9.5), F))
print('feed victims', len(rips[-1:]))
rips += victims(lambda t: isvia(t, 'GND', 71.8, 14.9))
rips += victims(lambda t: isvia(t, 'XO', 76.0, 10.625))
rips += victims(lambda t: isseg(t, 'XO', (76.0, 10.625), (74.125, 12.25), BK))
rips += victims(lambda t: isseg(t, 'XO', (74.125, 12.25), (72.625, 12.25), BK))
rips += victims(lambda t: isseg(t, 'XO', (76.5, 10.75), (76.0, 10.625), F))
for a, bb_ in (((70.875, 15.875), (70.875, 15.125)),
               ((70.875, 15.125), (70.875, 14.125)),
               ((70.875, 14.125), (70.875, 12.625))):
    v = victims(lambda t, a=a, bb_=bb_: isseg(t, '+3V3D', a, bb_, BK))
    print('B vert seg victims', len(v), a)
    rips += v
print('total rip victims:', len(rips))
for t in rips:
    b.Remove(t)

# --- via resizes
for (x, y) in ((70.875, 12.625), (70.875, 15.875)):
    hit = [t for t in b.GetTracks() if isvia(t, '+3V3D', x, y)]
    assert len(hit) == 1, (x, y, len(hit))
    hit[0].SetWidth(500000)
    hit[0].SetDrill(300000)
    print('resized +3V3D via', (x, y))

# --- adds
def add_seg(net, layer, a, bb_, w=200000):
    t = seg_t[net].Clone()
    t.SetStart(V(*a))
    t.SetEnd(V(*bb_))
    t.SetLayer(layer)
    t.SetWidth(w)
    t.SetNetCode(nc[net])
    b.Add(t)
def add_via(net, x, y):
    t = vt.Clone()
    t.SetPosition(V(x, y))
    t.SetNetCode(nc[net])
    b.Add(t)

add_seg('+3V3D', BK, (70.875, 12.625), (70.875, 15.875))
add_seg('+3V3D', F, (71.025, 13.0), (70.875, 12.625))
# XO journey
n = 0
for run in D['xo']['runs']:
    lay = (F, I2, BK)[run['layer']]
    pts = [tuple(p) for p in run['pts']]
    for a, bb_ in zip(pts, pts[1:]):
        add_seg('XO', lay, a, bb_)
        n += 1
for v in D['xo']['vias']:
    add_via('XO', v[0], v[1])
print('XO journey segs', n, 'vias', len(D['xo']['vias']))
# PHY stub + notch via + B journey
add_seg('PHY_1V8A', F, (75.75, 11.5625), (75.72, 11.0))
add_seg('PHY_1V8A', F, (75.72, 11.0), (75.7375, 10.75))
add_via('PHY_1V8A', 75.7375, 10.75)
Bpts = [(75.7375, 10.75), (75.3, 11.35), (74.9, 11.75), (74.2, 12.25),
        (73.5, 12.55), (73.3, 12.2), (73.22, 11.94), (72.92, 11.62),
        (72.35, 11.65), (71.9, 11.95), (71.3, 12.1), (70.7, 11.85),
        (70.3, 12.15), (70.2, 12.5), (70.18, 12.75)]
for a, bb_ in zip(Bpts, Bpts[1:]):
    add_seg('PHY_1V8A', BK, a, bb_)
# PHY tail journey
n = 0
for run in D['tail']['runs']:
    lay = (F, I2, BK)[run['layer']]
    pts = [tuple(p) for p in run['pts']]
    for a, bb_ in zip(pts, pts[1:]):
        add_seg('PHY_1V8A', lay, a, bb_)
        n += 1
print('PHY tail segs', n)
add_via('PHY_1V8A', 71.48, 15.38)
add_seg('PHY_1V8A', F, (71.48, 15.38), (71.48, 15.15))
# GND journey
n = 0
for run in D['gnd']['runs']:
    lay = (F, I2, BK)[run['layer']]
    pts = [tuple(p) for p in run['pts']]
    for a, bb_ in zip(pts, pts[1:]):
        add_seg('GND', lay, a, bb_)
        n += 1
for v in D['gnd']['vias']:
    add_via('GND', v[0], v[1])
print('GND journey segs', n, 'vias', len(D['gnd']['vias']))

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save('hw/pdlvds_rx.exp250.kicad_pcb')
print('saved exp250')

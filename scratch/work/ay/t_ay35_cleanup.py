import sys, math
sys.path.insert(0, 'scratch/work/ax')
import wx
_app = wx.App(False)
import pcbnew
from pcbnew import VECTOR2I

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp251.kicad_pcb')
F, BK = pcbnew.F_Cu, pcbnew.B_Cu

def mm(v):
    return (v.x / 1e6, v.y / 1e6)

def V(x, y):
    return VECTOR2I(int(round(x * 1e6)), int(round(y * 1e6)))

# ---------- 1) dedupe ULPI_STP exact-duplicate tracks + vias ----------
seen = {}
victims = []
for t in b.GetTracks():
    if t.GetNetname() != 'ULPI_STP':
        continue
    if isinstance(t, pcbnew.PCB_VIA):
        key = ('via', mm(t.GetPosition()), t.GetWidth())
    else:
        a, bb_ = mm(t.GetStart()), mm(t.GetEnd())
        key = ('seg', t.GetLayer(), min(a, bb_), max(a, bb_), t.GetWidth())
    if key in seen:
        victims.append(t)
    else:
        seen[key] = t
for t in victims:
    b.Remove(t)
print('STP duplicates removed:', len(victims), flush=True)

# ---------- 3) PHY tail via (71.375,17.625) ----------
tv = [t for t in b.GetTracks() if isinstance(t, pcbnew.PCB_VIA)
      and t.GetNetname() == 'PHY_1V8'
      and abs(mm(t.GetPosition())[0] - 71.375) < 0.01
      and abs(mm(t.GetPosition())[1] - 17.625) < 0.01]
assert len(tv) == 1
b.Remove(tv[0])
print('tail via removed', flush=True)

# ---------- 4) PHY F stub jog (census heal) ----------
stub = [t for t in b.GetTracks()
        if isinstance(t, pcbnew.PCB_TRACK)
        and not isinstance(t, pcbnew.PCB_VIA)
        and t.GetNetname() == 'PHY_1V8' and t.GetLayer() == F
        and abs(mm(t.GetStart())[0] - 77.25) < 0.01
        and abs(mm(t.GetStart())[1] - 10.75) < 0.01
        and abs(mm(t.GetEnd())[0] - 77.90) < 0.01
        and abs(mm(t.GetEnd())[1] - 10.08) < 0.01]
assert len(stub) == 1
b.Remove(stub[0])
NC = {n: b.GetNetcodeFromNetname(n) for n in ('PHY_1V8', 'GND')}

def add_seg(net, layer, a, bb_, w):
    t = pcbnew.PCB_TRACK(b)
    t.SetNetCode(NC[net])
    t.SetLayer(layer)
    t.SetStart(V(*a))
    t.SetEnd(V(*bb_))
    t.SetWidth(int(w))
    b.Add(t)
    return t

add_seg('PHY_1V8', F, (77.25, 10.75), (77.55, 10.35), 200000)
add_seg('PHY_1V8', F, (77.55, 10.35), (77.90, 10.08), 200000)
print('stub jog emitted', flush=True)

# ---------- 5) GND island stitches ----------
# exact point-in-polygon over F GND filled outlines (ray casting)
polys = []
for z in b.Zones():
    if z.GetNetname() != 'GND' or not z.IsOnLayer(F):
        continue
    poly = z.GetFilledPolysList(F)
    for oi in range(poly.OutlineCount()):
        o = poly.Outline(oi)
        pts = [(o.GetPoint(i).x / 1e6, o.GetPoint(i).y / 1e6)
               for i in range(o.PointCount())]
        polys.append(pts)

def in_poly(px, py, pts):
    inside = False
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        if (y1 > py) != (y2 > py):
            xin = x1 + (py - y1) * (x2 - x1) / (y2 - y1)
            if px < xin:
                inside = not inside
    return inside

def poly_at(px, py):
    return [i for i, pts in enumerate(polys) if in_poly(px, py, pts)]

# viafit gate from the item pool of the CURRENT board state is complex;
# use pcbnew geometry: candidate must be >=0.75mm centre-distance from
# every foreign track/via/pad on F (conservative for d0.5 via, 0.25 clr)
foreign = []
for t in b.GetTracks():
    if t.GetNetname() == 'GND':
        continue
    if isinstance(t, pcbnew.PCB_VIA):
        foreign.append(('via', mm(t.GetPosition()),
                        t.GetWidth() / 2e6))
    else:
        foreign.append(('seg', (mm(t.GetStart()), mm(t.GetEnd())),
                        t.GetWidth() / 2e6))
pads_f = []
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetNetname() != 'GND':
            pads_f.append((mm(p.GetPosition()),
                           (p.GetSize().x / 2e6, p.GetSize().y / 2e6)))

def seg_dist(px, py, a, bb_):
    dx, dy = bb_[0] - a[0], bb_[1] - a[1]
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - a[0]) * dx +
                                              (py - a[1]) * dy) / L2))
    return math.hypot(px - (a[0] + t * dx), py - (a[1] + t * dy))

def viafit(px, py):
    worst = 9.9
    for kind, d, r in foreign:
        if kind == 'via':
            dd = math.hypot(px - d[0], py - d[1]) - r
        else:
            dd = seg_dist(px, py, d[0], d[1]) - r
        worst = min(worst, dd - 0.25 - 0.2)  # via r0.25 + req 0.2
    for (cx, cy), (hw, hh) in pads_f:
        dd = math.hypot(max(abs(px - cx) - hw, 0.0),
                        max(abs(py - cy) - hh, 0.0))
        worst = min(worst, dd - 0.25 - 0.2)
    return worst

def add_via(net, x, y):
    v = pcbnew.PCB_VIA(b)
    v.SetNetCode(NC[net])
    v.SetPosition(V(x, y))
    v.SetWidth(500000)
    v.SetDrill(300000)
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(F, BK)
    b.Add(v)
    return v

cands = {'A': [(67.65, -0.77), (67.15, -0.52), (67.4, -0.77)],
         'B': [(69.13, -8.94), (69.38, -9.19), (68.88, -8.69)]}
for tag, pts in cands.items():
    done = False
    for (px, py) in pts:
        own = poly_at(px, py)
        g = viafit(px, py)
        print(f'  stitch {tag} cand ({px},{py}): polys {own} '
              f'viafit {g:+.3f}', flush=True)
        if own and g >= 0.0:
            add_via('GND', px, py)
            print(f'  stitch {tag} EMITTED at ({px},{py})', flush=True)
            done = True
            break
    assert done, f'no stitch site for island {tag}'

# ---------- refill + save ----------
filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())
b.Save('hw/pdlvds_rx.exp251.kicad_pcb')
print('saved exp251 v3 (cleanup)', flush=True)

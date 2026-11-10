#!/usr/bin/env python3
"""bl fix1 on exp259 -> exp260: named-fence repairs after the U7 re-place.
CK stub, STP tail, XO north revert+connector, PHY_1V8 stub + D0 root,
+3V3A east web restore + fresh pad feeds, PHY_1V8A stub."""
import math
import wx
_app = wx.App(False)
import pcbnew

IU = 1e6
F, IN2, B = pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp259.kicad_pcb')
b257 = pcbnew.LoadBoard('hw/pdlvds_rx.exp257.kicad_pcb')

def NC(n):
    return b.GetNetcodeFromNetname(n)

def pts(t):
    s, e = t.GetStart(), t.GetEnd()
    return (s.x / IU, s.y / IU), (e.x / IU, e.y / IU)

def near(p, q, tol=0.012):
    return abs(p[0] - q[0]) <= tol and abs(p[1] - q[1]) <= tol

def rip(net, layer, a, bb):
    hits = []
    for t in list(b.GetTracks()):
        if t.GetNetname() != net or t.Type() == pcbnew.PCB_VIA_T:
            continue
        if layer is not None and t.GetLayer() != layer:
            continue
        p, q = pts(t)
        if (near(p, a) and near(q, bb)) or (near(p, bb) and near(q, a)):
            hits.append(t)
    for t in hits:
        b.Remove(t)
    print(f'  rip {net} {a}->{bb}: {len(hits)}')
    return len(hits)

def rip_where(net, layer, pred, label):
    hits = []
    for t in list(b.GetTracks()):
        if t.GetNetname() != net or t.Type() == pcbnew.PCB_VIA_T:
            continue
        if layer is not None and t.GetLayer() != layer:
            continue
        p, q = pts(t)
        if pred(p, q):
            hits.append(t)
    for t in hits:
        b.Remove(t)
    print(f'  rip {net} {label}: {len(hits)}')
    return len(hits)

def add(net, layer, a, bb, w=0.20):
    t = pcbnew.PCB_TRACK(b)
    t.SetNetCode(NC(net))
    t.SetLayer(layer)
    t.SetStart(pcbnew.VECTOR2I(int(round(a[0] * IU)), int(round(a[1] * IU))))
    t.SetEnd(pcbnew.VECTOR2I(int(round(bb[0] * IU)), int(round(bb[1] * IU))))
    t.SetWidth(int(round(w * IU)))
    b.Add(t)

def add_via(net, x, y, d=0.5, drill=0.3):
    v = pcbnew.PCB_VIA(b)
    v.SetNetCode(NC(net))
    v.SetPosition(pcbnew.VECTOR2I(int(round(x * IU)), int(round(y * IU))))
    v.SetWidth(int(round(d * IU)))
    v.SetDrill(int(round(drill * IU)))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    b.Add(v)

def census(board):
    out = {}
    for t in board.GetTracks():
        k = (t.GetNetname(), 'via' if t.Type() == pcbnew.PCB_VIA_T else 'trk')
        out[k] = out.get(k, 0) + 1
    return out

base = census(b)
print('== CK stub')
rip('ULPI_CK', F, (77.500, 16.438), (76.625, 17.500))
add('ULPI_CK', F, (77.5, 16.438), (77.5, 17.2))
add('ULPI_CK', F, (77.5, 17.2), (76.625, 17.5))
print('== STP tail')
for a, bb in [((76.800, 17.300), (76.800, 17.350)), ((76.800, 17.350), (76.800, 17.400)),
              ((76.800, 17.400), (76.800, 17.450)), ((76.800, 17.450), (76.800, 17.500)),
              ((76.800, 17.500), (76.800, 17.550)), ((76.800, 17.550), (76.800, 17.600)),
              ((76.800, 17.600), (76.800, 17.650)), ((76.800, 17.650), (76.050, 17.700)),
              ((76.050, 17.700), (76.050, 17.750)), ((76.050, 17.750), (76.050, 17.800)),
              ((76.050, 17.800), (76.050, 17.850))]:
    rip('ULPI_STP', F, a, bb)
add('ULPI_STP', F, (76.85, 17.25), (77.18, 17.80))
add('ULPI_STP', F, (77.18, 17.80), (76.40, 18.05))
add('ULPI_STP', F, (76.40, 18.05), (76.05, 17.85))
print('== XO north revert + connector')
BOX = (76.3, 9.55, 78.1, 11.65)
rip_where('XO', F, lambda p, q: BOX[0] <= p[0] <= BOX[2] and BOX[1] <= p[1] <= BOX[3]
          and BOX[0] <= q[0] <= BOX[2] and BOX[1] <= q[1] <= BOX[3], 'north box')
for a, bb in [((77.5, 11.562), (77.1, 11.15)), ((77.1, 11.15), (76.5, 10.75)),
              ((76.5, 10.75), (76.3, 10.3)), ((76.3, 10.3), (76.25, 9.95))]:
    add('XO', F, a, bb)
print('== PHY_1V8 pad26 stub')
rip('PHY_1V8', F, (78.000, 11.562), (78.000, 10.750))
rip('PHY_1V8', F, (78.000, 10.750), (78.300, 10.350))
rip('PHY_1V8', F, (78.300, 10.350), (77.900, 10.080))
for a, bb in [((78.0, 11.562), (78.45, 11.35)), ((78.45, 11.35), (78.55, 10.8)),
              ((78.55, 10.8), (78.3, 10.35)), ((78.3, 10.35), (77.9, 10.08))]:
    add('PHY_1V8', F, a, bb)
print('== D0 root')
rip('ULPI_D0', F, (79.188, 12.250), (78.438, 11.250))
rip('ULPI_D0', F, (78.438, 11.250), (78.625, 10.625))
rip('ULPI_D0', F, (78.625, 10.625), (78.875, 10.375))
for a, bb in [((79.188, 12.250), (79.35, 11.5)), ((79.35, 11.5), (79.05, 10.9)),
              ((79.05, 10.9), (78.875, 10.375))]:
    add('ULPI_D0', F, a, bb, 0.25)
print('== +3V3A east web restore')
EB = (75.8, 9.6, 80.8, 17.8)
# old U7 pad rects (exp257) for +3V3A pads: skip restoring old stubs
old_pads = [(77.625, 11.122, 77.875, 12.002), (77.625, 16.0, 77.875, 16.876),
            (75.125, 11.122, 75.375, 12.002), (74.625, 11.122, 74.875, 12.002),
            (73.122, 14.625, 74.002, 14.875)]

def in_old_pad(p):
    return any(r[0] - 0.03 <= p[0] <= r[2] + 0.03 and r[1] - 0.03 <= p[1] <= r[3] + 0.03
               for r in old_pads)

def inbox(p):
    return EB[0] <= p[0] <= EB[2] and EB[1] <= p[1] <= EB[3]

# keep exp259 +3V3A pieces incident to moved U7.30/31 pads (their stubs are clean)
keep_pts = [(75.625, 11.125), (75.875, 11.125), (75.0, 10.625), (74.375, 10.625)]
rip_where('+3V3A', None, lambda p, q: inbox(p) and inbox(q)
          and not any(near(p, k, 0.02) or near(q, k, 0.02) for k in keep_pts),
          'east box (non-stub)')
n_add = 0
for t in list(b257.GetTracks()):
    if t.GetNetname() != '+3V3A' or t.Type() == pcbnew.PCB_VIA_T:
        continue
    s, e = t.GetStart(), t.GetEnd()
    p, q = (s.x / IU, s.y / IU), (e.x / IU, e.y / IU)
    if inbox(p) and inbox(q) and not in_old_pad(p) and not in_old_pad(q):
        nt = pcbnew.PCB_TRACK(b)
        nt.SetNetCode(NC('+3V3A'))
        nt.SetLayer(t.GetLayer())
        nt.SetStart(pcbnew.VECTOR2I(s.x, s.y))
        nt.SetEnd(pcbnew.VECTOR2I(e.x, e.y))
        nt.SetWidth(t.GetWidth())
        b.Add(nt)
        n_add += 1
print(f'  restored {n_add} exp257 +3V3A pieces')
# fresh feeds: pad25 -> new via -> In2 link to existing via; pad16 -> web joint
add_via('+3V3A', 78.7, 11.75)
add('+3V3A', F, (78.5, 11.562), (78.7, 11.75))
add('+3V3A', IN2, (78.7, 11.75), (78.2, 11.3), 0.6)
add('+3V3A', IN2, (78.2, 11.3), (77.862, 10.975), 0.6)
add('+3V3A', F, (78.5, 16.438), (78.35, 16.55))
add('+3V3A', F, (78.35, 16.55), (78.125, 16.375))
print('== PHY_1V8A stub')
rip('PHY_1V8A', F, (76.500, 11.562), (76.470, 11.000))
rip('PHY_1V8A', F, (76.470, 11.000), (74.990, 10.280))
add('PHY_1V8A', F, (76.5, 11.562), (76.1, 11.05))
add('PHY_1V8A', F, (76.1, 11.05), (74.99, 10.28))

b.BuildConnectivity()
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save('hw/pdlvds_rx.exp260.kicad_pcb')
b2 = pcbnew.LoadBoard('hw/pdlvds_rx.exp260.kicad_pcb')
new = census(b2)
print('census diffs vs exp259 (only changed):')
for k in sorted(set(base) | set(new)):
    if base.get(k, 0) != new.get(k, 0):
        print(f'  {k}: {base.get(k,0)} -> {new.get(k,0)}')
print('saved exp260')

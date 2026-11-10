#!/usr/bin/env python3
"""bl fix1 on exp259 -> exp260: named-fence repairs after the U7 re-place.
Snapshot-first: all geometry read into plain tuples BEFORE any mutation
(pcbnew wrappers rot after board edits). Removes, then adds, then refill."""
import wx
_app = wx.App(False)
import pcbnew

IU = 1e6
F, IN2, B = pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp259.kicad_pcb')
b257 = pcbnew.LoadBoard('hw/pdlvds_rx.exp257.kicad_pcb')

def snap(board):
    out = []
    for t in board.GetTracks():
        s, e = t.GetStart(), t.GetEnd()
        out.append(dict(obj=t, net=t.GetNetname(), via=t.Type() == pcbnew.PCB_VIA_T,
                        layer=t.GetLayer(), p=(s.x / IU, s.y / IU), q=(e.x / IU, e.y / IU),
                        w=t.GetWidth() / IU, code=t.GetNetCode()))
    return out

SNAP = snap(b)
SNAP257 = snap(b257)
NETCODES = {}
for d in SNAP:
    NETCODES.setdefault(d['net'], d['code'])
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetNetname():
            NETCODES.setdefault(p.GetNetname(), p.GetNetCode())

def near(p, q, tol=0.012):
    return abs(p[0] - q[0]) <= tol and abs(p[1] - q[1]) <= tol

def rip(net, layer, a, bb):
    hits = [d for d in SNAP if d['net'] == net and not d['via']
            and (layer is None or d['layer'] == layer)
            and ((near(d['p'], a) and near(d['q'], bb)) or (near(d['p'], bb) and near(d['q'], a)))]
    for d in hits:
        b.Remove(d['obj'])
        SNAP.remove(d)
    print(f'  rip {net} {a}->{bb}: {len(hits)}')
    return len(hits)

def rip_where(net, layer, pred, label):
    hits = [d for d in SNAP if d['net'] == net and not d['via']
            and (layer is None or d['layer'] == layer) and pred(d['p'], d['q'])]
    for d in hits:
        b.Remove(d['obj'])
        SNAP.remove(d)
    print(f'  rip {net} {label}: {len(hits)}')
    return len(hits)

ADDS = []

def add(net, layer, a, bb, w=0.20):
    ADDS.append(('trk', net, layer, a, bb, w))

def add_via(net, x, y, d=0.5, drill=0.3):
    ADDS.append(('via', net, x, y, d, drill))

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
old_pads = [(77.625, 11.122, 77.875, 12.002), (77.625, 16.0, 77.875, 16.876),
            (75.125, 11.122, 75.375, 12.002), (74.625, 11.122, 74.875, 12.002),
            (73.122, 14.625, 74.002, 14.875)]

def in_old_pad(p):
    return any(r[0] - 0.03 <= p[0] <= r[2] + 0.03 and r[1] - 0.03 <= p[1] <= r[3] + 0.03
               for r in old_pads)

def inbox(p):
    return EB[0] <= p[0] <= EB[2] and EB[1] <= p[1] <= EB[3]

keep_pts = [(75.625, 11.125), (75.875, 11.125), (75.0, 10.625), (74.375, 10.625)]
rip_where('+3V3A', None, lambda p, q: inbox(p) and inbox(q)
          and not any(near(p, k, 0.02) or near(q, k, 0.02) for k in keep_pts),
          'east box (non-stub)')
n_add = 0
for d in SNAP257:
    if d['net'] != '+3V3A' or d['via']:
        continue
    if inbox(d['p']) and inbox(d['q']) and not in_old_pad(d['p']) and not in_old_pad(d['q']):
        ADDS.append(('trk', '+3V3A', d['layer'], d['p'], d['q'], d['w']))
        n_add += 1
print(f'  restored {n_add} exp257 +3V3A pieces')
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

print(f'== applying {len(ADDS)} adds')
for a in ADDS:
    if a[0] == 'trk':
        _, net, layer, p, q, w = a
        t = pcbnew.PCB_TRACK(b)
        t.SetNetCode(NETCODES[net])
        t.SetLayer(layer)
        t.SetStart(pcbnew.VECTOR2I(int(round(p[0] * IU)), int(round(p[1] * IU))))
        t.SetEnd(pcbnew.VECTOR2I(int(round(q[0] * IU)), int(round(q[1] * IU))))
        t.SetWidth(int(round(w * IU)))
        b.Add(t)
    else:
        _, net, x, y, dd, dr = a
        v = pcbnew.PCB_VIA(b)
        v.SetNetCode(NETCODES[net])
        v.SetPosition(pcbnew.VECTOR2I(int(round(x * IU)), int(round(y * IU))))
        v.SetWidth(int(round(dd * IU)))
        v.SetDrill(int(round(dr * IU)))
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        b.Add(v)

b.BuildConnectivity()
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save('hw/pdlvds_rx.exp260.kicad_pcb')
b2 = pcbnew.LoadBoard('hw/pdlvds_rx.exp260.kicad_pcb')
c260 = {}
for t in b2.GetTracks():
    k = (t.GetNetname(), 'via' if t.Type() == pcbnew.PCB_VIA_T else 'trk')
    c260[k] = c260.get(k, 0) + 1
b259 = pcbnew.LoadBoard('hw/pdlvds_rx.exp259.kicad_pcb')
c259 = {}
for t in b259.GetTracks():
    k = (t.GetNetname(), 'via' if t.Type() == pcbnew.PCB_VIA_T else 'trk')
    c259[k] = c259.get(k, 0) + 1
print('census diffs exp259 -> exp260 (only changed):')
for k in sorted(set(c259) | set(c260)):
    if c259.get(k, 0) != c260.get(k, 0):
        print(f'  {k}: {c259.get(k,0)} -> {c260.get(k,0)}')
print('saved exp260')

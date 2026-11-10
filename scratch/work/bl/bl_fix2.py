#!/usr/bin/env python3
"""bl fix2 on exp260 -> exp261. Packages:
A south fanout joint re-lay (CK via move, STP west route, DIR shift)
B east-row via moves D2/D3/D4/D6/D7 (+ B re-lay for D7)
C C19 +0.2E, NRST stub, +3V3D vertical east
D +3V3A: pad15-touch rip, In2 bridge restore, north feed re-lay,
  pad25 feed via B detour to SE web via
E PHY_1V8 pad26 stub nudge east
F ULPI_D0 east-branch root to staircase joint (78.625,9.875)
G ULPI_D1 funnel re-lay east
H XO connector SW channel + rip sheared 0.8 chain piece
I PHY_1V8A stub re-lay
Snapshot-first (wrappers rot after mutation)."""
import wx
_app = wx.App(False)
import pcbnew

IU = 1e6
F, IN2, B = pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp260.kicad_pcb')

# C19 move first (fresh footprint object, before track work)
for fp in b.GetFootprints():
    if fp.GetReference() == 'C19':
        p = fp.GetPosition()
        fp.SetPosition(pcbnew.VECTOR2I(p.x + int(0.20 * IU), p.y))
        print(f'C19 -> ({fp.GetPosition().x/IU:.3f},{fp.GetPosition().y/IU:.3f})')
        break

def snap(board):
    out = []
    for t in board.GetTracks():
        s, e = t.GetStart(), t.GetEnd()
        out.append(dict(obj=t, net=t.GetNetname(), via=t.Type() == pcbnew.PCB_VIA_T,
                        layer=t.GetLayer(), p=(s.x / IU, s.y / IU), q=(e.x / IU, e.y / IU),
                        w=t.GetWidth() / IU, code=t.GetNetCode(),
                        pos=(t.GetPosition().x / IU, t.GetPosition().y / IU)))
    return out

SNAP = snap(b)
NETCODES = {}
for d in SNAP:
    NETCODES.setdefault(d['net'], d['code'])

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

def rip_via(net, at):
    hits = [d for d in SNAP if d['net'] == net and d['via'] and near(d['pos'], at)]
    for d in hits:
        b.Remove(d['obj'])
        SNAP.remove(d)
    print(f'  rip via {net} @{at}: {len(hits)}')
    return len(hits)

ADDS = []

def add(net, layer, a, bb, w=0.20):
    ADDS.append(('trk', net, layer, a, bb, w))

def chain(net, layer, pts, w=0.20):
    for a, bb in zip(pts, pts[1:]):
        add(net, layer, a, bb, w)

def add_via(net, x, y, d=0.5, drill=0.3):
    ADDS.append(('via', net, x, y, d, drill))

print('== A south fanout')
rip('ULPI_CK', F, (77.500, 16.438), (77.500, 17.200))
rip('ULPI_CK', F, (77.500, 17.200), (76.625, 17.500))
rip_via('ULPI_CK', (76.625, 17.500))
rip('ULPI_CK', IN2, (76.620, 17.300), (76.625, 17.500))
add_via('ULPI_CK', 77.05, 17.85)
chain('ULPI_CK', F, [(77.5, 16.438), (77.5, 17.3), (77.05, 17.85)])
chain('ULPI_CK', IN2, [(77.05, 17.85), (77.35, 18.35), (76.9, 18.75),
                      (76.62, 18.3), (76.62, 17.3)])
for a, bb in [((77.000, 16.950), (76.950, 17.000)), ((76.950, 17.000), (76.950, 17.050)),
              ((76.950, 17.050), (76.900, 17.100)), ((76.900, 17.100), (76.900, 17.150)),
              ((76.900, 17.150), (76.850, 17.200)), ((76.850, 17.200), (76.850, 17.250)),
              ((76.850, 17.250), (76.800, 17.300)), ((76.850, 17.250), (77.180, 17.800)),
              ((77.180, 17.800), (76.400, 18.050)), ((76.400, 18.050), (76.050, 17.850))]:
    rip('ULPI_STP', F, a, bb)
chain('ULPI_STP', F, [(77.0, 16.95), (76.55, 17.2), (76.45, 17.75),
                      (76.3, 18.15), (76.065, 17.96)])
rip('ULPI_DIR', F, (76.500, 16.875), (76.350, 17.300))
rip('ULPI_DIR', F, (76.350, 17.300), (75.420, 17.950))
chain('ULPI_DIR', F, [(76.5, 16.875), (76.2, 17.35), (75.42, 17.95)])
print('== B east via moves')
rip('ULPI_D2', F, (79.875, 13.125), (79.870, 12.970))
rip('ULPI_D2', IN2, (79.870, 12.970), (80.000, 8.300))
rip_via('ULPI_D2', (79.870, 12.970))
add_via('ULPI_D2', 80.3, 12.8)
add('ULPI_D2', F, (79.875, 13.125), (80.3, 12.8))
add('ULPI_D2', IN2, (80.3, 12.8), (80.0, 8.3), 0.25)
rip('ULPI_D3', F, (79.950, 13.750), (79.790, 13.830))
rip('ULPI_D3', IN2, (79.790, 13.830), (82.200, 11.600))
rip_via('ULPI_D3', (79.790, 13.830))
add_via('ULPI_D3', 80.15, 13.7)
add('ULPI_D3', F, (79.95, 13.75), (80.15, 13.7))
add('ULPI_D3', IN2, (80.15, 13.7), (82.2, 11.6), 0.25)
rip('ULPI_D4', F, (79.875, 14.375), (79.969, 14.531))
rip('ULPI_D4', IN2, (79.969, 14.531), (80.375, 14.125))
rip_via('ULPI_D4', (79.969, 14.531))
add_via('ULPI_D4', 80.2, 14.45)
add('ULPI_D4', F, (79.875, 14.375), (80.2, 14.45))
add('ULPI_D4', IN2, (80.2, 14.45), (80.375, 14.125))
rip('ULPI_D6', F, (80.875, 15.750), (80.750, 14.625))
rip('ULPI_D6', IN2, (80.750, 14.625), (81.375, 14.125))
rip_via('ULPI_D6', (80.750, 14.625))
add_via('ULPI_D6', 81.0, 14.4, 0.6)
add('ULPI_D6', F, (80.875, 15.75), (81.0, 14.4))
add('ULPI_D6', IN2, (81.0, 14.4), (81.375, 14.125))
rip('ULPI_D7', F, (78.438, 15.750), (78.688, 15.750))
rip('ULPI_D7', F, (78.688, 15.750), (78.625, 15.875))
rip('ULPI_D7', B, (78.625, 15.875), (78.625, 14.375))
rip('ULPI_D7', B, (78.625, 14.375), (78.625, 10.625))
rip('ULPI_D7', B, (78.625, 10.625), (78.875, 10.375))
rip_via('ULPI_D7', (78.625, 15.875))
add_via('ULPI_D7', 79.1, 15.88, 0.6)
add('ULPI_D7', F, (79.19, 15.75), (79.1, 15.88))
chain('ULPI_D7', B, [(79.1, 15.88), (79.05, 14.4), (78.95, 10.7), (78.875, 10.375)], 0.25)
print('== C C19 / NRST / +3V3D')
rip('NRST', F, (80.575, 12.000), (80.225, 10.500))
add('NRST', F, (80.775, 12.0), (80.225, 10.5))
rip('+3V3D', F, (81.000, 12.600), (81.000, 11.000))
rip('+3V3D', F, (81.000, 11.000), (81.625, 10.900))
rip('+3V3D', F, (80.825, 13.600), (81.000, 12.600))
chain('+3V3D', F, [(80.825, 13.6), (81.55, 12.3), (81.55, 11.05), (81.625, 10.9)])
print('== D +3V3A')
rip('+3V3A', F, (78.000, 16.438), (78.125, 16.375))
add('+3V3A', IN2, (78.125, 16.375), (77.875, 16.125))
rip('+3V3A', F, (75.875, 11.125), (74.250, 10.625))
chain('+3V3A', F, [(75.875, 11.125), (75.62, 10.78), (74.7, 10.76), (74.375, 10.625)])
rip_via('+3V3A', (78.700, 11.750))
rip('+3V3A', F, (78.500, 11.562), (78.700, 11.750))
rip('+3V3A', IN2, (78.700, 11.750), (78.200, 11.300))
rip('+3V3A', IN2, (78.200, 11.300), (77.862, 10.975))
add_via('+3V3A', 78.8, 11.62)
add('+3V3A', F, (78.5, 11.562), (78.8, 11.62))
chain('+3V3A', B, [(78.8, 11.62), (79.5, 11.9), (79.65, 12.6), (79.65, 14.5),
                   (79.375, 16.625)])
print('== E PHY_1V8 stub')
rip('PHY_1V8', F, (78.000, 11.562), (78.450, 11.350))
rip('PHY_1V8', F, (78.450, 11.350), (78.550, 10.800))
rip('PHY_1V8', F, (78.550, 10.800), (78.300, 10.350))
rip('PHY_1V8', F, (78.300, 10.350), (77.900, 10.080))
chain('PHY_1V8', F, [(78.0, 11.562), (78.52, 11.3), (78.64, 10.75),
                     (78.3, 10.35), (77.9, 10.08)])
print('== F D0 root')
rip('ULPI_D0', F, (79.188, 12.250), (79.350, 11.500))
rip('ULPI_D0', F, (79.350, 11.500), (79.050, 10.900))
rip('ULPI_D0', F, (79.050, 10.900), (78.875, 10.375))
chain('ULPI_D0', F, [(79.19, 12.25), (79.42, 11.9), (79.42, 11.45), (79.3, 10.95),
                     (79.0, 10.72), (78.45, 10.35), (78.5, 10.15), (78.625, 9.875)], 0.25)
print('== G D1 funnel')
rip('ULPI_D1', F, (79.930, 11.950), (79.050, 11.400))
rip('ULPI_D1', F, (79.050, 11.400), (79.050, 11.050))
rip('ULPI_D1', F, (79.050, 11.050), (79.350, 10.350))
chain('ULPI_D1', F, [(79.93, 11.95), (79.78, 11.5), (79.75, 10.9), (79.35, 10.35)])
print('== H XO connector')
rip('XO', F, (77.500, 11.562), (77.100, 11.150))
rip('XO', F, (77.100, 11.150), (76.500, 10.750))
rip('XO', F, (76.500, 10.750), (76.300, 10.300))
rip('XO', F, (76.300, 10.300), (76.250, 9.950))
rip('XO', F, (76.850, 9.800), (76.050, 9.800))
chain('XO', F, [(77.5, 11.562), (77.3, 11.02), (77.12, 10.5), (76.6, 10.45),
                (76.2, 10.0), (76.05, 9.8)])
print('== I PHY_1V8A stub')
rip('PHY_1V8A', F, (76.500, 11.562), (76.100, 11.050))
rip('PHY_1V8A', F, (76.100, 11.050), (74.990, 10.280))
chain('PHY_1V8A', F, [(76.5, 11.562), (76.42, 10.92), (75.95, 10.82),
                      (75.35, 10.42), (74.99, 10.28)])

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
b.Save('hw/pdlvds_rx.exp261.kicad_pcb')
print('saved exp261')

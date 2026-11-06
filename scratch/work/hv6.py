import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp196.kicad_pcb')
def M(v): return pcbnew.FromMM(v)
def mm(v): return pcbnew.ToMM(v)
victims = []
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == 'GND':
        p = t.GetPosition()
        if abs(mm(p.x)-28.25) < 0.01 and abs(mm(p.y)+3.0) < 0.01:
            victims.append(t)
assert len(victims) == 1
for t in victims: b.Remove(t)
def track(netname, layer, w, pts):
    net = b.FindNet(netname)
    for a, bb in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(pcbnew.VECTOR2I(M(a[0]), M(a[1]))); t.SetEnd(pcbnew.VECTOR2I(M(bb[0]), M(bb[1])))
        t.SetWidth(M(w)); t.SetLayer(layer); t.SetNet(net); b.Add(t)
def via(netname, x, y, dia=0.5, drill=0.3):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(pcbnew.VECTOR2I(M(x), M(y)))
    v.SetDrill(M(drill)); v.SetWidth(M(dia))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(b.FindNet(netname)); b.Add(v)
via('GND', 28.05, -3.0, 0.6, 0.3)
track('HV_VC', pcbnew.F_Cu, 0.2, [(21.925,-3.0),(21.3,-3.6),(22.2,-4.6),(23.5,-4.55),(24.85,-4.08)])
via('HV_VC2', 20.725, -1.5)
track('HV_VC2', pcbnew.B_Cu, 0.2, [(20.725,-1.5),(23.45,-3.15)])
via('HV_VC2', 23.45, -3.15)
track('HV_GATE', pcbnew.F_Cu, 0.2, [(23.9,-9.05),(21.9,-10.9),(22.3,-12.15),(27.3,-12.15),(27.6,-9.0)])
track('HV_GATE', pcbnew.F_Cu, 0.15, [(27.6,-9.0),(28.65,-7.9),(28.85,-7.5),(28.85,-6.6),(28.65,-6.2),(28.65,-2.5)])
track('HV_GATE', pcbnew.F_Cu, 0.2, [(28.65,-2.5),(29.3,-2.5)])
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
b.Save('scratch/work/t18.kicad_pcb'); print('saved t17')

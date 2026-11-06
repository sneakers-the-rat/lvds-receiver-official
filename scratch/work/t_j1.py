import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp202.kicad_pcb')
def M(v): return pcbnew.FromMM(v)
def track(netname, layer, w, pts):
    net = b.FindNet(netname)
    for a, bb in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(pcbnew.VECTOR2I(M(a[0]), M(a[1]))); t.SetEnd(pcbnew.VECTOR2I(M(bb[0]), M(bb[1])))
        t.SetWidth(M(w)); t.SetLayer(layer); t.SetNet(net); b.Add(t)
def via(netname, x, y, d=0.5, drill=0.3):
    net = b.FindNet(netname)
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(pcbnew.VECTOR2I(M(x), M(y)))
    v.SetDrill(M(drill)); v.SetWidth(M(d))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNet(net); b.Add(v)
_TS=b.Tracks(); _ALL=[_TS[i] for i in range(_TS.size())]
def alltracks():
    return _ALL
def rip(netname, layer, a, bb):
    # remove track whose endpoints match a-bb (either order), on layer
    for t in alltracks():
        if t.Type()==pcbnew.PCB_VIA_T: continue
        if t.GetNetname()!=netname or t.GetLayer()!=layer: continue
        s=(pcbnew.ToMM(t.GetStart().x),pcbnew.ToMM(t.GetStart().y)); e=(pcbnew.ToMM(t.GetEnd().x),pcbnew.ToMM(t.GetEnd().y))
        if (abs(s[0]-a[0])<0.01 and abs(s[1]-a[1])<0.01 and abs(e[0]-bb[0])<0.01 and abs(e[1]-bb[1])<0.01) or \
           (abs(s[0]-bb[0])<0.01 and abs(s[1]-bb[1])<0.01 and abs(e[0]-a[0])<0.01 and abs(e[1]-a[1])<0.01):
            b.Remove(t); print('ripped TRK', netname, a, bb); return
    print('RIP MISS TRK', netname, a, bb)
def ripvia(netname, x, y):
    for t in alltracks():
        if t.Type()!=pcbnew.PCB_VIA_T: continue
        if t.GetNetname()!=netname: continue
        p=t.GetPosition()
        if abs(pcbnew.ToMM(p.x)-x)<0.01 and abs(pcbnew.ToMM(p.y)-y)<0.01:
            b.Remove(t); print('ripped VIA', netname, x, y); return
    print('RIP MISS VIA', netname, x, y)

# --- DATP: rip old F exit + via + B head ---
rip('CDR_DATP', pcbnew.F_Cu, (66.0,34.562),(66.125,34.125))
rip('CDR_DATP', pcbnew.F_Cu, (66.125,34.125),(66.375,33.875))
ripvia('CDR_DATP', 66.375, 33.875)
rip('CDR_DATP', pcbnew.B_Cu, (66.375,33.875),(66.625,33.625))
# --- DATP: new exit, via (66.22,33.28) d0.5, B rejoin at midpoint of next B seg ---
track('CDR_DATP', pcbnew.F_Cu, 0.2, [(66.0,34.562),(66.02,34.05),(66.22,33.28)])
via('CDR_DATP', 66.22, 33.28)
track('CDR_DATP', pcbnew.B_Cu, 0.2, [(66.22,33.28),(66.75,33.5)])
# --- DATN: F thread + via (66.95,32.65) + B dive to own channel at (77.4,21.15) ---
track('CDR_DATN', pcbnew.F_Cu, 0.2, [(66.5,34.4),(66.62,34.0),(66.95,32.65)])
via('CDR_DATN', 66.95, 32.65)
track('CDR_DATN', pcbnew.B_Cu, 0.3, [(66.95,32.65),(67.98,30.87),(74.0,24.85),(75.2,23.35),(77.4,21.15)])
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
b.Save('scratch/work/t_j1.kicad_pcb'); print('saved t_j1')

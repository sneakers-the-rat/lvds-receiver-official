import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp196.kicad_pcb')
def M(v): return pcbnew.FromMM(v)
def mm(v): return pcbnew.ToMM(v)
def key(t):
    s, e = t.GetStart(), t.GetEnd()
    return (round(mm(s.x),3), round(mm(s.y),3), round(mm(e.x),3), round(mm(e.y),3))
kill = {(73.562,13.75,72.812,13.75), (72.812,13.75,72.125,13.625)}
kill |= {(k[2],k[3],k[0],k[1]) for k in list(kill)}
victims = []
for t in b.GetTracks():
    if t.GetNetname() == '+5V' and t.Type() != pcbnew.PCB_VIA_T and key(t) in kill:
        victims.append(t)
    elif t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == '+5V':
        p = t.GetPosition()
        if abs(mm(p.x)-72.125) < 0.01 and abs(mm(p.y)-13.625) < 0.01:
            victims.append(t)
print('victims', len(victims)); assert len(victims) == 3
for t in victims: b.Remove(t)
p5 = b.FindNet('+5V')
def track(net, layer, w, a, bb):
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(M(a[0]), M(a[1]))); t.SetEnd(pcbnew.VECTOR2I(M(bb[0]), M(bb[1])))
    t.SetWidth(M(w)); t.SetLayer(layer); t.SetNet(net); b.Add(t)
for a, bb in [((73.35,13.75),(72.72,13.75)), ((72.72,13.75),(72.55,13.37)), ((72.55,13.37),(69.9,13.33)), ((69.9,13.33),(69.75,13.4))]:
    track(p5, pcbnew.F_Cu, 0.2, a, bb)
v = pcbnew.PCB_VIA(b)
v.SetPosition(pcbnew.VECTOR2I(M(69.75), M(13.4)))
v.SetDrill(M(0.4)); v.SetWidth(M(0.8))
v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(p5); b.Add(v)
va = b.FindNet('+3V3A')
pts = [(73.9,14.75), (72.9,14.75), (72.62,13.8), (69.0,13.8), (69.0,19.0), (69.225,19.0)]
for a, bb in zip(pts, pts[1:]):
    track(va, pcbnew.F_Cu, 0.2, a, bb)
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
b.Save('scratch/work/t10.kicad_pcb'); print('saved t10')

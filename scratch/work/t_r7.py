import pcbnew
SRC='hw/pdlvds_rx.exp206.kicad_pcb'; OUT='scratch/work/t_r7.kicad_pcb'
b=pcbnew.LoadBoard(SRC)
F=pcbnew.F_Cu; In2=pcbnew.In2_Cu
def net(name): return b.FindNet(name)
def trk(netname, layer, w, x1,y1,x2,y2):
    t=pcbnew.PCB_TRACK(b); t.SetNet(net(netname)); t.SetLayer(layer)
    t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x1),pcbnew.FromMM(y1)))
    t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x2),pcbnew.FromMM(y2)))
    t.SetWidth(pcbnew.FromMM(w)); b.Add(t); return t
def via(netname, x, y, d=0.5, drill=0.3):
    v=pcbnew.PCB_VIA(b); v.SetNet(net(netname))
    v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y)))
    v.SetWidth(pcbnew.FromMM(d)); v.SetDrill(pcbnew.FromMM(drill))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v); return v
n=0
for t in list(b.GetTracks()):
    if t.Type()==pcbnew.PCB_VIA_T and t.GetNetname()=='GND':
        p=t.GetPosition()
        if abs(p.x/1e6-72.0)<0.01 and abs(p.y/1e6-14.65)<0.01:
            b.Remove(t); n+=1; print('ripped GND via (72.0,14.65)')
print('rips:', n)
via('GND', 71.70,14.55)                      # stitch inside C23.2's pad (same net)
trk('+3V3A', F, 0.20, 73.122,14.75, 72.90,14.62)
trk('+3V3A', F, 0.20, 72.90,14.62, 72.50,14.60)
via('+3V3A', 72.50,14.60)
trk('+3V3A', In2, 0.25, 72.50,14.60, 72.50,15.45)
trk('+3V3A', In2, 0.25, 72.50,15.45, 68.80,15.45)
via('+3V3A', 68.80,15.45)                    # disc overlaps B spine x68.625 (same net)
zf=pcbnew.ZONE_FILLER(b); zf.Fill(b.Zones())
b.Save(OUT); print('saved', OUT)

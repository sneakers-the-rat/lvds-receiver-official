import pcbnew
SRC='hw/pdlvds_rx.exp206.kicad_pcb'; OUT='scratch/work/t_r2.kicad_pcb'
b=pcbnew.LoadBoard(SRC)
F=pcbnew.F_Cu; In2=pcbnew.In2_Cu; Bc=pcbnew.B_Cu
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
ALLTRK=[]
_t=b.Tracks()
for _x in _t: ALLTRK.append(_x)
def rip(netname, layer, x1,y1,x2,y2):
    for t in ALLTRK:
        if t.GetNetname()!=netname or t.GetLayer()!=layer: continue
        s=t.GetStart(); e=t.GetEnd()
        pts={(round(s.x/1e6,3),round(s.y/1e6,3)),(round(e.x/1e6,3),round(e.y/1e6,3))}
        if pts=={(x1,y1),(x2,y2)}: b.Remove(t); print('ripped',netname,x1,y1,x2,y2); return
    print('RIP MISS', netname, x1,y1,x2,y2)
# PHY_1V8 stub relay: move the elbow east so XO's via clears it
rip('PHY_1V8', F, 77.25,10.812, 77.625,10.625)
rip('PHY_1V8', F, 77.625,10.625, 77.875,10.375)
trk('PHY_1V8', F, 0.20, 77.25,10.812, 77.75,10.65)
trk('PHY_1V8', F, 0.20, 77.75,10.65, 77.875,10.375)
# XO: F stub + via at (76.75,10.7)
trk('XO', F, 0.20, 76.75,11.562, 76.75,10.70)
via('XO', 76.75,10.70)
# In2: east jog, south run at x77.1, west underpass at y7.85
trk('XO', In2, 0.25, 76.75,10.70, 77.10,10.35)
trk('XO', In2, 0.25, 77.10,10.35, 77.10,7.85)
trk('XO', In2, 0.25, 77.10,7.85, 75.20,7.85)
# B hop over ULPI_CK In2 vertical (x74.625)
via('XO', 75.20,7.85)
trk('XO', Bc, 0.25, 75.20,7.85, 73.30,8.45)
via('XO', 73.30,8.45)
# In2: west + north into XO's own In2 path near (72.875,10.875)
trk('XO', In2, 0.25, 73.30,8.45, 72.85,8.30)
trk('XO', In2, 0.25, 72.85,8.30, 72.85,10.83)
zf=pcbnew.ZONE_FILLER(b); zf.Fill(b.Zones())
b.Save(OUT); print('saved', OUT)

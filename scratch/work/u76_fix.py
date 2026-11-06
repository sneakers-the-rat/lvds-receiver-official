import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp196.kicad_pcb')
def M(v): return pcbnew.FromMM(v)
def mm(v): return pcbnew.ToMM(v)
# 1) relay the GND stitch via 0.35 west
n = 0
for t in list(b.GetTracks()):
    if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == 'GND':
        p = t.GetPosition()
        if abs(mm(p.x)-72.0) < 0.01 and abs(mm(p.y)-14.65) < 0.01:
            b.Remove(t); n += 1
print('removed GND via', n); assert n == 1
gnd = b.FindNet('GND')
v = pcbnew.PCB_VIA(b)
v.SetPosition(pcbnew.VECTOR2I(M(71.65), M(14.65)))
v.SetDrill(M(0.3)); v.SetWidth(M(0.6))
v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(gnd); b.Add(v)
# 2) +3V3A F stub from U7.6 pad to the new via
net = b.FindNet('+3V3A')
t = pcbnew.PCB_TRACK(b)
t.SetStart(pcbnew.VECTOR2I(M(73.35), M(14.75))); t.SetEnd(pcbnew.VECTOR2I(M(72.5), M(14.75)))
t.SetWidth(M(0.2)); t.SetLayer(pcbnew.F_Cu); t.SetNet(net); b.Add(t)
# 3) +3V3A via
v = pcbnew.PCB_VIA(b)
v.SetPosition(pcbnew.VECTOR2I(M(72.5), M(14.75)))
v.SetDrill(M(0.3)); v.SetWidth(M(0.5))
v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(net); b.Add(v)
# 4) B run south then west into the trunk
pts = [(72.5,14.75), (72.5,12.1), (70.4,12.1), (70.4,8.625)]
for a, bb in zip(pts, pts[1:]):
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(M(a[0]), M(a[1]))); t.SetEnd(pcbnew.VECTOR2I(M(bb[0]), M(bb[1])))
    t.SetWidth(M(0.3)); t.SetLayer(pcbnew.B_Cu); t.SetNet(net); b.Add(t)
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
b.Save('scratch/work/t9.kicad_pcb'); print('saved t9')

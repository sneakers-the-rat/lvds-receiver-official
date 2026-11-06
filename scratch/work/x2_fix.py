import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp184.kicad_pcb')
def mm(v): return pcbnew.ToMM(v)
def M(x): return pcbnew.FromMM(x)
def key(t):
    s, e = t.GetStart(), t.GetEnd()
    return (round(mm(s.x),3), round(mm(s.y),3), round(mm(e.x),3), round(mm(e.y),3))
kill = {(73.375,25.625,73.625,25.375), (73.625,25.375,73.625,22.625), (73.625,22.625,73.875,22.375)}
kill |= {(k[2],k[3],k[0],k[1]) for k in list(kill)}
n = 0
for t in list(b.GetTracks()):
    if t.GetNetname() == 'CDR_SQUELCH' and key(t) in kill:
        b.Remove(t); n += 1
print('removed SQUELCH segs', n); assert n == 3
sq = b.FindNet('CDR_SQUELCH')
for a, bb in [((73.375,25.625),(73.975,25.375)), ((73.975,25.375),(73.975,22.625)), ((73.975,22.625),(73.875,22.375))]:
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(M(a[0]), M(a[1]))); t.SetEnd(pcbnew.VECTOR2I(M(bb[0]), M(bb[1])))
    t.SetWidth(M(0.25)); t.SetLayer(pcbnew.F_Cu); t.SetNet(sq); b.Add(t)
gnd = b.FindNet('GND')
for a, bb in [((72.9,24.575),(73.525,24.575)), ((73.525,24.575),(73.525,22.0))]:
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(M(a[0]), M(a[1]))); t.SetEnd(pcbnew.VECTOR2I(M(bb[0]), M(bb[1])))
    t.SetWidth(M(0.2)); t.SetLayer(pcbnew.F_Cu); t.SetNet(gnd); b.Add(t)
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
b.Save('scratch/work/s5.kicad_pcb'); print('saved s5')

import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp198.kicad_pcb')
def M(v): return pcbnew.FromMM(v)
code = b.FindNet('+5V').GetNetCode()
segs = [(41.8,51.25,42.125,50.875),(42.125,50.875,42.125,50.375),(42.125,50.375,42.375,50.125)]
hit = []
for t in list(b.GetTracks()):
    if t.GetNetCode() == code and t.GetLayer() == pcbnew.F_Cu and t.Type() == pcbnew.PCB_TRACE_T:
        s, e = t.GetStart(), t.GetEnd()
        for (x1,y1,x2,y2) in segs:
            if (abs(s.x/1e6-x1)<0.01 and abs(s.y/1e6-y1)<0.01 and abs(e.x/1e6-x2)<0.01 and abs(e.y/1e6-y2)<0.01) or \
               (abs(e.x/1e6-x1)<0.01 and abs(e.y/1e6-y1)<0.01 and abs(s.x/1e6-x2)<0.01 and abs(s.y/1e6-y2)<0.01):
                hit.append(t); break
for t in hit: b.Remove(t)
print('ripped', len(hit))
# now Add a track + via via helpers
net = b.FindNet('+5V')
t = pcbnew.PCB_TRACK(b)
t.SetStart(pcbnew.VECTOR2I(M(41.8), M(51.25))); t.SetEnd(pcbnew.VECTOR2I(M(42.15), M(51.35)))
t.SetWidth(M(0.2)); t.SetLayer(pcbnew.F_Cu); t.SetNet(net); b.Add(t)
v = pcbnew.PCB_VIA(b)
v.SetPosition(pcbnew.VECTOR2I(M(42.15), M(51.35)))
v.SetDrill(M(0.3)); v.SetWidth(M(0.5)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(net); b.Add(v)
print('added track+via')
try:
    n2 = b.FindNet('+5V')
    print('FindNet after Add:', type(n2), n2.GetNetCode() if hasattr(n2,'GetNetCode') else 'NO ATTR')
except Exception as ex:
    print('FindNet after Add FAILED:', ex)
try:
    print('tracks:', len(list(b.GetTracks())))
except Exception as ex:
    print('GetTracks FAILED:', ex)

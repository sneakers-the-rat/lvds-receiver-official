import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp198.kicad_pcb')
code = b.FindNet('+5V').GetNetCode()
hit = []
for t in list(b.GetTracks()):
    if t.GetNetCode() == code and t.GetLayer() == pcbnew.F_Cu and t.Type() == pcbnew.PCB_TRACE_T:
        s, e = t.GetStart(), t.GetEnd()
        if abs(s.x/1e6-41.8)<0.01 and abs(s.y/1e6-51.25)<0.01:
            hit.append(t)
print('matched', len(hit))
for t in hit: b.Remove(t)
try:
    n2 = b.FindNet('SET_P')
    print('FindNet after Remove:', type(n2), n2.GetNetCode() if hasattr(n2,'GetNetCode') else 'NO ATTR')
except Exception as ex:
    print('FindNet after Remove FAILED:', ex)
try:
    print('tracks after remove:', len(list(b.GetTracks())))
except Exception as ex:
    print('GetTracks after Remove FAILED:', ex)
b.Save('scratch/work/dbg2.kicad_pcb')
print('saved ok')

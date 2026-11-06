import pcbnew, math
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp181.kicad_pcb')
mm = lambda v: v/1e6
for fp in b.GetFootprints():
    if fp.GetReference() in ('X1','U4'):
        p = fp.GetPosition()
        print(fp.GetReference(), 'at', round(mm(p.x),2), round(mm(p.y),2), 'rot', fp.GetOrientationDegrees())
        for pad in fp.Pads():
            pp = pad.GetPosition()
            print('   pad', pad.GetNumber(), pad.GetNetname(), 'at', round(mm(pp.x),3), round(mm(pp.y),3))
print('--- CDR_SQUELCH tracks/vias')
for t in b.GetTracks():
    if t.GetNetname() == 'CDR_SQUELCH':
        if isinstance(t, pcbnew.PCB_VIA):
            p = t.GetPosition(); print('  VIA at', round(mm(p.x),3), round(mm(p.y),3))
        else:
            s, e = t.GetStart(), t.GetEnd()
            print('  TRK', t.GetLayerName(), '(', round(mm(s.x),3), round(mm(s.y),3), ')->(', round(mm(e.x),3), round(mm(e.y),3), ') len', round(t.GetLength()/1e6,3), 'w', mm(t.GetWidth()))

import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp201.kicad_pcb')
code = b.FindNet('+3V3D').GetNetCode()
for t in b.GetTracks():
    if t.GetNetCode() == code and t.GetLayer() == pcbnew.F_Cu and t.Type() == pcbnew.PCB_TRACE_T:
        s, e = t.GetStart(), t.GetEnd()
        L = ((e.x-s.x)**2 + (e.y-s.y)**2) ** 0.5 / 1e6
        if abs(L - 1.0) < 0.01:
            print('len1.0 stub: (%.3f,%.3f)->(%.3f,%.3f) w %.2f' % (s.x/1e6, s.y/1e6, e.x/1e6, e.y/1e6, t.GetWidth()/1e6))

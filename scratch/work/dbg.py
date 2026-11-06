import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp198.kicad_pcb')
net = b.FindNet('+5V')
print('findnet code:', net.GetNetCode(), 'class:', type(net))
n=0
for t in b.GetTracks():
    if t.GetNetCode() == net.GetNetCode() and t.GetLayer() == pcbnew.F_Cu and t.Type() == pcbnew.PCB_TRACE_T:
        s,e = t.GetStart(), t.GetEnd()
        if 41 < s.x/1e6 < 43 and 50 < s.y/1e6 < 52:
            print('TRK', s.x, s.y, e.x, e.y, 'mm:', s.x/1e6, s.y/1e6, e.x/1e6, e.y/1e6); n+=1
print('found', n)
print('track count total:', len(list(b.GetTracks())))
t0 = list(b.GetTracks())[0]
print('GetNet type:', type(t0.GetNet()), 'eq findnet:', t0.GetNet() == b.FindNet(t0.GetNetname()))

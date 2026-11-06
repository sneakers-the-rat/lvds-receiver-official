import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp198.kicad_pcb')
def rip(netname, layer, segs):
    code = b.FindNet(netname).GetNetCode()
    hit = []
    for t in list(b.GetTracks()):
        if t.GetNetCode() == code and t.GetLayer() == layer and t.Type() == pcbnew.PCB_TRACE_T:
            s, e = t.GetStart(), t.GetEnd()
            for (x1, y1, x2, y2) in segs:
                if (abs(s.x/1e6-x1)<0.01 and abs(s.y/1e6-y1)<0.01 and abs(e.x/1e6-x2)<0.01 and abs(e.y/1e6-y2)<0.01) or \
                   (abs(e.x/1e6-x1)<0.01 and abs(e.y/1e6-y1)<0.01 and abs(s.x/1e6-x2)<0.01 and abs(s.y/1e6-y2)<0.01):
                    hit.append(t); break
    for t in hit: b.Remove(t)
    print('ripped', netname, len(hit), 'of', len(segs))
rip('+5V', pcbnew.F_Cu, [(41.8,51.25,42.125,50.875),(42.125,50.875,42.125,50.375),(42.125,50.375,42.375,50.125)])
rip('+5V', pcbnew.F_Cu, [(52.375,49.125,52.125,48.875),(52.125,48.875,51.875,48.625),(51.875,48.625,51.875,48.375),(51.875,48.375,52.125,48.125),(52.125,48.125,52.125,47.875),(52.125,47.875,52.2,47.25)])
b.Save('scratch/work/t_c1a.kicad_pcb'); print('saved t_c1a')

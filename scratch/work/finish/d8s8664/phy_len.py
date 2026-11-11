import pcbnew, wx, math
_app = wx.App(False)
b = pcbnew.LoadBoard('hw/pdlvds_rx.kicad_pcb')
for net in ('DM_PHY', 'DP_PHY'):
    total = 0.0; vias = 0; layers = {}
    for t in b.GetTracks():
        if t.GetNetname() != net: continue
        if t.Type() == pcbnew.PCB_VIA_T:
            vias += 1; continue
        s, e = t.GetStart(), t.GetEnd()
        L = math.hypot(s.x-e.x, s.y-e.y)/1e6
        total += L
        ln = b.GetLayerName(t.GetLayer())
        layers[ln] = layers.get(ln, 0.0) + L
    print('%s total %.1f mm, vias %d, by layer %s' % (net, total, vias, {k: round(v,1) for k,v in layers.items()}))

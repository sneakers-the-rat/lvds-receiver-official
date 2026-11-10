import sys, pcbnew
src, dst = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard(src)
def mm(v): return pcbnew.ToMM(v)
def M(x): return pcbnew.FromMM(x)
OLD = (22.375, 0.375); NEW = (22.375, 1.875)
moved_via = moved_f = moved_b = 0
for t in list(b.GetTracks()):
    s, e = t.GetStart(), t.GetEnd()
    sp, ep = (mm(s.x), mm(s.y)), (mm(e.x), mm(e.y))
    if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == 'HV_R29M' and abs(sp[0]-OLD[0])<0.01 and abs(sp[1]-OLD[1])<0.01:
        t.SetPosition(pcbnew.VECTOR2I(M(NEW[0]), M(NEW[1]))); moved_via += 1
    elif t.Type() == pcbnew.PCB_TRACK_T and t.GetNetname() == 'HV_R29M':
        # F seg (22.375,0.375)->(22.375,6.125): move its start (the 0.375 end)
        if abs(sp[0]-OLD[0])<0.01 and abs(sp[1]-OLD[1])<0.01:
            t.SetStart(pcbnew.VECTOR2I(M(NEW[0]), M(NEW[1]))); moved_f += 1
        if abs(ep[0]-OLD[0])<0.01 and abs(ep[1]-OLD[1])<0.01:
            t.SetEnd(pcbnew.VECTOR2I(M(NEW[0]), M(NEW[1]))); moved_f += 1
        # B seg (22.375,0.375)->(22.375,-1.125)
        if t.GetLayer() == pcbnew.B_Cu: moved_b += 0  # counted via start/end moves above
print('via moved', moved_via, 'endpoints moved', moved_f)
assert moved_via == 1 and moved_f == 2
filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())
b.Save(dst)
print('saved', dst)

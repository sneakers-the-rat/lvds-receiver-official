import pcbnew, sys
b = pcbnew.LoadBoard(sys.argv[1])
mm = lambda v: v/1e6
print('--- CDR_SQUELCH segs with any pt in x[82,90] y[9,15]')
for t in b.GetTracks():
    if t.GetNetname() != 'CDR_SQUELCH' or isinstance(t, pcbnew.PCB_VIA): continue
    s, e = t.GetStart(), t.GetEnd()
    pts = [(mm(s.x), mm(s.y)), (mm(e.x), mm(e.y))]
    if any(82 <= x <= 90 and 9 <= y <= 15 for x, y in pts):
        print('  ', pts, t.GetLayerName())
print('--- foreign pads in corridor x[82,90] y[11,16]')
for fp in b.GetFootprints():
    for pad in fp.Pads():
        p = pad.GetPosition(); x, y = mm(p.x), mm(p.y)
        if 82 <= x <= 90 and 11 <= y <= 16:
            s = pad.GetSize()
            print('  ', fp.GetReference(), pad.GetNumber(), pad.GetNetname(), (round(x,2), round(y,2)), 'size', round(mm(s.x),2), round(mm(s.y),2))
print('--- foreign tracks crossing y in [12.6,14.2], x in [83,89]')
for t in b.GetTracks():
    if t.GetNetname() == 'CDR_SQUELCH': continue
    if isinstance(t, pcbnew.PCB_VIA):
        p = t.GetPosition(); x, y = mm(p.x), mm(p.y)
        if 83 <= x <= 89 and 12.6 <= y <= 14.2: print('   VIA', t.GetNetname(), (round(x,2), round(y,2)))
        continue
    s, e = t.GetStart(), t.GetEnd()
    pts = [(mm(s.x), mm(s.y)), (mm(e.x), mm(e.y))]
    if any(83 <= x <= 89 and 12.6 <= y <= 14.2 for x, y in pts):
        print('  ', t.GetNetname(), pts, t.GetLayerName())

import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp181.kicad_pcb')
mm = lambda v: v/1e6
doomed = []
for t in list(b.GetTracks()):
    if t.GetNetname() != 'CDR_SQUELCH' or isinstance(t, pcbnew.PCB_VIA):
        continue
    s, e = t.GetStart(), t.GetEnd()
    pts = [(mm(s.x), mm(s.y)), (mm(e.x), mm(e.y))]
    if any(83.8 <= x <= 88.2 and 10.6 <= y <= 13.2 for x, y in pts):
        doomed.append(t)
for t in doomed:
    s, e = t.GetStart(), t.GetEnd()
    print('rip', (round(mm(s.x),3), round(mm(s.y),3)), '->', (round(mm(e.x),3), round(mm(e.y),3)))
    b.Remove(t)
print('ripped', len(doomed))
b.Save('hw/pdlvds_rx.exp181.kicad_pcb')

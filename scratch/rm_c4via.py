import pcbnew
b = pcbnew.LoadBoard('scratch/stitch182.kicad_pcb')
mm = lambda v: v/1e6
kill = []
for t in b.GetTracks():
    if t.GetNetname() != 'GND': continue
    if isinstance(t, pcbnew.PCB_VIA):
        p = t.GetPosition()
        if abs(mm(p.x)-27.5) < 0.01 and abs(mm(p.y)-18.0) < 0.01: kill.append(t)
    else:
        s, e = t.GetStart(), t.GetEnd()
        for q in (s, e):
            if abs(mm(q.x)-26.75) < 0.01 and abs(mm(q.y)-18.0) < 0.01: kill.append(t)
for t in kill: b.Remove(t)
print('removed', len(kill))
b.Save('scratch/stitch182a.kicad_pcb')

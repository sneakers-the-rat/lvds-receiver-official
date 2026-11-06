import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp181.kicad_pcb')
mm = lambda v: v/1e6
for fp in b.GetFootprints():
    if fp.GetReference() == 'X1':
        for pad in fp.Pads():
            s = pad.GetSize(); p = pad.GetPosition()
            print('X1 pad', pad.GetNumber(), pad.GetNetname(), 'pos', round(mm(p.x),2), round(mm(p.y),2), 'size', round(mm(s.x),2), 'x', round(mm(s.y),2), pad.GetShape())
    # what pads are near the squelch chain end?
print('--- pads near (91.5,1.5) and (91.6,8) r=3')
for fp in b.GetFootprints():
    for pad in fp.Pads():
        p = pad.GetPosition(); x, y = mm(p.x), mm(p.y)
        if (abs(x-91.5)<3 and abs(y-1.5)<3) or (abs(x-91.6)<3 and abs(y-8)<3):
            print('  ', fp.GetReference(), pad.GetNumber(), pad.GetNetname(), round(x,2), round(y,2))

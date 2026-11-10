import pcbnew
MM = pcbnew.ToMM
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp252.kicad_pcb')
rows = []
for t in b.GetTracks():
    if t.GetNetname() != 'ULPI_STP':
        continue
    lay = {pcbnew.F_Cu: 'F', pcbnew.In2_Cu: 'In2', pcbnew.B_Cu: 'B'}.get(t.GetLayer(), '?')
    if t.Type() == pcbnew.PCB_VIA_T:
        x, y = MM(t.GetPosition().x), MM(t.GetPosition().y)
        if 74.8 <= x <= 77.0 and -1.7 <= y <= -0.6:
            rows.append((y, x, f'via ({x:.2f},{y:.2f})'))
    else:
        s = (MM(t.GetStart().x), MM(t.GetStart().y)); e = (MM(t.GetEnd().x), MM(t.GetEnd().y))
        cx, cy = (s[0]+e[0])/2, (s[1]+e[1])/2
        if 74.8 <= cx <= 77.0 and -1.7 <= cy <= -0.6:
            rows.append((cy, cx, f'{lay} seg ({s[0]:.2f},{s[1]:.2f})->({e[0]:.2f},{e[1]:.2f})'))
for r in sorted(rows): print(' ', r[2])
print('total', len(rows))

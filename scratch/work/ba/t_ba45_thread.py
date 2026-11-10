"""t_ba45: trace STP's southern B thread on exp252:
all STP items (B and F) with centres in x[75.3,77.9]
y[-0.9,1.5], sorted, to find where the x77.45 thread joins
the kept approach web."""
import pcbnew
MM = pcbnew.ToMM
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp252.kicad_pcb')
rows = []
for t in b.GetTracks():
    if t.GetNetname() != 'ULPI_STP':
        continue
    lay = {pcbnew.F_Cu: 'F', pcbnew.In2_Cu: 'In2',
           pcbnew.B_Cu: 'B'}.get(t.GetLayer(), '?')
    if t.Type() == pcbnew.PCB_VIA_T:
        x, y = MM(t.GetPosition().x), MM(t.GetPosition().y)
        if 75.3 <= x <= 77.9 and -0.9 <= y <= 1.5:
            rows.append((y, x, f'via ({x:.2f},{y:.2f})'))
    else:
        s = (MM(t.GetStart().x), MM(t.GetStart().y))
        e = (MM(t.GetEnd().x), MM(t.GetEnd().y))
        cx, cy = (s[0] + e[0]) / 2, (s[1] + e[1]) / 2
        if 75.3 <= cx <= 77.9 and -0.9 <= cy <= 1.5:
            rows.append((cy, cx, f'{lay} seg ({s[0]:.2f},{s[1]:.2f})->'
                                 f'({e[0]:.2f},{e[1]:.2f})'))
for r in sorted(rows):
    print(' ', r[2])
print('total', len(rows))
print('=== done ===')

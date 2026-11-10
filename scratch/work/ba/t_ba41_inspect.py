"""t_ba41: board geometry at the 3 STP dangling sites on
exp253 (and exp252 for the kept items): STP tracks within
0.7mm of (76.1,13.5), (75.45,13.7), (77.45,0.5)."""
import pcbnew
MM = pcbnew.ToMM

for src in ('hw/pdlvds_rx.exp252.kicad_pcb',
            'hw/pdlvds_rx.exp253.kicad_pcb'):
    print(f'===== {src} =====')
    b = pcbnew.LoadBoard(src)
    pts = [(76.1, 13.5), (75.45, 13.7), (77.45, 0.5)]
    for (px, py) in pts:
        print(f'-- near ({px},{py}) --')
        for t in b.GetTracks():
            if t.GetNetname() != 'ULPI_STP':
                continue
            if t.Type() == pcbnew.PCB_VIA_T:
                x, y = MM(t.GetPosition().x), MM(t.GetPosition().y)
                if abs(x - px) < 0.7 and abs(y - py) < 0.7:
                    print(f'   via ({x:.3f},{y:.3f})')
            else:
                s = (MM(t.GetStart().x), MM(t.GetStart().y))
                e = (MM(t.GetEnd().x), MM(t.GetEnd().y))
                cx, cy = (s[0] + e[0]) / 2, (s[1] + e[1]) / 2
                if abs(cx - px) < 0.7 and abs(cy - py) < 0.7:
                    lay = {pcbnew.F_Cu: 'F', pcbnew.In2_Cu: 'In2',
                           pcbnew.B_Cu: 'B'}[t.GetLayer()]
                    print(f'   {lay} seg ({s[0]:.3f},{s[1]:.3f})->'
                          f'({e[0]:.3f},{e[1]:.3f}) w{MM(t.GetWidth()):.2f}')
print('=== done ===')

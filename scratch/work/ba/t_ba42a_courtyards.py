"""t_ba42a: exact courtyard outlines (file coords) for U7
and C22 from exp252: U7 F_CrtYd south edge in x[74,79.5];
C22 courtyard half-extents."""
import pcbnew
MM = pcbnew.ToMM
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp252.kicad_pcb')
for fp in b.GetFootprints():
    ref = fp.GetReference()
    if ref not in ('U7', 'C22'):
        continue
    pos = fp.GetPosition()
    print(f'{ref} at ({MM(pos.x):.3f},{MM(pos.y):.3f})')
    for layer in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
        ch = fp.GetCourtyard(layer)
        pts = []
        for i in range(ch.OutlineCount()):
            o = ch.Outline(i)
            for j in range(o.PointCount()):
                p = o.CPoint(j)
                pts.append((MM(p.x), MM(p.y)))
        if not pts:
            continue
        lname = 'F' if layer == pcbnew.F_CrtYd else 'B'
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        print(f'  {lname}_CrtYd: x[{min(xs):.3f},{max(xs):.3f}] '
              f'y[{min(ys):.3f},{max(ys):.3f}] npts {len(pts)}')
        if ref == 'U7' and layer == pcbnew.F_CrtYd:
            south = [p for p in pts if 74 <= p[0] <= 79.5]
            south.sort(key=lambda p: p[1])
            print('   U7 F south-most pts:', 
                  [(round(p[0], 3), round(p[1], 3)) for p in south[:6]])
print('=== done ===')

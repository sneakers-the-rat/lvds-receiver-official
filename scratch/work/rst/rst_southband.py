import sys
sys.path.insert(0, 'hw')
import gridroute as GR
items = GR.load_items('hw/pdlvds_rx.exp272.kicad_pcb')
for net in ('ULPI_D0', 'I2C_SCL'):
    print(f'--- {net} items x[73.5,77] y[4.5,7.5]')
    for it in items:
        if it.net != net:
            continue
        pts = [q for q in (it.a, it.b) if q]
        if it.rect:
            pts.append(((it.rect[0] + it.rect[2]) / 2, (it.rect[1] + it.rect[3]) / 2))
        if pts and any(73.5 <= p[0] <= 77 and 4.5 <= p[1] <= 7.5 for p in pts):
            b = f'->({it.b[0]:.3f},{it.b[1]:.3f})' if it.b else ''
            r = f' rect={tuple(round(v, 2) for v in it.rect)}' if it.rect else ''
            a = f'({it.a[0]:.3f},{it.a[1]:.3f})' if it.a else '(rect)'
            print(f'   {it.kind} {it.layer} {a}{b} hw={it.hw:.3f}{r}')

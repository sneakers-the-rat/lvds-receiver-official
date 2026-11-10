import sys
sys.path.insert(0, 'hw')
import gridroute as G
items = G.load_items('hw/pdlvds_rx.exp270.kicad_pcb')
for net in ('ULPI_D5',):
    for it in items:
        if it.net != net:
            continue
        if it.kind == 'trk':
            (ax, ay), (bx, by) = it.a, it.b
            print(f"  trk {it.layer} ({ax:.3f},{ay:.3f})->({bx:.3f},{by:.3f}) w{2*it.hw:.2f}")
        elif it.kind == 'via':
            print(f"  via @({it.a[0]:.3f},{it.a[1]:.3f}) d{2*it.hw:.2f}")

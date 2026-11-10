import sys
sys.path.insert(0, 'hw')
import gridroute as G
items = G.load_items('hw/pdlvds_rx.exp270.kicad_pcb')
for it in items:
    if it.net not in ('+3V3D', 'GND'):
        continue
    if it.kind == 'pad':
        r = it.rect
        cx, cy = (r[0]+r[2])/2, (r[1]+r[3])/2
        if 79.5 <= cx <= 84.5 and 11.5 <= cy <= 15.5:
            print(f"pad {it.net} L{it.layer} rect({r[0]:.3f},{r[1]:.3f},{r[2]:.3f},{r[3]:.3f})")
    elif it.kind == 'trk':
        (ax, ay), (bx, by) = it.a, it.b
        if it.net == '+3V3D' and 79.5 <= (ax+bx)/2 <= 84.5 and 10.5 <= (ay+by)/2 <= 16.5:
            print(f"trk {it.net} {it.layer} ({ax:.3f},{ay:.3f})->({bx:.3f},{by:.3f}) w{2*it.hw:.2f}")
    elif it.kind == 'via':
        cx, cy = it.a
        if it.net == '+3V3D' and 79.5 <= cx <= 84.5 and 10.5 <= cy <= 16.5:
            print(f"via {it.net} @({cx:.3f},{cy:.3f}) d{2*it.hw:.2f}")

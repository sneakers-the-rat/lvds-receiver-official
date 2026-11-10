import sys
sys.path.insert(0, 'hw')
import gridroute as G
items = G.load_items('hw/pdlvds_rx.exp269.kicad_pcb')
BOX = (76.0, 10.0, 81.0, 18.5)
NETS = {'+3V3A', 'I2C_SCL', 'I2C_SDA', 'ULPI_D7', 'ULPI_D6', 'GND', '+3V3D'}
for it in items:
    if it.net not in NETS: continue
    if it.kind == 'trk':
        (ax, ay), (bx, by) = it.a, it.b
        if not (BOX[0] <= (ax+bx)/2 <= BOX[2] and BOX[1] <= (ay+by)/2 <= BOX[3]): continue
        print(f"trk {it.net} {it.layer} ({ax:.3f},{ay:.3f})->({bx:.3f},{by:.3f}) w{2*it.hw:.2f}")
    elif it.kind == 'via':
        cx, cy = it.a
        if not (BOX[0] <= cx <= BOX[2] and BOX[1] <= cy <= BOX[3]): continue
        print(f"via {it.net} @({cx:.3f},{cy:.3f}) d{2*it.hw:.2f}")
    elif it.kind == 'pad' and it.layer == 'F':
        r = it.rect
        cx, cy = (r[0]+r[2])/2, (r[1]+r[3])/2
        if not (BOX[0] <= cx <= BOX[2] and BOX[1] <= cy <= BOX[3]): continue
        print(f"pad {it.net} rect({r[0]:.3f},{r[1]:.3f},{r[2]:.3f},{r[3]:.3f})")

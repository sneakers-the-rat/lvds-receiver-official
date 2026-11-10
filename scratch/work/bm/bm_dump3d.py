import sys
sys.path.insert(0, 'hw')
import gridroute as G
items = G.load_items('hw/pdlvds_rx.exp270.kicad_pcb')
BOX = (78.4, 9.8, 82.2, 17.2)
NETS = {'ULPI_D0','ULPI_D1','ULPI_D2','ULPI_D3','ULPI_D4','ULPI_D5','ULPI_D6','+3V3D','NRST'}
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

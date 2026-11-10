import sys
sys.path.insert(0, 'hw')
import gridroute as G
items = G.load_items('hw/pdlvds_rx.exp269.kicad_pcb')
def show(net, box=None):
    print(f"== {net} ==")
    for it in items:
        if it.net != net: continue
        if it.kind == 'trk':
            (ax, ay), (bx, by) = it.a, it.b
            if box and not (box[0] <= (ax+bx)/2 <= box[2] and box[1] <= (ay+by)/2 <= box[3]): continue
            print(f"trk {it.layer} ({ax:.3f},{ay:.3f})->({bx:.3f},{by:.3f}) w{2*it.hw:.2f}")
        elif it.kind == 'via':
            print(f"via @({it.a[0]:.3f},{it.a[1]:.3f}) d{2*it.hw:.2f}")
        elif it.kind == 'pad':
            r = it.rect
            print(f"pad {it.layer} rect({r[0]:.3f},{r[1]:.3f},{r[2]:.3f},{r[3]:.3f})")
show('ULPI_D7')
show('I2C_SCL', (76.0, 5.0, 82.0, 22.0))
print("== anything at (78.875,10.375) ==")
for it in items:
    if it.kind in ('via','pad'):
        c = it.a if it.kind=='via' else ((it.rect[0]+it.rect[2])/2,(it.rect[1]+it.rect[3])/2)
        if abs(c[0]-78.875)<0.6 and abs(c[1]-10.375)<0.6:
            print(it.kind, it.net, it.layer, c, getattr(it,'rect',''))

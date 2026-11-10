import sys
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch/work/bm')
import gridroute as G
items = G.load_items('hw/pdlvds_rx.exp268.kicad_pcb')
def show(net=None, layers=('F',), box=(73.0, 8.0, 78.0, 12.2)):
    for it in items:
        if net and it.net != net: continue
        lay = getattr(it, 'layer', None)
        if lay not in layers: continue
        if it.kind == 'trk':
            (ax, ay), (bx, by) = it.a, it.b
            if box and not (box[0] <= (ax+bx)/2 <= box[2] and box[1] <= (ay+by)/2 <= box[3]): continue
            print(f"trk {it.net} {lay} ({ax:.3f},{ay:.3f})->({bx:.3f},{by:.3f}) w{2*it.hw}")
        elif it.kind == 'via':
            cx, cy = it.a
            if box and not (box[0] <= cx <= box[2] and box[1] <= cy <= box[3]): continue
            print(f"via {it.net} @({cx:.3f},{cy:.3f}) d{2*it.hw}")
        elif it.kind == 'pad':
            r = it.rect
            if box and not (box[0] <= (r[0]+r[2])/2 <= box[2] and box[1] <= (r[1]+r[3])/2 <= box[3]): continue
            print(f"pad {it.net} {lay} rect({r[0]:.3f},{r[1]:.3f},{r[2]:.3f},{r[3]:.3f})")
print("== XO all F =="); show('XO', ('F',), None)
print("== XI F+B =="); show('XI', ('F','B'), None)
print("== all F in south box =="); show(None, ('F',))

import sys
sys.path.insert(0, 'hw')
import gridroute as GR

items = GR.load_items('hw/pdlvds_rx.exp272.kicad_pcb')
def inbox(it):
    pts = [q for q in (it.a, it.b) if q]
    if it.rect:
        pts.append(((it.rect[0] + it.rect[2]) / 2, (it.rect[1] + it.rect[3]) / 2))
    return any(69.0 <= p[0] <= 79.0 and 2.5 <= p[1] <= 21.5 for p in pts)
sel = [it for it in items if inbox(it)]
from collections import defaultdict
by = defaultdict(list)
for it in sel:
    by[it.net].append(it)
for net in sorted(by):
    print(f'== {net} ({len(by[net])})')
    for it in sorted(by[net], key=lambda z: (z.kind, z.layer, z.a or (0, 0))):
        b = f'->({it.b[0]:.3f},{it.b[1]:.3f})' if it.b else ''
        r = f' rect={tuple(round(v,3) for v in it.rect)}' if it.rect else ''
        a = f'({it.a[0]:.3f},{it.a[1]:.3f})' if it.a else '(rect)'
        print(f'   {it.kind} {it.layer} {a}{b} hw={it.hw:.3f}{r}')

import sys
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch/heal8')
import wx
_app = wx.App(False)
import pcbnew
import repair
from router import netclass, cell_of, CELL, OY
from router6 import seg_margin, via_margin, via_size, _neck_hw, SAFE
b = pcbnew.LoadBoard('scratch/work/t_aa8.kicad_pcb')
items, pad_cells = repair.build_items(b)
groups = repair.compute_groups(b)
def centre(n): return ((n[1] + 0.5) * CELL, (n[2] + 0.5) * CELL + OY)
for net in ['ULPI_DIR', 'ULPI_NXT']:
    w, clr = netclass(net)
    vr = via_size(w)[0] / 2
    gs = sorted(groups[net], key=len, reverse=True)
    main = gs[0]
    print(f"== {net} main group items: {[it.desc for it in main]}")
    cells = set()
    for it in main: cells |= it.cells
    for c in sorted(cells):
        ctr = centre(c)
        # can a track step into this cell centre from each neighbour?
        ok = []
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
            nb = (c[0], c[1]+dx, c[2]+dy)
            nc = centre(nb)
            m = seg_margin(items, c[0], net, clr, nc[0], nc[1], ctr[0], ctr[1], w/2)
            if m >= SAFE: ok.append((dx, dy, round(m, 2)))
        vm = via_margin(items, net, clr, ctr[0], ctr[1], vr)
        print(f"   cell L{c[0]} ({ctr[0]:.3f},{ctr[1]:.3f}) enterable_from={ok} via_margin_at_centre={vm:+.3f}")

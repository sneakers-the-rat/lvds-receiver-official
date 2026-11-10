import sys, math
sys.path.insert(0, 'hw')
import pcbnew, repair, router6
from ripup import seg_dist
from diagnose_groups import fanout_targets
from router import netclass, cell_of, W, H

def bfs(items, net, width, clr, neck_pts, anchors, seeds, cap=600000):
    vr = router6.via_size(width)[0] / 2
    seen = set(seeds); frontier = list(seen)
    steps = ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1))
    while frontier and len(seen) < cap:
        nxt = []
        for (li, cx, cy) in frontier:
            ax, ay = (cx + 0.5) * router6.CELL, (cy + 0.5) * router6.CELL
            for dx, dy in steps:
                nx, ny = cx + dx, cy + dy
                if not (0 <= nx < W and 0 <= ny < H): continue
                nb = (li, nx, ny)
                if nb in seen: continue
                bx, by = (nx + 0.5) * router6.CELL, (ny + 0.5) * router6.CELL
                hw_ = router6._neck_hw(width, ax, ay, bx, by, neck_pts)
                if router6.seg_margin(items, li, net, clr, ax, ay, bx, by, hw_) < router6.SAFE: continue
                seen.add(nb); nxt.append(nb)
            if 2 <= cx <= W - 3 and 2 <= cy <= H - 3:
                vx, vy = (cx + 0.5) * router6.CELL, (cy + 0.5) * router6.CELL
                if router6.via_margin(items, net, clr, vx, vy, vr) >= router6.SAFE:
                    for lj in range(3):
                        nb = (lj, cx, cy)
                        if nb not in seen: seen.add(nb); nxt.append(nb)
        frontier = nxt
    return seen

b = pcbnew.LoadBoard('hw/pdlvds_rx.fr1r.s2.kicad_pcb')
items, pad_cells = repair.build_items(b)
net = '+3V3A'; width, clr = netclass(net)
pos = [p for d, cs, p in pad_cells[net] if d == 'U7.25']
cands = []
for t in b.GetTracks():
    if t.GetNetname() == net: continue
    d = min(seg_dist(px, py, t) for px, py in pos)
    if d < 2.0: cands.append((d, t))
cands.sort(key=lambda x: x[0])
for d, t in cands[:12]: b.Remove(t)
items, pad_cells = repair.build_items(b)
neck_pts = [p[2] for p in pad_cells[net]]
anchors = {}
for _d, cs, p in pad_cells[net]:
    for c in cs: anchors[c] = p
groups = repair.compute_groups(b)
gs = sorted(groups[net], key=len, reverse=True)
print('main group items:', [it.desc for it in gs[0]][:14], '... total', len(gs[0]))
g = [gg for gg in groups[net] if any(it.desc == 'U7.25' and it.kind == 'pad' for it in gg)][0]
starts = []
for it in g:
    if it.kind == 'pad': starts += list(it.cells)
ft = set()
for s in starts:
    if s in anchors: ft |= fanout_targets(items, s, anchors[s], net, width, clr, neck_pts)
reach_pad = bfs(items, net, width, clr, neck_pts, anchors, set(starts) | ft)
print('reach from U7.25 (ripped):', len(reach_pad))
main_cells = set()
for it in gs[0]: main_cells |= it.cells
reach_main = bfs(items, net, width, clr, neck_pts, anchors, main_cells)
print('reach from main group:', len(reach_main))
inter = reach_pad & reach_main
print('reaches intersect:', len(inter))
if not inter:
    best = min((abs(a[1]-c[1]) + abs(a[2]-c[2]) for a in reach_pad for c in reach_main if a[0] == c[0]), default=None)
    print('min same-layer cell gap between reaches:', best)

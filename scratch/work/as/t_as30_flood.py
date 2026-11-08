"""t_as30: passability flood in the exact item model for the CAP nets.
Per layer: G(cell) = min over foreign items of dist_to_item - pair_clr.
Track-passable: G >= 0.10 (w0.2 track). Via-fit: min over layers G >= 0.25.
Components per layer + via-graph BFS from escape via to target pad edge.
Writes ASCII maps flood_CAP_CLK.txt / flood_CAP_DATA.txt."""
import wx
_app = wx.App(False)
import pcbnew, sys, math
import numpy as np
from scipy import ndimage
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
import t_ai_lib as L
from router import netclass

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
items = L.load_items(board)

X0, X1, Y0, Y1, ST = 63.0, 79.5, -3.0, 29.5, 0.05
xs = np.arange(X0, X1 + 1e-9, ST)
ys = np.arange(Y0, Y1 + 1e-9, ST)
GX, GY = np.meshgrid(xs, ys)  # shape (ny, nx)

def item_dist_field(it, GX, GY):
    kind, net, d = it[0], it[1], it[2]
    if kind == 'pad':
        cx, cy, hw, hh, rot = d
        dx, dy = GX - cx, GY - cy
        c, s = math.cos(-rot), math.sin(-rot)
        lx, ly = dx * c - dy * s, dx * s + dy * c
        ex = np.maximum(np.abs(lx) - hw, 0.0)
        ey = np.maximum(np.abs(ly) - hh, 0.0)
        return np.hypot(ex, ey)
    if kind == 'seg':
        x1, y1, x2, y2, hw = d
        px, py = GX - x1, GY - y1
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else np.clip((px * dx + py * dy) / L2, 0, 1)
        return np.hypot(px - t * dx, py - t * dy) - hw
    cx, cy, r = d
    return np.hypot(GX - cx, GY - cy) - r

def item_bbox(it):
    kind, d = it[0], it[2]
    if kind == 'pad':
        cx, cy, hw, hh, rot = d
        r = math.hypot(hw, hh)
        return cx - r, cx + r, cy - r, cy + r
    if kind == 'seg':
        return (min(d[0], d[2]) - d[4], max(d[0], d[2]) + d[4],
                min(d[1], d[3]) - d[4], max(d[1], d[3]) + d[4])
    return d[0] - d[2], d[0] + d[2], d[1] - d[2], d[1] + d[2]

CASES = {
    'CAP_CLK':  dict(start=(70.02, 1.83), target=(75.45, 25.385)),
    'CAP_DATA': dict(start=(69.90, 3.18), target=(75.45, 22.845)),
}

for net, case in CASES.items():
    myclr = netclass(net)[1]
    G = {}
    for l in range(3):
        field = np.full(GX.shape, 9.9)
        for it in items[l]:
            if it[1] == net:
                continue
            bx0, bx1, by0, by1 = item_bbox(it)
            req = max(myclr, it[3])
            if bx1 < X0 - req - 0.3 or bx0 > X1 + req + 0.3 or \
               by1 < Y0 - req - 0.3 or by0 > Y1 + req + 0.3:
                continue
            field = np.minimum(field, item_dist_field(it, GX, GY) - req)
        G[l] = field
    track = {l: G[l] >= 0.10 for l in range(3)}
    viafit = (np.minimum(np.minimum(G[0], G[1]), G[2]) >= 0.25)
    # components per layer
    comp = {}
    ncomp = {}
    for l in range(3):
        lab, n = ndimage.label(track[l], structure=np.ones((3, 3)))
        comp[l] = lab
        ncomp[l] = n
    def cell(x, y):
        return (int(round((y - Y0) / ST)), int(round((x - X0) / ST)))
    # BFS over (layer, comp) via via-fit cells
    from collections import deque
    start_nodes = set()
    sy, sx = cell(*case['start'])
    for l in range(3):
        if track[l][sy, sx]:
            start_nodes.add((l, comp[l][sy, sx]))
    ty, tx = cell(*case['target'])
    target_node = (0, comp[0][ty, tx]) if track[0][ty, tx] else None
    # via edges: for each via-fit cell, layers where track-passable
    via_cells = np.argwhere(viafit)
    adj = {}
    def add_edge(a, b, at):
        adj.setdefault(a, []).append((b, at))
        adj.setdefault(b, []).append((a, at))
    for (cy, cx) in via_cells:
        ls = [l for l in range(3) if track[l][cy, cx]]
        for i in range(len(ls)):
            for j in range(i + 1, len(ls)):
                add_edge((ls[i], comp[ls[i]][cy, cx]),
                         (ls[j], comp[ls[j]][cy, cx]),
                         (xs[cx], ys[cy]))
    prev = {}
    dq = deque()
    for sn in start_nodes:
        prev[sn] = None
        dq.append(sn)
    found = None
    while dq:
        node = dq.popleft()
        if node == target_node:
            found = node
            break
        for nb, at in adj.get(node, []):
            if nb not in prev:
                prev[nb] = (node, at)
                dq.append(nb)
    print(f"== {net}: start comps {sorted(start_nodes)} target {target_node} "
          f"REACHABLE={found is not None}")
    path = []
    if found:
        node = found
        while prev[node] is not None:
            node, at = prev[node]
            path.append((node, at))
        path.reverse()
        print("   via transitions (layer,comp) -> at (x,y):")
        cur = None
        for node, at in path:
            print(f"     -> L{node[0]} comp {node[1]} via at ({at[0]:.2f},{at[1]:.2f})")
    # ASCII map: R = reachable comp, . = other passable, # blocked,
    # v = via-fit in reachable comp, S/T markers
    reach = set(n for n in prev)
    lines = []
    for l in range(3):
        lines.append(f"-- {net} layer {l} (0=F 1=In2 2=B)")
        for iy in range(len(ys) - 1, -1, -4):
            row = []
            for ix in range(0, len(xs), 4):
                x, y = xs[ix], ys[iy]
                if (ix, iy) == (sx, sy):
                    row.append('S')
                elif l == 0 and (ix, iy) == (tx, ty):
                    row.append('T')
                elif not track[l][iy, ix]:
                    row.append('#')
                elif (l, comp[l][iy, ix]) in reach:
                    row.append('v' if viafit[iy, ix] else 'R')
                else:
                    row.append('.')
            lines.append(f"y={ys[iy]:6.2f} " + ''.join(row))
        lines.append("        " + ''.join(
            str(int(xs[ix]) % 10) if ix % 20 == 0 else ' '
            for ix in range(0, len(xs), 4)))
    fn = f"scratch/work/as/flood_{net}.txt"
    open(fn, 'w').write('\n'.join(lines))
    print(f"   map written {fn}; comps per layer {ncomp}")

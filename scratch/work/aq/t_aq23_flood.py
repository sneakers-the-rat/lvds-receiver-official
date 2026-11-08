"""t_aq23: replicate groute's grid for one net; report flood extent
from the start pad and from the goal pad (bidirectional diagnosis)."""
import sys, wx
_app = wx.App(False)
import pcbnew, math, heapq
sys.path.insert(0, 'hw')
import repair
from router import netclass, dist_to_item

SRC = 'hw/pdlvds_rx.exp236prep.kicad_pcb'
NET, SP, GP = sys.argv[1], sys.argv[2], sys.argv[3]
X0, X1, Y0, Y1 = 64.0, 98.0, -23.0, 12.0
CELL = 0.125
EPS = 0.004
board = pcbnew.LoadBoard(SRC)
items, _pc = repair.build_items(board)
pad_item = {}
for it in items:
    if it['kind'] == 'pad':
        pad_item[it['desc']] = it
by_layer = [[], [], []]
for it in items:
    for li in range(3):
        if li in it['layers']:
            by_layer[li].append(it)

def pair_clr(a, b):
    return max(netclass(a), netclass(b))

def pt_clear(li, x, y, net, rad):
    for it in by_layer[li]:
        if it['net'] == net:
            continue
        d = dist_to_item(it, x, y) - rad - pair_clr(net, it['net'])
        if d < EPS:
            return False
    return True

NX = int((X1 - X0) / CELL) + 1
NY = int((Y1 - Y0) / CELL) + 1
def cxy(i, j):
    return (X0 + i * CELL, Y0 + j * CELL)

trk = [[[False] * NY for _ in range(NX)] for _ in range(3)]
viaok = [[False] * NY for _ in range(NX)]
for i in range(NX):
    for j in range(NY):
        x, y = cxy(i, j)
        for li in range(3):
            trk[li][i][j] = pt_clear(li, x, y, NET, 0.1)
        viaok[i][j] = all(pt_clear(li, x, y, NET, 0.25) for li in range(3))

def cells_of(desc):
    out = []
    for i in range(NX):
        for j in range(NY):
            x, y = cxy(i, j)
            if dist_to_item(pad_item[desc], x, y) <= 0.03:
                out.append((i, j))
    return out

def flood(seeds, label):
    seen = set()
    dq = []
    for (i, j) in seeds:
        for li in range(3):
            seen.add((i, j, li)); dq.append((i, j, li))
    # seeds start on F per groute; allow all layers here for diagnosis
    # of layer reachability separately: rerun restricted below.
    while dq:
        i, j, li = dq.pop()
        if viaok[i][j]:
            for nl in range(3):
                if nl != li and (i, j, nl) not in seen:
                    seen.add((i, j, nl)); dq.append((i, j, nl))
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                if di == 0 and dj == 0:
                    continue
                ni, nj = i + di, j + dj
                if not (0 <= ni < NX and 0 <= nj < NY):
                    continue
                if not trk[li][ni][nj]:
                    continue
                if di and dj and not (trk[li][i][nj] and trk[li][ni][j]):
                    continue
                if (ni, nj, li) not in seen:
                    seen.add((ni, nj, li)); dq.append((ni, nj, li))
    xs = [cxy(i, j)[0] for (i, j, l) in seen]
    ys = [cxy(i, j)[1] for (i, j, l) in seen]
    print(f'{label}: {len(seen)} cells x[{min(xs):.1f},{max(xs):.1f}] '
          f'y[{min(ys):.1f},{max(ys):.1f}]')
    return seen

ss = cells_of(SP); gs = cells_of(GP)
print('start cells', len(ss), 'goal cells', len(gs))
flood(ss, 'from START (all-layer seeds)')
flood(gs, 'from GOAL (all-layer seeds)')

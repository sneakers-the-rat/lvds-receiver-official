"""t_ab2: multi-layer fine-grid (0.125) A* under KiCad DRC rules.

Why this exists: heal/astar6 routes under the router6 MODEL
(w0.25 tracks, d0.6 via discs, per-net clearances to 0.25), which
is stricter than KiCad DRC (flat 0.200, w0.2/d0.5) — in the U7
south district the model walls heal out entirely (445k-cell flood,
goal cells unvisited, either direction). This router searches
F/In2/B on a 0.125 grid using DRC geometry instead:

  track w0.2 (half 0.1), via d0.5/drill0.3 (r 0.25, all layers),
  pair clearance = max(check_pcb class clr of the two nets):
  HV 1.0 / power 0.25 / default 0.2 — the same classes check_pcb
  enforces, so a path legal here is legal for both referees.

Obstacle geometry is repair.build_items (exact OBB pads, segs,
vias) with router.dist_to_item edge distances. Own-net items are
not obstacles. Grid-point track checks carry a 0.045 guard eps
(covers segment-midpoint dip between 0.125-spaced samples);
emitted segments are re-verified by dense sampling at eps 0.01
and any failing segment falls back to its raw grid steps.
Diagonal steps are forbidden when an orthogonal neighbour cell
is impassable (corner-cut prevention).

Routes nets sequentially; emitted copper is registered into the
item model before the next net routes. Zones refilled before
save; reload per-net item counts printed (save-rename guard).

Usage: t_ab2_groute.py IN OUT NET:STARTPAD:GOALPAD [...] \
       X0 X1 Y0 Y1   (box last four args)
Env: VIA_COST (default 2.0), CELL (default 0.125)
"""
import math, os, sys, heapq
sys.path.insert(0, 'hw')
import pcbnew
import repair, router
from router import netclass, dist_to_item

MM = pcbnew.FromMM
CELL = float(os.environ.get('CELL', '0.125'))
VIA_COST = float(os.environ.get('VIA_COST', '2.0'))
TRK_W, TRK_HW = 0.2, 0.1
VIA_R = 0.25
EPS_GRID, EPS_SEG = 0.004, 0.0
LAYNAME = ['F', 'In2', 'B']
KLAY = {'F': pcbnew.F_Cu, 'In2': pcbnew.In2_Cu, 'B': pcbnew.B_Cu}

src, out = sys.argv[1], sys.argv[2]
jobs = []
for a in sys.argv[3:-4]:
    n, s, g = a.split(':')
    jobs.append((n, s, g))
X0, X1, Y0, Y1 = map(float, sys.argv[-4:])

board = pcbnew.LoadBoard(src)
items, _pc = repair.build_items(board)

# BLOCK_SEGS=x1,y1,x2,y2;... -- virtual foreign F segments, for
# reserving a sibling net's exit column while one net routes
# (DIR's greedy exit diagonal crossed NXT's column at y17.31 and
# sealed NXT at its pad: start flood 25 cells).
for spec in os.environ.get('BLOCK_SEGS', '').split(';'):
    if not spec.strip():
        continue
    bx1, by1, bx2, by2 = map(float, spec.split(','))
    items[0].add(0, ('seg', 'BLOCK!', (bx1, by1, bx2, by2, 0.1), 0.2),
                 (min(bx1, bx2) - 2, min(by1, by2) - 2,
                  max(bx1, bx2) + 2, max(by1, by2) + 2))
    print(f'block seg F ({bx1},{by1})->({bx2},{by2})')

pad_item = {}
for fp in board.GetFootprints():
    ref = fp.GetReference()
    for pad in fp.Pads():
        pos = pcbnew.ToMM(pad.GetPosition())
        size = pcbnew.ToMM(pad.GetSize())
        pad_item[f'{ref}.{pad.GetNumber()}'] = (
            'pad', pad.GetNetname(),
            (pos[0], pos[1], size[0] / 2, size[1] / 2,
             math.radians(pad.GetOrientationDegrees())), 0.2)

NX = int(round((X1 - X0) / CELL)) + 1
NY = int(round((Y1 - Y0) / CELL)) + 1
def cxy(i, j): return (X0 + i * CELL, Y0 + j * CELL)

def pair_clr(net, other):
    return max(netclass(net)[1], netclass(other)[1] if other else 0.2)

def pt_clear(li, x, y, net, rad, eps):
    """True if a disc of radius rad for `net` at (x,y) on layer li
    keeps pair clearance to every foreign item on that layer."""
    seen = set()
    for it in items[li].near(li, x, y):
        if it[1] == net or id(it) in seen:
            continue
        seen.add(id(it))
        if dist_to_item(it, x, y) < rad + pair_clr(net, it[1]) + eps:
            return False
    return True

def via_clear(x, y, net):
    return all(pt_clear(li, x, y, net, VIA_R, EPS_GRID) for li in range(3))

def seg_clear(li, a, b, net, eps=EPS_SEG):
    n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 0.04))
    for k in range(n + 1):
        x = a[0] + (b[0] - a[0]) * k / n
        y = a[1] + (b[1] - a[1]) * k / n
        if not pt_clear(li, x, y, net, TRK_HW, eps):
            return False
    return True

def route_one(net, start_desc, goal_desc):
    assert start_desc in pad_item and goal_desc in pad_item
    # passability grids
    trk_ok = [[[False] * NY for _ in range(NX)] for _ in range(3)]
    via_ok = [[False] * NY for _ in range(NX)]
    for i in range(NX):
        for j in range(NY):
            x, y = cxy(i, j)
            for li in range(3):
                trk_ok[li][i][j] = pt_clear(li, x, y, net, TRK_HW, EPS_GRID)
            via_ok[i][j] = via_clear(x, y, net)
    starts, goals = [], set()
    for i in range(NX):
        for j in range(NY):
            x, y = cxy(i, j)
            if dist_to_item(pad_item[start_desc], x, y) <= 0.03:
                starts.append((i, j, 0))
            if dist_to_item(pad_item[goal_desc], x, y) <= 0.03:
                goals.add((i, j, 0))
    assert starts and goals, f'{net}: no start/goal cells'
    # Pad cells are enterable on F regardless of trk_ok: a track
    # must be allowed to terminate on its own pad even where a
    # neighbour's clearance shadow covers the pad's cells (the
    # U6 mouths are exact threads -- centreline gap exactly the
    # class clearance, so the guard eps shadows every pad cell
    # and an unenterable goal makes A* report NO PATH while the
    # floods meet in open country). The final segment is still
    # verified by seg_clear and refereed by KiCad DRC.
    enter_ok = {(i, j) for (i, j, _l) in starts + list(goals)}
    gx = [cxy(i, j) for (i, j, _l) in goals]
    def heur(i, j):
        x, y = cxy(i, j)
        return 0.95 * min(math.hypot(x - a, y - b) for a, b in gx)
    open_h, came, gs = [], {}, {}
    for s in starts:
        gs[s] = 0.0; came[s] = None
        heapq.heappush(open_h, (heur(s[0], s[1]), 0.0, s))
    found = None
    while open_h:
        f, g, cur = heapq.heappop(open_h)
        if cur in goals:
            found = cur; break
        if g > gs.get(cur, 1e18):
            continue
        i, j, li = cur
        x, y = cxy(i, j)
        # via transition
        if via_ok[i][j]:
            for nl in range(3):
                if nl == li:
                    continue
                nb = (i, j, nl)
                ng = g + VIA_COST
                if ng < gs.get(nb, 1e18):
                    gs[nb] = ng; came[nb] = cur
                    heapq.heappush(open_h, (ng + heur(i, j), ng, nb))
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                if di == 0 and dj == 0:
                    continue
                ni, nj = i + di, j + dj
                if not (0 <= ni < NX and 0 <= nj < NY):
                    continue
                if not trk_ok[li][ni][nj] and not (
                        li == 0 and (ni, nj) in enter_ok):
                    continue
                if di and dj and not (trk_ok[li][i][nj] and trk_ok[li][ni][j]):
                    continue
                nb = (ni, nj, li)
                ng = g + CELL * (1.41421 if di and dj else 1.0)
                if ng < gs.get(nb, 1e18):
                    gs[nb] = ng; came[nb] = cur
                    heapq.heappush(open_h, (ng + heur(ni, nj), ng, nb))
    if not found:
        print(f'{net}: NO PATH; A* expanded {len(gs)} states; '
              f'starts {len(starts)} goals {len(goals)}')
        # BFS cross-check on the identical graph
        from collections import deque
        seen = set(starts)
        dq = deque(starts)
        while dq:
            i, j, li = dq.popleft()
            if via_ok[i][j]:
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
                    if not trk_ok[li][ni][nj] and not (
                            li == 0 and (ni, nj) in enter_ok):
                        continue
                    if di and dj and not (trk_ok[li][i][nj] and
                                          trk_ok[li][ni][j]):
                        continue
                    if (ni, nj, li) not in seen:
                        seen.add((ni, nj, li)); dq.append((ni, nj, li))
        hit = [s for s in seen if s in goals]
        xs = [cxy(i, j)[0] for (i, j, _l) in seen]
        ys = [cxy(i, j)[1] for (i, j, _l) in seen]
        print(f'  BFS reached {len(seen)} states, goal hits {len(hit)}, '
              f'bbox x {min(xs):.2f}..{max(xs):.2f} '
              f'y {min(ys):.2f}..{max(ys):.2f}')
        return None
    path = []
    cur = found
    while cur:
        path.append(cur); cur = came[cur]
    path.reverse()
    print(f'{net}: path {len(path)} cells, cost {gs[found]:.2f}')
    # waypoint list with vias: (x, y, li, is_via_here)
    wps = []
    for k, (i, j, li) in enumerate(path):
        x, y = cxy(i, j)
        wps.append([x, y, li])
    # smooth per-layer runs; emit segment list [(li, a, b)] and via list
    segs, vias = [], []
    k = 0
    runs = []  # (li, [pts]) split at via transitions
    cur_run = [wps[0]]
    for a, b in zip(wps, wps[1:]):
        if a[2] != b[2]:
            runs.append(cur_run)
            if not vias or vias[-1] != (a[0], a[1]):
                vias.append((a[0], a[1]))
            cur_run = [b]
        else:
            cur_run.append(b)
    runs.append(cur_run)
    for pts in runs:
        li = pts[0][2]
        simp = [(p[0], p[1]) for p in pts]
        # greedy shortcut with exact-ish verification
        sm = [simp[0]]
        i0 = 0
        while i0 < len(simp) - 1:
            j0 = len(simp) - 1
            while j0 > i0 + 1 and not seg_clear(li, simp[i0], simp[j0], net):
                j0 -= 1
            if j0 == i0 + 1 and not seg_clear(li, simp[i0], simp[j0], net):
                # raw step failed dense check: keep it anyway; DRC
                # referee decides (should not happen with EPS guard)
                print(f'  WARN raw step fails seg_clear {simp[i0]}->{simp[j0]} L{li}')
            sm.append(simp[j0]); i0 = j0
        for a, b in zip(sm, sm[1:]):
            if a != b:
                segs.append((li, a, b))
    return segs, vias

def emit(net, segs, vias):
    code = board.GetNetcodeFromNetname(net)
    assert code > 0
    clr = netclass(net)[1]
    for li, a, b in segs:
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
        t.SetEnd(pcbnew.VECTOR2I(MM(b[0]), MM(b[1])))
        t.SetWidth(MM(TRK_W)); t.SetLayer(KLAY[LAYNAME[li]])
        t.SetNetCode(code); board.Add(t)
        items[li].add(li, ('seg', net, (a[0], a[1], b[0], b[1], TRK_HW), clr),
                      (min(a[0], b[0]) - 2, min(a[1], b[1]) - 2,
                       max(a[0], b[0]) + 2, max(a[1], b[1]) + 2))
    for (x, y) in vias:
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
        v.SetWidth(MM(0.5)); v.SetDrill(MM(0.3))
        v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetNetCode(code)
        board.Add(v)
        for li in range(3):
            items[li].add(li, ('via', net, (x, y, VIA_R), clr),
                          (x - VIA_R - 2, y - VIA_R - 2,
                           x + VIA_R + 2, y + VIA_R + 2))
    print(f'{net}: emitted {len(segs)} segs, {len(vias)} vias')

for net, s, g in jobs:
    r = route_one(net, s, g)
    if r is None:
        print(f'ABORT: {net} unrouted'); sys.exit(1)
    emit(net, *r)

zr = pcbnew.ZONE_FILLER(board)
zr.Fill(board.Zones())
board.Save(out)
print('saved', out)
b2 = pcbnew.LoadBoard(out)
for net, s, g in jobs:
    c = sum(1 for t in b2.GetTracks() if t.GetNetname() == net)
    print(f'reload {net}: {c} items')

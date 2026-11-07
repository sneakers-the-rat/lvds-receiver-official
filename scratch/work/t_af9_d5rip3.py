"""t_af9: D5 joint re-fanout with DEEP In2 rip (3 staircase segs
each for D4/D6) and grouted connectors.

Rationale (af7 maps): with only the first In2 seg ripped, the
KEPT staircase segs fence the via pocket (D5's margin at its best
point is bound by D4's kept seg2; everything east is bound by
D6's kept seg2). Rip D4/D6 In2 segs 1-3 instead:

  anchors: A4=(80.625,13.875) on kept D4 seg4,
           A6=(81.625,13.875) on kept D6 seg4

Vias + F stubs searched as in t_af4 (F statics are unchanged by
the deeper In2 rip). Connectors are NOT parametrized: a
single-layer DRC-rule A* (t_ab2 machinery, 0.125 grid) routes
each net's In2 run via->anchor sequentially (D4, D6, then D5
toward the district exit at x>=84.25 or y<=11.25), with emitted
paths registered as obstacles for the next net. A combo is
feasible only if all three groute runs succeed and every
pairwise margin (exact item model) is >= 0.

Usage: xvfb-run -a python3 scratch/work/t_af9_d5rip3.py BOARD
"""
import math, sys, heapq
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
from router import netclass, dist_to_item

MM = pcbnew.ToMM
LAYERS = [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
src = sys.argv[1] if len(sys.argv) > 1 else 'hw/pdlvds_rx.exp216.kicad_pcb'
board = pcbnew.LoadBoard(src)

items = {0: [], 1: [], 2: []}
for fp in board.GetFootprints():
    for pad in fp.Pads():
        net = pad.GetNetname()
        x, y = MM(pad.GetPosition())
        sx, sy = MM(pad.GetSize())
        data = (x, y, sx / 2, sy / 2, math.radians(pad.GetOrientationDegrees()))
        clr = netclass(net)[1] if net else 0.2
        for li, ln in enumerate(LAYERS):
            if pad.IsOnLayer(ln):
                items[li].append(('pad', net, data, clr))
for t in board.GetTracks():
    net = t.GetNetname()
    clr = netclass(net)[1] if net else 0.2
    if isinstance(t, pcbnew.PCB_VIA):
        x, y = MM(t.GetPosition())
        r = MM(t.GetWidth()) / 2
        for li in range(3):
            items[li].append(('via', net, (x, y, r), clr))
    else:
        if t.GetLayer() not in LAYERS:
            continue
        li = LAYERS.index(t.GetLayer())
        a = MM(t.GetStart()); b = MM(t.GetEnd())
        w = MM(t.GetWidth())
        items[li].append(('seg', net, (a[0], a[1], b[0], b[1], w / 2), clr))

def close(a, b, tol=0.002):
    return all(abs(x - y) <= tol for x, y in zip(a, b))

D4_IN2 = [(79.625, 14.875, 79.875, 14.625), (79.875, 14.625, 80.125, 14.375),
          (80.125, 14.375, 80.375, 14.125), (80.375, 14.125, 80.625, 13.875)]
D6_IN2 = [(80.625, 14.875, 80.875, 14.625), (80.875, 14.625, 81.125, 14.375),
          (81.125, 14.375, 81.375, 14.125), (81.375, 14.125, 81.625, 13.875)]
RIP_SEGS = {
    'ULPI_D4': [(78.438, 14.25, 78.688, 14.25, 0),
                (78.688, 14.25, 79.125, 14.375, 0),
                (79.125, 14.375, 79.375, 14.625, 0),
                (79.375, 14.625, 79.625, 14.875, 0)]
               + [s + (1,) for s in D4_IN2[:3]],
    'ULPI_D6': [(78.438, 15.25, 78.688, 15.25, 0),
                (78.688, 15.25, 79.125, 15.375, 0),
                (79.125, 15.375, 79.375, 15.625, 0),
                (79.375, 15.625, 79.875, 15.625, 0),
                (79.875, 15.625, 80.125, 15.375, 0),
                (80.125, 15.375, 80.375, 15.125, 0),
                (80.375, 15.125, 80.625, 14.875, 0)]
               + [s + (1,) for s in D6_IN2[:3]],
}
RIP_VIAS = {'ULPI_D4': (79.625, 14.875), 'ULPI_D6': (80.625, 14.875)}
ANCH = {'ULPI_D4': (80.625, 13.875), 'ULPI_D6': (81.625, 13.875)}

def is_ripped(kind, net, data, li):
    if net not in ('ULPI_D4', 'ULPI_D6'):
        return False
    if kind == 'via':
        return close(data[:2], RIP_VIAS[net])
    if kind == 'seg':
        return any(close(data[:4], s[:4]) and li == s[4]
                   for s in RIP_SEGS[net])
    return False

static = {li: [it for it in items[li] if not is_ripped(it[0], it[1], it[2], li)]
          for li in range(3)}
n_rip = sum(len(items[li]) - len(static[li]) for li in range(3))
print(f'ripped entries: {n_rip} (expect F 4+7, In2 3+3, vias 2x3 = 23)')
BOX = (76.5, 86.0, 9.0, 18.0)
def in_box(it):
    k, _n, d, _c = it
    if k in ('pad', 'via'):
        return BOX[0]-1 <= d[0] <= BOX[1]+1 and BOX[2]-1 <= d[1] <= BOX[3]+1
    return (BOX[0]-1 <= min(d[0], d[2]) and max(d[0], d[2]) <= BOX[1]+1
            and BOX[2]-1 <= min(d[1], d[3]) and max(d[1], d[3]) <= BOX[3]+1)
static_box = {li: [it for it in static[li] if in_box(it)] for li in range(3)}

def pair_clr(n1, n2):
    return max(netclass(n1)[1], netclass(n2)[1] if n2 else 0.2)

def pt_margin(li, x, y, net, rad, pool):
    m = 9.9
    for it in pool:
        if it[1] == net:
            continue
        d = dist_to_item(it, x, y) - rad - pair_clr(net, it[1])
        if d < m:
            m = d
    return m

def seg_margin(li, a, b, net, hw, pool, step=0.02):
    n = max(2, int(math.hypot(b[0]-a[0], b[1]-a[1]) / step))
    m = 9.9
    for k in range(n + 1):
        mm_ = pt_margin(li, a[0]+(b[0]-a[0])*k/n, a[1]+(b[1]-a[1])*k/n,
                        net, hw, pool)
        if mm_ < m:
            m = mm_
    return m

def poly_margin(li, pts, net, hw, pool):
    return min(seg_margin(li, a, b, net, hw, pool)
               for a, b in zip(pts, pts[1:]))

PAD = {'ULPI_D4': (78.4375, 14.25), 'ULPI_D5': (78.4375, 14.75),
       'ULPI_D6': (78.4375, 15.25)}
RAD = {'ULPI_D4': 0.30, 'ULPI_D5': 0.25, 'ULPI_D6': 0.30}
TRK_HW = 0.1

def grid(x0, x1, y0, y1, step=0.125):
    xs = [x0 + i*step for i in range(int(round((x1-x0)/step)) + 1)]
    ys = [y0 + i*step for i in range(int(round((y1-y0)/step)) + 1)]
    return [(round(x, 4), round(y, 4)) for x in xs for y in ys]

CAND = {'ULPI_D4': grid(79.25, 80.5, 13.875, 15.5),
        'ULPI_D6': grid(80.0, 81.5, 14.125, 16.0),
        'ULPI_D5': grid(78.875, 81.375, 13.75, 15.875)}
feas = {}
for net, cand in CAND.items():
    feas[net] = []
    for V in cand:
        m = min(pt_margin(li, V[0], V[1], net, RAD[net], static_box[li])
                for li in range(3))
        if m >= 0.0:
            feas[net].append((m, V))
    feas[net].sort(reverse=True)
    print(f'{net}: {len(feas[net])} static-feasible vias (rip-3): '
          f'{[v for _m, v in feas[net][:14]]}')

# ---- F stub variants (same shapes as t_af4) --------------------------
PRE4 = [[(78.4375, 14.25), (78.6875, 14.25), (79.125, 14.375),
         (79.375, 14.625)],
        [(78.4375, 14.25), (78.6875, 14.25), (79.125, 14.375)]]
PRE6 = [[(78.4375, 15.25), (78.6875, 15.25), (79.125, 15.375),
         (79.375, 15.625), (79.875, 15.625), (80.125, 15.375),
         (80.375, 15.125)],
        [(78.4375, 15.25), (78.6875, 15.25), (79.125, 15.375),
         (79.375, 15.625), (79.875, 15.625)]]
E_WAY6 = [(80.95, 15.625), (81.05, 15.55), (81.125, 15.625),
          (81.0, 15.5), (80.875, 15.625), (81.25, 15.5),
          (81.125, 15.375), (81.25, 15.25),
          (80.95, 15.875), (81.125, 15.875),
          (80.125, 15.625), (80.25, 15.625), (80.375, 15.625),
          (80.5, 15.625), (80.25, 15.5), (80.375, 15.5),
          (80.5, 15.55), (80.625, 15.625)]
BEND5 = [(79.0, 14.75), (79.125, 14.875), (79.25, 15.0), (79.5, 15.25),
         (79.75, 15.375), (80.0, 15.375), None]
def stub_variants(net, V):
    if net == 'ULPI_D4':
        return [pre + [V] for pre in PRE4]
    if net == 'ULPI_D6':
        out = [pre + [V] for pre in PRE6]
        for W in E_WAY6:
            out.append(PRE6[1] + [W, V])
        return out
    out = []
    for B in BEND5:
        if B is None:
            out.append([PAD[net], V])
        else:
            out.append([PAD[net], B, V])
    out.append([PAD[net], (V[0], 14.75), V] if V[1] != 14.75
               else [PAD[net], V])
    return out

def seg_item(net, a, b, hw=TRK_HW):
    return ('seg', net, (a[0], a[1], b[0], b[1], hw), netclass(net)[1])

def poly_items(net, pts):
    return [seg_item(net, a, b) for a, b in zip(pts, pts[1:])]

def item_pair_margin(li, it_a, it_b):
    na, nb = it_a[1], it_b[1]
    if na == nb:
        return 9.9
    clr = pair_clr(na, nb)
    def sample_vs(it_src, it_dst):
        if it_src[0] == 'via':
            pts = [(it_src[2][0], it_src[2][1])]
            hw = it_src[2][2]
        else:
            x1, y1, x2, y2, hw = it_src[2]
            n = max(2, int(math.hypot(x2-x1, y2-y1) / 0.02))
            pts = [(x1+(x2-x1)*k/n, y1+(y2-y1)*k/n) for k in range(n+1)]
        return min(dist_to_item(it_dst, x, y) - hw - clr for x, y in pts)
    if it_a[0] == 'via' and it_b[0] == 'via':
        d = math.hypot(it_a[2][0]-it_b[2][0], it_a[2][1]-it_b[2][1])
        return d - it_a[2][2] - it_b[2][2] - clr
    return min(sample_vs(it_a, it_b), sample_vs(it_b, it_a))

# ---- mini-groute on In2 ----------------------------------------------
GX0, GX1, GY0, GY1, CELL = 78.75, 85.0, 10.75, 16.25, 0.125
NX = int(round((GX1-GX0)/CELL)) + 1
NY = int(round((GY1-GY0)/CELL)) + 1
def cxy(i, j):
    return (GX0 + i*CELL, GY0 + j*CELL)

def groute_in2(net, start, goal_pred, extra_items):
    """A* on In2 from `start` (a via centre, on-grid) to any cell
    satisfying goal_pred(x, y). Obstacles: static_box[1] +
    extra_items (other nets' new In2/via items). Returns a
    simplified point list or None."""
    pool = static_box[1] + list(extra_items)
    ok = {}
    def passable(i, j):
        if (i, j) not in ok:
            x, y = cxy(i, j)
            ok[(i, j)] = pt_margin(1, x, y, net, TRK_HW, pool) >= 0.004
        return ok[(i, j)]
    si = int(round((start[0]-GX0)/CELL)); sj = int(round((start[1]-GY0)/CELL))
    goals = set()
    for i in range(NX):
        for j in range(NY):
            x, y = cxy(i, j)
            if goal_pred(x, y):
                goals.add((i, j))
    if not goals:
        return None
    gx = [cxy(i, j) for (i, j) in goals]
    def heur(i, j):
        x, y = cxy(i, j)
        return 0.95 * min(math.hypot(x-a, y-b) for a, b in gx)
    open_h, came, gs = [], {}, {}
    s = (si, sj)
    gs[s] = 0.0; came[s] = None
    heapq.heappush(open_h, (heur(si, sj), 0.0, s))
    found = None
    while open_h:
        f, g, cur = heapq.heappop(open_h)
        if cur in goals:
            found = cur; break
        if g > gs.get(cur, 1e18):
            continue
        i, j = cur
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                if di == 0 and dj == 0:
                    continue
                ni, nj = i+di, j+dj
                if not (0 <= ni < NX and 0 <= nj < NY):
                    continue
                if not passable(ni, nj):
                    continue
                if di and dj and not (passable(i, nj) and passable(ni, j)):
                    continue
                nb = (ni, nj)
                ng = g + CELL * (1.41421 if di and dj else 1.0)
                if ng < gs.get(nb, 1e18):
                    gs[nb] = ng; came[nb] = cur
                    heapq.heappush(open_h, (ng + heur(ni, nj), ng, nb))
    if not found:
        return None
    path = []
    cur = found
    while cur:
        path.append(cxy(*cur)); cur = came[cur]
    path.reverse()
    path[0] = start
    # greedy shortcut verified against the same pool
    sm = [path[0]]
    i0 = 0
    while i0 < len(path) - 1:
        j0 = len(path) - 1
        while j0 > i0 + 1 and seg_margin(1, path[i0], path[j0], net,
                                         TRK_HW, pool, step=0.04) < 0:
            j0 -= 1
        sm.append(path[j0]); i0 = j0
    return sm

# ---- option build -----------------------------------------------------
opts = {}
for net in ('ULPI_D4', 'ULPI_D6', 'ULPI_D5'):
    opts[net] = []
    for vm, V in feas[net]:
        for sp in stub_variants(net, V):
            sm = poly_margin(0, sp, net, TRK_HW, static_box[0])
            if sm >= 0:
                opts[net].append((min(vm, sm), vm, V, sp))
    print(f'{net}: {len(opts[net])} via+stub options pass statics')

def vv(oa, ob, na, nb):
    Va, Vb = oa[2], ob[2]
    return math.hypot(Va[0]-Vb[0], Va[1]-Vb[1]) - (RAD[na]+RAD[nb]+0.2)

sols = []
tried = 0
for o4 in opts['ULPI_D4']:
    V4 = o4[2]
    via4 = ('via', 'ULPI_D4', (V4[0], V4[1], RAD['ULPI_D4']), 0.2)
    for o6 in opts['ULPI_D6']:
        if vv(o4, o6, 'ULPI_D4', 'ULPI_D6') < 0.005:
            continue
        V6 = o6[2]
        via6 = ('via', 'ULPI_D6', (V6[0], V6[1], RAD['ULPI_D6']), 0.2)
        # F-layer pairwise D4-D6 (stubs + vias)
        f46 = min([item_pair_margin(0, a, b)
                   for a in poly_items('ULPI_D4', o4[3]) + [via4]
                   for b in poly_items('ULPI_D6', o6[3]) + [via6]])
        if f46 < 0:
            continue
        for o5 in opts['ULPI_D5']:
            if vv(o4, o5, 'ULPI_D4', 'ULPI_D5') < 0.005:
                continue
            if vv(o6, o5, 'ULPI_D6', 'ULPI_D5') < 0.005:
                continue
            V5 = o5[2]
            via5 = ('via', 'ULPI_D5', (V5[0], V5[1], RAD['ULPI_D5']), 0.2)
            f45 = min([item_pair_margin(0, a, b)
                       for a in poly_items('ULPI_D4', o4[3]) + [via4]
                       for b in poly_items('ULPI_D5', o5[3]) + [via5]])
            f65 = min([item_pair_margin(0, a, b)
                       for a in poly_items('ULPI_D6', o6[3]) + [via6]
                       for b in poly_items('ULPI_D5', o5[3]) + [via5]])
            if f45 < 0 or f65 < 0:
                continue
            tried += 1
            # groute connectors: D4 -> A4, D6 -> A6, D5 -> exit
            c4 = groute_in2('ULPI_D4', V4,
                            lambda x, y, A=ANCH['ULPI_D4']:
                            math.hypot(x-A[0], y-A[1]) <= 0.03,
                            [via6, via5])
            if c4 is None:
                continue
            i4 = poly_items('ULPI_D4', c4)
            c6 = groute_in2('ULPI_D6', V6,
                            lambda x, y, A=ANCH['ULPI_D6']:
                            math.hypot(x-A[0], y-A[1]) <= 0.03,
                            [via4, via5] + i4)
            if c6 is None:
                continue
            i6 = poly_items('ULPI_D6', c6)
            c5 = groute_in2('ULPI_D5', V5,
                            lambda x, y: x >= 84.25 or y <= 11.25,
                            [via4, via6] + i4 + i6)
            if c5 is None:
                continue
            worst = min(o4[0], o6[0], o5[0], f46, f45, f65)
            move = (math.hypot(V4[0]-79.625, V4[1]-14.875)
                    + math.hypot(V6[0]-80.625, V6[1]-14.875))
            sols.append((worst, -move, o4, o6, o5, c4, c6, c5))
            print(f'FEASIBLE #{len(sols)}: worst {worst:+.3f} '
                  f'V4={V4} V6={V6} V5={V5}')
            if len(sols) >= 6:
                break
        if len(sols) >= 6:
            break
    if len(sols) >= 6:
        break
print(f'\n{tried} combos reached grouting; {len(sols)} feasible')
for s in sols:
    print(f'  worst {s[0]:+.3f} move {-s[1]:.2f}')
    print(f'    V4={s[2][2]} stub4={s[2][3]} conn4={s[5]}')
    print(f'    V6={s[3][2]} stub6={s[3][3]} conn6={s[6]}')
    print(f'    V5={s[4][2]} stub5={s[4][3]} conn5={s[7]}')

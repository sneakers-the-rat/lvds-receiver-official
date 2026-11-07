"""t_af4: ULPI_D5 joint re-fanout search, bent-stub edition.

t_af2/t_af3 proved: with D4/D6 stubs+first In2 segs ripped, the
statically feasible via positions are D4: 28 pts, D6: 7 pts,
D5: 5 pts (a pocket at (80.1-80.4, 15.0-15.25)) -- but STRAIGHT
pad->via stubs all fail (three straight diagonals from adjacent
rows to one pocket must cross; worst -0.396). The board's own
escapes are bent polylines that stay in their row band, so this
search parametrizes stub SHAPE:

  D4 stub: existing polyline prefix ending (79.375,14.625) or
           (79.125,14.375), then straight to V4
  D6 stub: existing polyline prefix ending (80.375,15.125) or
           (79.875,15.625), then straight to V6
  D5 stub: pad -> bend B -> V5, B in a NE-arc waypoint set
           (incl. straight, B = V5)
  D4/D6 In2 connectors: via -> kept-staircase anchor, straight
  D5: one clear 1.25 mm launch seg on In2 or B

Radii faithful to the board: D4/D6 vias d0.6, D5 via d0.5,
tracks w0.2. Exact item model + dist_to_item margins as in
t_af2. Every candidate solution is then JOINT-verified: all new
items vs all static foreign items and vs each other, densely
sampled. Objective: maximize the worst margin.

Usage: xvfb-run -a python3 scratch/work/t_af4_d5opt2.py BOARD
"""
import math, sys
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

RIP_SEGS = {
    'ULPI_D4': [(78.438, 14.25, 78.688, 14.25, 0),
                (78.688, 14.25, 79.125, 14.375, 0),
                (79.125, 14.375, 79.375, 14.625, 0),
                (79.375, 14.625, 79.625, 14.875, 0),
                (79.625, 14.875, 79.875, 14.625, 1)],
    'ULPI_D6': [(78.438, 15.25, 78.688, 15.25, 0),
                (78.688, 15.25, 79.125, 15.375, 0),
                (79.125, 15.375, 79.375, 15.625, 0),
                (79.375, 15.625, 79.875, 15.625, 0),
                (79.875, 15.625, 80.125, 15.375, 0),
                (80.125, 15.375, 80.375, 15.125, 0),
                (80.375, 15.125, 80.625, 14.875, 0),
                (80.625, 14.875, 80.875, 14.625, 1)],
}
RIP_VIAS = {'ULPI_D4': (79.625, 14.875), 'ULPI_D6': (80.625, 14.875)}

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
BOX = (76.5, 84.0, 11.0, 18.0)
def in_box(it):
    k, _n, d, _c = it
    if k in ('pad', 'via'):
        return BOX[0]-1 <= d[0] <= BOX[1]+1 and BOX[2]-1 <= d[1] <= BOX[3]+1
    return (BOX[0]-1 <= min(d[0], d[2]) and max(d[0], d[2]) <= BOX[1]+1
            and BOX[2]-1 <= min(d[1], d[3]) and max(d[1], d[3]) <= BOX[3]+1)
static_box = {li: [it for it in static[li] if in_box(it)] for li in range(3)}
print(f'static in box: {[len(static_box[li]) for li in range(3)]}')

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
ANCH = {'ULPI_D4': (79.875, 14.625), 'ULPI_D6': (80.875, 14.625)}
RAD = {'ULPI_D4': 0.30, 'ULPI_D5': 0.25, 'ULPI_D6': 0.30}
TRK_HW = 0.1

def grid(x0, x1, y0, y1, step=0.125):
    xs = [x0 + i*step for i in range(int(round((x1-x0)/step)) + 1)]
    ys = [y0 + i*step for i in range(int(round((y1-y0)/step)) + 1)]
    return [(round(x, 4), round(y, 4)) for x in xs for y in ys]

CAND = {'ULPI_D4': grid(79.25, 80.375, 14.0, 15.5),
        'ULPI_D6': grid(80.0, 81.375, 14.25, 16.0),
        'ULPI_D5': grid(78.875, 81.125, 13.875, 15.875)}
feas = {}
for net, cand in CAND.items():
    feas[net] = []
    for V in cand:
        m = min(pt_margin(li, V[0], V[1], net, RAD[net], static_box[li])
                for li in range(3))
        if m >= 0.0:
            feas[net].append((m, V))
    feas[net].sort(reverse=True)
    print(f'{net}: {len(feas[net])} static-feasible vias')

# ---- stub shape variants (point lists, F layer) ----------------------
PRE4 = [[(78.4375, 14.25), (78.6875, 14.25), (79.125, 14.375),
         (79.375, 14.625)],
        [(78.4375, 14.25), (78.6875, 14.25), (79.125, 14.375)]]
PRE6 = [[(78.4375, 15.25), (78.6875, 15.25), (79.125, 15.375),
         (79.375, 15.625), (79.875, 15.625), (80.125, 15.375),
         (80.375, 15.125)],
        [(78.4375, 15.25), (78.6875, 15.25), (79.125, 15.375),
         (79.375, 15.625), (79.875, 15.625)]]
BEND5 = [(79.0, 14.75), (79.125, 14.875), (79.25, 15.0), (79.5, 15.25),
         (79.75, 15.375), (80.0, 15.375), None]  # None = straight

E_WAY6 = [(80.95, 15.625), (81.05, 15.55), (81.125, 15.625),
          (81.0, 15.5), (80.875, 15.625), (81.25, 15.5),
          (81.125, 15.375), (81.25, 15.25)]
def stub_variants(net, V):
    if net == 'ULPI_D4':
        return [pre + [V] for pre in PRE4]
    if net == 'ULPI_D6':
        out = [pre + [V] for pre in PRE6]
        # eastern approach: stay on the y15.625 row past the pocket,
        # then drop to the via from the NE (aimed at the af5 bind:
        # D6's NW tail seg vs D5's via, -0.462)
        for W in E_WAY6:
            out.append(PRE6[1] + [W, V])
        return out
    out = []
    for B in BEND5:
        if B is None:
            out.append([PAD[net], V])
        elif B == (79.0, 14.75):
            out.append([PAD[net], (V[0], 14.75), V] if V[1] != 14.75
                       else [PAD[net], V])
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
    """Margin between two NEW items of (possibly) different nets."""
    na, nb = it_a[1], it_b[1]
    if na == nb:
        return 9.9
    clr = pair_clr(na, nb)
    def sample_vs(it_src, it_dst):
        # sample points on src (seg) or centre (via); margin to dst
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

LAUNCH_DIRS = [(1, 0), (1, -0.5), (1, -1), (0.5, -1), (0, -1),
               (1, 0.5), (1, 1), (0.5, 1)]
def launch_best(V, extra_by_layer):
    best = (-9.9, None)
    for li in (1, 2):
        pool = static_box[li] + extra_by_layer.get(li, [])
        for dx, dy in LAUNCH_DIRS:
            L = 1.25 / math.hypot(dx, dy)
            b = (V[0] + dx*L, V[1] + dy*L)
            m = seg_margin(li, V, b, 'ULPI_D5', TRK_HW, pool)
            if m > best[0]:
                best = (m, (li, b))
    return best

# Precompute per-net options: (via_margin, V, stub_pts, stub_static_m,
#                              conn_static_m or None)
opts = {}
for net in ('ULPI_D4', 'ULPI_D6'):
    opts[net] = []
    for vm, V in feas[net]:
        cm = seg_margin(1, V, ANCH[net], net, TRK_HW, static_box[1])
        for sp in stub_variants(net, V):
            sm = poly_margin(0, sp, net, TRK_HW, static_box[0])
            if sm >= 0 and cm >= 0:
                opts[net].append((min(vm, sm, cm), vm, V, sp, cm))
    print(f'{net}: {len(opts[net])} options pass statics')
opts['ULPI_D5'] = []
for vm, V in feas['ULPI_D5']:
    for sp in stub_variants('ULPI_D5', V):
        sm = poly_margin(0, sp, 'ULPI_D5', TRK_HW, static_box[0])
        if sm >= 0:
            opts['ULPI_D5'].append((min(vm, sm), vm, V, sp, None))
print(f"ULPI_D5: {len(opts['ULPI_D5'])} options pass statics")

def layered(stub_pts, net, V, conn_to):
    """New items for one net, split by layer: (F items, In2 items).
    Vias are through -- they appear on every layer at verify time."""
    f_items = poly_items(net, stub_pts) + \
        [('via', net, (V[0], V[1], RAD[net]), 0.2)]
    i_items = []
    if conn_to is not None:
        i_items = [seg_item(net, V, conn_to)]
    return f_items, i_items

sols = []
for w4, vm4, V4, sp4, cm4 in opts['ULPI_D4']:
    f4, i4 = layered(sp4, 'ULPI_D4', V4, ANCH['ULPI_D4'])
    for w6, vm6, V6, sp6, cm6 in opts['ULPI_D6']:
        dvv = math.hypot(V4[0]-V6[0], V4[1]-V6[1]) - (RAD['ULPI_D4']+RAD['ULPI_D6']+0.2)
        if dvv < 0:
            continue
        f6, i6 = layered(sp6, 'ULPI_D6', V6, ANCH['ULPI_D6'])
        for w5, vm5, V5, sp5, _ in opts['ULPI_D5']:
            if math.hypot(V5[0]-V4[0], V5[1]-V4[1]) < RAD['ULPI_D5']+RAD['ULPI_D4']+0.2:
                continue
            if math.hypot(V5[0]-V6[0], V5[1]-V6[1]) < RAD['ULPI_D5']+RAD['ULPI_D6']+0.2:
                continue
            f5, i5 = layered(sp5, 'ULPI_D5', V5, None)
            via4 = ('via', 'ULPI_D4', (V4[0], V4[1], RAD['ULPI_D4']), 0.2)
            via6 = ('via', 'ULPI_D6', (V6[0], V6[1], RAD['ULPI_D6']), 0.2)
            via5 = ('via', 'ULPI_D5', (V5[0], V5[1], RAD['ULPI_D5']), 0.2)
            new_by_layer = {
                0: f4 + f6 + f5,
                1: [via4, via6, via5] + i4 + i6,
                2: [via4, via6, via5],
            }
            worst = min(w4, w6, w5)
            ok = True
            for li in range(3):
                pool = new_by_layer[li]
                for i in range(len(pool)):
                    for j in range(i+1, len(pool)):
                        m = item_pair_margin(li, pool[i], pool[j])
                        if m < worst:
                            worst = m
                        if worst < 0:
                            ok = False
                            break
                    if not ok:
                        break
                if not ok:
                    break
            if not ok:
                continue
            lm, ldir = launch_best(V5, {1: i4 + i6})
            if lm < 0:
                continue
            worst = min(worst, lm)
            move = (math.hypot(V4[0]-79.625, V4[1]-14.875)
                    + math.hypot(V6[0]-80.625, V6[1]-14.875))
            sols.append((worst, -move, V4, sp4, V6, sp6, V5, sp5, ldir))
            if len(sols) >= 3000:
                break
        if len(sols) >= 3000:
            break
    if len(sols) >= 3000:
        break

sols.sort(key=lambda s: (s[0], s[1]), reverse=True)
print(f'\n{len(sols)} JOINT-VERIFIED feasible solutions')
for s in sols[:8]:
    print(f'  worst {s[0]:+.3f} move {-s[1]:.2f}')
    print(f'    V4={s[2]} stub4={s[3]}')
    print(f'    V6={s[4]} stub6={s[5]}')
    print(f'    V5={s[6]} stub5={s[7]} launch={s[8]}')

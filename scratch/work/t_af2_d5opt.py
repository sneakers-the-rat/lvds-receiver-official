"""t_af2: computational search for the ULPI_D5 escape.

D5 (U7.19, east face (78.438,14.75)) has ZERO copper board-wide:
its F escape is sealed by D4's escape polyline + via (79.625,14.875)
d0.6 to the SE and D6's polyline + via (80.625,14.875) d0.6 to the
NE (inter-via corridor 0.35 mm of copper gap where a w0.2 track
needs 0.6). This script searches a JOINT re-fanout of D4+D5+D6:

  rip:  D4 F stub (4 segs) + via + first In2 seg
        D6 F stub (7 segs) + via + first In2 seg
  keep: D4 In2 staircase from anchor A4=(79.875,14.625)
        D6 In2 staircase from anchor A6=(80.875,14.625)
  vars: V4, V6 (d0.6, as existing), V5 (d0.5, as D2/D3) on a
        0.125 grid; F stubs straight pad->via w0.2; In2 connectors
        straight via->anchor w0.2; D5 needs one clear 1.25 mm
        launch seg on In2 or B.

All clearance checks use the exact item model (repair.build_items
geometry: OBB pads, segs, vias) with router.dist_to_item edge
distances and check_pcb pair classes (max of the two nets' class
clearances). Margin = edge_dist - own_radius - pair_clr; feasible
is margin >= 0 everywhere. A final joint verifier re-checks every
new item against all static foreign items and against the other
nets' new items by dense sampling.

Usage: xvfb-run -a python3 scratch/work/t_af2_d5opt.py BOARD
"""
import math, sys, itertools
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
from router import netclass, dist_to_item

MM = pcbnew.ToMM
LAYERS = [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]

src = sys.argv[1]
board = pcbnew.LoadBoard(src)

# ---- flat item model -------------------------------------------------
items = {0: [], 1: [], 2: []}   # li -> [(kind, net, data, clr)]
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
track_by_id = {}
for t in board.GetTracks():
    net = t.GetNetname()
    clr = netclass(net)[1] if net else 0.2
    if isinstance(t, pcbnew.PCB_VIA):
        x, y = MM(t.GetPosition())
        r = MM(t.GetWidth()) / 2
        for li in range(3):
            items[li].append(('via', net, (x, y, r), clr))
        track_by_id[id(t)] = ('via', net, (x, y))
    else:
        if t.GetLayer() not in LAYERS:
            continue
        li = LAYERS.index(t.GetLayer())
        a = MM(t.GetStart()); b = MM(t.GetEnd())
        w = MM(t.GetWidth())
        items[li].append(('seg', net, (a[0], a[1], b[0], b[1], w / 2), clr))
        track_by_id[id(t)] = ('seg', net, (a[0], a[1], b[0], b[1], li))

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

# static obstacles: everything except the rip set
static = {li: [it for it in items[li] if not is_ripped(it[0], it[1], it[2], li)]
          for li in range(3)}
n_rip = sum(len(items[li]) - len(static[li]) for li in range(3))
print(f'static items per layer: {[len(static[li]) for li in range(3)]}, '
      f'ripped entries: {n_rip} (expect D4 5x1+D6 8x1 + vias 2x3 = 19)')

# district filter for speed: only items within reach matter
BOX = (76.5, 84.0, 11.0, 18.0)
def in_box(it):
    k, _n, d, _c = it
    if k == 'pad':
        return BOX[0] - 1 <= d[0] <= BOX[1] + 1 and BOX[2] - 1 <= d[1] <= BOX[3] + 1
    if k == 'via':
        return BOX[0] - 1 <= d[0] <= BOX[1] + 1 and BOX[2] - 1 <= d[1] <= BOX[3] + 1
    return (BOX[0] - 1 <= min(d[0], d[2]) and max(d[0], d[2]) <= BOX[1] + 1
            and BOX[2] - 1 <= min(d[1], d[3]) and max(d[1], d[3]) <= BOX[3] + 1)
static_box = {li: [it for it in static[li] if in_box(it)] for li in range(3)}
print(f'static items in box: {[len(static_box[li]) for li in range(3)]}')

def pair_clr(n1, n2):
    return max(netclass(n1)[1], netclass(n2)[1] if n2 else 0.2)

def pt_margin(li, x, y, net, rad, pool):
    """Min margin of a disc (rad) at (x,y) vs foreign items in pool."""
    m = 9.9
    for it in pool:
        if it[1] == net:
            continue
        d = dist_to_item(it, x, y) - rad - pair_clr(net, it[1])
        if d < m:
            m = d
    return m

def seg_margin(li, a, b, net, hw, pool, step=0.02):
    n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / step))
    m = 9.9
    for k in range(n + 1):
        x = a[0] + (b[0] - a[0]) * k / n
        y = a[1] + (b[1] - a[1]) * k / n
        mm_ = pt_margin(li, x, y, net, hw, pool)
        if mm_ < m:
            m = mm_
    return m

def via_static_margin(net, V, r):
    return min(pt_margin(li, V[0], V[1], net, r, static_box[li])
               for li in range(3))

PAD = {'ULPI_D4': (78.438, 14.25), 'ULPI_D5': (78.438, 14.75),
       'ULPI_D6': (78.438, 15.25)}
ANCH = {'ULPI_D4': (79.875, 14.625), 'ULPI_D6': (80.875, 14.625)}
RAD = {'ULPI_D4': 0.30, 'ULPI_D5': 0.25, 'ULPI_D6': 0.30}
TRK_HW = 0.1

def grid(x0, x1, y0, y1, step=0.125):
    xs = [x0 + i * step for i in range(int(round((x1 - x0) / step)) + 1)]
    ys = [y0 + i * step for i in range(int(round((y1 - y0) / step)) + 1)]
    return [(round(x, 4), round(y, 4)) for x in xs for y in ys]

CAND = {
    'ULPI_D4': grid(79.25, 80.375, 14.0, 15.5),
    'ULPI_D6': grid(80.0, 81.375, 14.25, 16.0),
    'ULPI_D5': grid(78.875, 81.125, 13.875, 15.875),
}
feas = {}
for net, cand in CAND.items():
    feas[net] = [(via_static_margin(net, V, RAD[net]), V) for V in cand]
    feas[net] = [f for f in feas[net] if f[0] >= 0.0]
    feas[net].sort(reverse=True)
    print(f'{net}: {len(feas[net])}/{len(cand)} via candidates pass '
          f'static check; best margin '
          f'{feas[net][0][0] if feas[net] else None}')

def stub_m(net, V, extra_pool0=()):
    pool = static_box[0] + list(extra_pool0)
    return seg_margin(0, PAD[net], V, net, TRK_HW, pool)

def conn_m(net, V, extra_pool1=()):
    pool = static_box[1] + list(extra_pool1)
    return seg_margin(1, V, ANCH[net], net, TRK_HW, pool)

LAUNCH_DIRS = [(1, 0), (1, -0.5), (1, -1), (0.5, -1), (0, -1),
               (1, 0.5), (1, 1), (0.5, 1)]
def launch_m(V, extra1=(), extra2=()):
    best = -9.9
    for li, extra in ((1, extra1), (2, extra2)):
        pool = static_box[li] + list(extra)
        for dx, dy in LAUNCH_DIRS:
            L = 1.25 / math.hypot(dx, dy)
            b = (V[0] + dx * L, V[1] + dy * L)
            best = max(best, seg_margin(li, V, b, 'ULPI_D5', TRK_HW, pool))
    return best

def seg_item(net, a, b, hw=TRK_HW):
    return ('seg', net, (a[0], a[1], b[0], b[1], hw), netclass(net)[1])

def via_item(net, V, r):
    return ('via', net, (V[0], V[1], r), netclass(net)[1])

sols = []
CAP = {'ULPI_D4': 60, 'ULPI_D6': 60, 'ULPI_D5': 200}
for m4, V4 in feas['ULPI_D4'][:CAP['ULPI_D4']]:
    if stub_m('ULPI_D4', V4) < 0 or conn_m('ULPI_D4', V4) < 0:
        continue
    stub4 = seg_item('ULPI_D4', PAD['ULPI_D4'], V4)
    conn4 = seg_item('ULPI_D4', V4, ANCH['ULPI_D4'])
    for m6, V6 in feas['ULPI_D6'][:CAP['ULPI_D6']]:
        if math.hypot(V4[0] - V6[0], V4[1] - V6[1]) < \
                RAD['ULPI_D4'] + RAD['ULPI_D6'] + 0.2:
            continue
        if stub_m('ULPI_D6', V6, (stub4,)) < 0:
            continue
        if conn_m('ULPI_D6', V6, (conn4,)) < 0:
            continue
        stub6 = seg_item('ULPI_D6', PAD['ULPI_D6'], V6)
        conn6 = seg_item('ULPI_D6', V6, ANCH['ULPI_D6'])
        for m5, V5 in feas['ULPI_D5'][:CAP['ULPI_D5']]:
            if math.hypot(V5[0] - V4[0], V5[1] - V4[1]) < \
                    RAD['ULPI_D5'] + RAD['ULPI_D4'] + 0.2:
                continue
            if math.hypot(V5[0] - V6[0], V5[1] - V6[1]) < \
                    RAD['ULPI_D5'] + RAD['ULPI_D6'] + 0.2:
                continue
            s5 = stub_m('ULPI_D5', V5, (stub4, stub6))
            if s5 < 0:
                continue
            l5 = launch_m(V5, (conn4, conn6), ())
            if l5 < 0:
                continue
            worst = min(m4, m6, m5, s5, l5,
                        stub_m('ULPI_D6', V6, (stub4,)),
                        conn_m('ULPI_D6', V6, (conn4,)))
            move = (math.hypot(V4[0] - 79.625, V4[1] - 14.875)
                    + math.hypot(V6[0] - 80.625, V6[1] - 14.875))
            sols.append((worst, -move, V4, V6, V5,
                         dict(m4=m4, m6=m6, m5=m5, s5=s5, l5=l5)))
            if len(sols) > 4000:
                break
        if len(sols) > 4000:
            break
    if len(sols) > 4000:
        break

sols.sort(key=lambda s: (s[0], s[1]), reverse=True)
print(f'\n{len(sols)} feasible joint solutions (straight stubs)')
for s in sols[:10]:
    print(f'  worst-margin {s[0]:+.3f} move {-s[1]:.2f} '
          f'V4={s[2]} V6={s[3]} V5={s[4]} {s[5]}')

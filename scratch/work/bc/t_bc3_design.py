"""t_bc3 v2: design + exact-gate the user's XI build on exp256.

v1 timed out (full layer pool scanned at every sample point); v2 gates
through the Items spatial index (near()) with early abort at the
incumbent score. Same design:

- ULPI_DIR via (75.5,17.521) nudged WEST along y=17.521 (scan picks the
  landing the gates require); DIR F stub (75.750,16.875)->via and B seg
  via->(71.375,19.125) re-laid compactly.
- XI ride on B, w0.2: arc via (75.625,18.625) -> exit point -> waist
  between DIR/dive vias -> northbound -> NW bend -> west lane past the
  GND stitch via (75.6,14.75) -> NE jog -> PV (75.82,10.30).
All gates exact: dense-sampled dist_to_item edge distances minus
(hw + pair class clearance), the check_pcb class table. Old DIR
via/stub/B-seg are excluded from obstacle pools (they are ripped);
new DIR copper and the new ride gate against each other.
"""
import json, math, sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import repair
from router import netclass, dist_to_item

SRC = 'hw/pdlvds_rx.exp256.kicad_pcb'
board = pcbnew.LoadBoard(SRC)
items, _pc = repair.build_items(board)
LAYN = ['F', 'In2', 'B']

def pair_clr(n, o):
    return max(netclass(n)[1], netclass(o)[1] if o else 0.2)

def is_dir_victim(it):
    if it[1] != 'ULPI_DIR':
        return False
    if it[0] == 'via':
        return abs(it[2][0] - 75.5) < 0.01 and abs(it[2][1] - 17.521) < 0.01
    if it[0] == 'seg':
        x1, y1, x2, y2, _hw = it[2]
        pts = {(round(x1, 2), round(y1, 2)), (round(x2, 2), round(y2, 2))}
        return (75.5, 17.52) in pts
    return False

def seg_gate(li, a, b, net, hw, extra=(), step=0.03, floor=-9e9):
    worst, arg = 9e9, None
    n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / step))
    for k in range(n + 1):
        x = a[0] + (b[0] - a[0]) * k / n
        y = a[1] + (b[1] - a[1]) * k / n
        seen = set()
        for it in items[li].near(li, x, y):
            if it[1] == net or id(it) in seen or is_dir_victim(it):
                continue
            seen.add(id(it))
            d = dist_to_item(it, x, y) - hw - pair_clr(net, it[1])
            if d < worst:
                worst, arg = d, (it[1], it[0], round(x, 3), round(y, 3))
                if worst <= floor:
                    return worst, arg
        for it in extra:
            if it[1] == net:
                continue
            d = dist_to_item(it, x, y) - hw - pair_clr(net, it[1])
            if d < worst:
                worst, arg = d, (it[1], it[0], round(x, 3), round(y, 3))
                if worst <= floor:
                    return worst, arg
    return worst, arg

def via_gate(x, y, net, r=0.25, extra_by_layer=None, floor=-9e9):
    worst, arg = 9e9, None
    for li in range(3):
        extra = (extra_by_layer or {}).get(li, ())
        seen = set()
        for it in items[li].near(li, x, y):
            if it[1] == net or id(it) in seen or is_dir_victim(it):
                continue
            seen.add(id(it))
            d = dist_to_item(it, x, y) - r - pair_clr(net, it[1])
            if d < worst:
                worst, arg = d, (LAYN[li], it[1], it[0])
                if worst <= floor:
                    return worst, arg
        for it in extra:
            if it[1] == net:
                continue
            d = dist_to_item(it, x, y) - r - pair_clr(net, it[1])
            if d < worst:
                worst, arg = d, (LAYN[li], it[1], it[0])
                if worst <= floor:
                    return worst, arg
    return worst, arg

DIR_STUB_A = (75.750, 16.875)
DIR_B_B = (71.375, 19.125)
ARC = (75.625, 18.625)
PV = (75.82, 10.30)
DIVE = (76.065, 17.96)

def dir_items(vx, vy):
    via = ('via', 'ULPI_DIR', (vx, vy, 0.25), 0.2)
    bseg = ('seg', 'ULPI_DIR', (vx, vy, DIR_B_B[0], DIR_B_B[1], 0.1), 0.2)
    return via, bseg

def gate_dir(vx, vy, ride_segs=(), floor=-9e9):
    via, bseg = dir_items(vx, vy)
    ride_b = [('seg', 'XI', (a[0], a[1], b[0], b[1], 0.1), 0.2) for a, b in ride_segs]
    w1, a1 = via_gate(vx, vy, 'ULPI_DIR', extra_by_layer={2: ride_b}, floor=floor)
    if w1 <= floor:
        return w1, (('via', w1, a1),)
    w2, a2 = seg_gate(0, DIR_STUB_A, (vx, vy), 'ULPI_DIR', 0.1, floor=floor)
    if w2 <= floor:
        return w2, (('fstub', w2, a2),)
    w3, a3 = seg_gate(2, (vx, vy), DIR_B_B, 'ULPI_DIR', 0.1, extra=ride_b, floor=floor)
    return min(w1, w2, w3), (('via', w1, a1), ('fstub', w2, a2), ('bseg', w3, a3))

def ride_points(vx, wx, p1, lane_x):
    wy = (17.521 + DIVE[1]) / 2
    return [ARC, p1, (wx, wy), (wx, 16.55), (lane_x, 15.10),
            (lane_x, 13.60), (75.35, 12.90), PV]

def gate_ride(pts, vx, vy, floor=-9e9):
    via, bseg = dir_items(vx, vy)
    extra = [bseg, via]
    worst, arg = 9e9, None
    segs = list(zip(pts, pts[1:]))
    for si, (a, b) in enumerate(segs):
        w, ag = seg_gate(2, a, b, 'XI', 0.1, extra=extra, floor=max(floor, -9e9))
        if w < worst:
            worst, arg = w, (f'seg{si}', ag)
            if worst <= floor:
                return worst, arg, segs
    return worst, arg, segs

# ---- stage 1: DIR via landings, legs only ----------------------------------
cands = []
vx = 74.80
while vx <= 75.201:
    w, det = gate_dir(vx, 17.521)
    cands.append((w, vx, det))
    vx += 0.025
cands.sort(key=lambda t: -t[0])
print('top DIR landings by own-gate margin:')
for w, vx, det in cands[:6]:
    print(f'  via x={vx:.3f} margin {w:+.3f}  detail={det}')
sys.stdout.flush()

# ---- stage 2: joint scan ----------------------------------------------------
best = None
for _w0, vx, _det in cands[:4]:
    for wx in [75.44 + 0.01 * k for k in range(14)]:
        for p1 in [(75.26, 18.12), (75.30, 18.15), (75.34, 18.18), (75.30, 18.08)]:
            for lane_x in (74.90, 74.92, 74.94):
                floor = best[0] if best else 0.0
                pts = ride_points(vx, wx, p1, lane_x)
                w_ride, arg, segs = gate_ride(pts, vx, 17.521, floor=floor)
                if w_ride <= floor:
                    continue
                w_dir, det = gate_dir(vx, 17.521, ride_segs=segs, floor=floor)
                score = min(w_ride, w_dir)
                if score > floor:
                    best = (score, vx, wx, p1, lane_x, w_ride, arg, w_dir, det, pts)
                    print(f'  new best {score:+.3f} via_x={vx:.3f} wx={wx:.2f} '
                          f'p1={p1} lane={lane_x}')
                    sys.stdout.flush()
if best is None:
    print('NO joint configuration gates positive')
    sys.exit(1)
score, vx, wx, p1, lane_x, w_ride, arg, w_dir, det, pts = best

# ---- final: re-gate winner at fine sampling ---------------------------------
w_ride_f, arg_f, segs = gate_ride(pts, vx, 17.521)
w_dir_f, det_f = gate_dir(vx, 17.521, ride_segs=segs)
print(f'\nWINNER: DIR via -> ({vx:.3f},17.521)  scan joint margin {score:+.3f}')
print(f'  fine re-gate: ride {w_ride_f:+.3f} binding {arg_f}')
print(f'  fine re-gate: DIR  {w_dir_f:+.3f} detail {det_f}')
print('  ride waypoints:', [(round(x, 3), round(y, 3)) for x, y in pts])
json.dump({'dir_via': [vx, 17.521], 'ride': pts,
           'ride_margin': w_ride_f, 'dir_margin': w_dir_f},
          open('scratch/work/bc/design_bc.json', 'w'), indent=1)
print('saved scratch/work/bc/design_bc.json')

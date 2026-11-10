"""t_bd9: family C v2 joint scan on exp256, shaped by t_bd7's probe.

Fixes vs t_bd4, each from measured arithmetic:
- NXT In2 leg bends west at (74.42,17.75) (was straight through the
  DIR via disc, -0.469).
- DIR stub is a 3-leg thread: head (75.75,16.875) -> (b1x,~17.32)
  -> (b2x,17.85) -> DV, passing east then south of the NXT via disc,
  west of the STP F column (x76.05, y17.3-17.96).
- DIR B seg bends north at ~(73.9,18.75) around the CAP_DATA via
  graze (-0.001) and the DM via (73.625,19.125).
- XI ride: east lane x 75.66-75.74 (NXT via pass +0.55), west lane
  x 74.95/74.98 (GND stitch via graze -0.020 at x75.02).
Stage 1 keeps the TOP 3 configs; the ride is tried on each.
Gates: bc's exact model, floor-pruned per stage."""
import json, math, sys, time
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import repair
from router import netclass, dist_to_item

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp256.kicad_pcb')
items, _pc = repair.build_items(board)
LAYN = ['F', 'In2', 'B']

def pair_clr(n, o):
    return max(netclass(n)[1], netclass(o)[1] if o else 0.2)

def seg_touch(it, px, py):
    if it[0] != 'seg':
        return False
    x1, y1, x2, y2, _h = it[2]
    return (abs(x1 - px) < 0.01 and abs(y1 - py) < 0.01) or \
           (abs(x2 - px) < 0.01 and abs(y2 - py) < 0.01)

def is_victim(it):
    net = it[1]
    if net == 'ULPI_DIR':
        if it[0] == 'via':
            return abs(it[2][0] - 75.5) < 0.01 and abs(it[2][1] - 17.521) < 0.01
        return seg_touch(it, 75.5, 17.521)
    if net == 'ULPI_NXT':
        return seg_touch(it, 74.65, 17.8) or seg_touch(it, 75.25, 16.875)
    return False

def seg_gate(li, a, b, net, hw, extra=(), step=0.03, floor=-9e9):
    worst, arg = 9e9, None
    n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / step))
    for k in range(n + 1):
        x = a[0] + (b[0] - a[0]) * k / n
        y = a[1] + (b[1] - a[1]) * k / n
        seen = set()
        for it in items[li].near(li, x, y):
            if it[1] == net or id(it) in seen or is_victim(it):
                continue
            seen.add(id(it))
            d = dist_to_item(it, x, y) - hw - pair_clr(net, it[1])
            if d < worst:
                worst, arg = d, (LAYN[li], it[1], it[0], round(x, 3), round(y, 3))
                if worst <= floor:
                    return worst, arg
        for it in extra:
            if it[1] == net:
                continue
            d = dist_to_item(it, x, y) - hw - pair_clr(net, it[1])
            if d < worst:
                worst, arg = d, (LAYN[li], it[1], it[0], round(x, 3), round(y, 3))
                if worst <= floor:
                    return worst, arg
    return worst, arg

def via_gate(x, y, net, r=0.25, extra_by_layer=None, floor=-9e9):
    worst, arg = 9e9, None
    for li in range(3):
        extra = (extra_by_layer or {}).get(li, ())
        seen = set()
        for it in items[li].near(li, x, y):
            if it[1] == net or id(it) in seen or is_victim(it):
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

DIR_HEAD = (75.75, 16.875)
DIR_B_END = (71.375, 19.125)
NXT_HEAD = (75.25, 16.875)
NXT_VIA_OLD = (74.5, 19.25)
ARC = (75.625, 18.625)
PV = (75.82, 10.30)
DIVE = (76.065, 17.96)

def gate_stage1(nv, dv, b1, b2, in2bend, bbend, floor):
    nv_it = ('via', 'ULPI_NXT', (nv[0], nv[1], 0.25), 0.2)
    dv_it = ('via', 'ULPI_DIR', (dv[0], dv[1], 0.25), 0.2)
    nxt_stub = ('seg', 'ULPI_NXT', (NXT_HEAD[0], NXT_HEAD[1], nv[0], nv[1], 0.1), 0.2)
    det = {}
    w, a = via_gate(nv[0], nv[1], 'ULPI_NXT',
                    extra_by_layer={0: [dv_it], 1: [dv_it], 2: [dv_it]}, floor=floor)
    if w <= floor: return w, None
    det['nxt_via'] = (w, a)
    w, a = seg_gate(0, NXT_HEAD, nv, 'ULPI_NXT', 0.1, extra=[dv_it], floor=floor)
    if w <= floor: return w, None
    det['nxt_stub'] = (w, a)
    for p, q in ((nv, in2bend), (in2bend, NXT_VIA_OLD)):
        w, a = seg_gate(1, p, q, 'ULPI_NXT', 0.1, extra=[dv_it], floor=floor)
        if w <= floor: return w, None
        det['nxt_in2'] = min(det.get('nxt_in2', (9e9, None)), (w, a))
    w, a = via_gate(dv[0], dv[1], 'ULPI_DIR',
                    extra_by_layer={0: [nv_it, nxt_stub], 1: [nv_it], 2: [nv_it]},
                    floor=floor)
    if w <= floor: return w, None
    det['dir_via'] = (w, a)
    stub_pts = [DIR_HEAD, b1, b2, dv]
    w_all, a_all = 9e9, None
    for p, q in zip(stub_pts, stub_pts[1:]):
        w, a = seg_gate(0, p, q, 'ULPI_DIR', 0.1, extra=[nv_it, nxt_stub], floor=floor)
        if w <= floor: return w, None
        if w < w_all: w_all, a_all = w, a
    det['dir_stub'] = (w_all, a_all)
    b_pts = [dv] + ([bbend] if bbend else []) + [DIR_B_END]
    w_all, a_all = 9e9, None
    for p, q in zip(b_pts, b_pts[1:]):
        w, a = seg_gate(2, p, q, 'ULPI_DIR', 0.1, extra=[nv_it], floor=floor)
        if w <= floor: return w, None
        if w < w_all: w_all, a_all = w, a
    det['dir_bseg'] = (w_all, a_all)
    return min(v[0] for v in det.values()), det

t0 = time.time()
tops = []
n = 0
for nvx in (75.00, 75.04, 75.08):
    for nvy in (17.30, 17.34, 17.38):
        for dvx in (74.72, 74.76, 74.80):
            for dvy in (17.96, 18.04, 18.12):
                for b1x in (75.60, 75.65, 75.70):
                    for b2x in (75.40, 75.45, 75.50):
                        for ib in ((74.42, 17.75), (74.48, 17.85)):
                            for bb in ((73.9, 18.75), (73.8, 18.65), None):
                                n += 1
                                cfg = ((nvx, nvy), (dvx, dvy), (b1x, 17.32),
                                       (b2x, 17.85), ib, bb)
                                floor = tops[2][0] if len(tops) >= 3 else 0.0
                                w, det = gate_stage1(*cfg, floor)
                                if det is not None and w > floor:
                                    tops.append((w, cfg, det))
                                    tops.sort(key=lambda t: -t[0])
                                    tops = tops[:3]
                                    print(f'  top {w:+.3f} NV={cfg[0]} DV={cfg[1]} '
                                          f'b1={cfg[2]} b2={cfg[3]} in2={ib} bb={bb} '
                                          f'[{time.time()-t0:.0f}s]', flush=True)
print(f'\nstage 1 done: {n} configs, {time.time()-t0:.0f}s, {len(tops)} positive tops')
for w, cfg, det in tops:
    print(f'  S1 {w:+.3f} NV={cfg[0]} DV={cfg[1]} b1={cfg[2]} b2={cfg[3]} in2={cfg[4]} bb={cfg[5]}')
    for k, v in det.items():
        print(f'      {k}: {v[0]:+.3f} binding {v[1]}')
if not tops:
    print('NO stage-1 configuration gates positive in family C v2')
    sys.exit(1)

# ---- stage 2: ride on each top ----------------------------------------------
winner = None
for s1w, cfg, det in tops:
    nv, dv = cfg[0], cfg[1]
    nv_it = ('via', 'ULPI_NXT', (nv[0], nv[1], 0.25), 0.2)
    dv_it = ('via', 'ULPI_DIR', (dv[0], dv[1], 0.25), 0.2)
    b_pts = [dv] + ([cfg[5]] if cfg[5] else []) + [DIR_B_END]
    dv_bsegs = [('seg', 'ULPI_DIR', (p[0], p[1], q[0], q[1], 0.1), 0.2)
                for p, q in zip(b_pts, b_pts[1:])]
    ride_extra = [nv_it, dv_it] + dv_bsegs
    mid = ((dv[0] + DIVE[0]) / 2, (dv[1] + DIVE[1]) / 2)
    dvec = (DIVE[0] - dv[0], DIVE[1] - dv[1])
    dl = math.hypot(*dvec)
    perp = (-dvec[1] / dl, dvec[0] / dl)
    dirh = (dvec[0] / dl, dvec[1] / dl)
    best2 = (min(0.0, s1w), None)
    for ex, ey in ((75.45, 18.25), (75.38, 18.10), (75.52, 18.32)):
        for s in (-0.15, 0.0, 0.15):
            for t in (-0.06, -0.03, 0.0, 0.03, 0.06):
                wp = (mid[0] + s * dirh[0] + t * perp[0],
                      mid[1] + s * dirh[1] + t * perp[1])
                for lx in (75.66, 75.70, 75.74):
                    for wx2 in (74.95, 74.98):
                        pts = [ARC, (ex, ey), wp, (lx, 16.90), (lx, 16.30),
                               (wx2, 15.95), (wx2, 13.40), (75.32, 12.75), PV]
                        w_all, arg_all = 9e9, None
                        for p, q in zip(pts, pts[1:]):
                            w, a = seg_gate(2, p, q, 'XI', 0.1,
                                            extra=ride_extra, floor=best2[0])
                            if w < w_all:
                                w_all, arg_all = w, a
                            if w_all <= best2[0]:
                                break
                        joint = min(w_all, s1w)
                        if joint > best2[0]:
                            best2 = (joint, (pts, w_all, arg_all))
    if best2[1] is not None:
        joint, (pts, w_ride, arg_ride) = best2
        print(f'\nRIDE on S1 {s1w:+.3f} (DV={dv}): joint {joint:+.3f} '
              f'ride {w_ride:+.3f} binding {arg_ride}')
        print('  ride:', [(round(x, 3), round(y, 3)) for x, y in pts])
        if winner is None or joint > winner[0]:
            winner = (joint, cfg, det, pts, w_ride, arg_ride)
if winner is None:
    print('NO ride gates positive over any stage-1 top')
    sys.exit(2)
joint, cfg, det, pts, w_ride, arg_ride = winner
print(f'\nJOINT WINNER family C v2: overall {joint:+.3f}')
print(f'  NV={cfg[0]} DV={cfg[1]} stub bends {cfg[2]} {cfg[3]} in2 bend {cfg[4]} bseg bend {cfg[5]}')
print('  ride:', [(round(x, 3), round(y, 3)) for x, y in pts])
json.dump({'family': 'C2', 'nxt_via': cfg[0], 'dir_via': cfg[1],
           'stub_b1': cfg[2], 'stub_b2': cfg[3], 'in2_bend': cfg[4],
           'bseg_bend': cfg[5], 'ride': pts, 'joint_margin': joint,
           'ride_margin': w_ride},
          open('scratch/work/bd/design_bd_c2.json', 'w'), indent=1)
print('saved scratch/work/bd/design_bd_c2.json')

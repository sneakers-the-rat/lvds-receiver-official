"""t_bd11: family C v3 on exp256 -- DV moves south-east, DIR's B
journey threads the DM/CAP_DATA via gap on its exact bisector.

Changes vs C v2 (each from t_bd7/t_bd10 measured bindings):
- DV south-east ~(74.84,18.16): clears the NXT In2 west leg
  (was -0.261 at DV (74.72,17.96)) and keeps the STP waist ~1.24.
- NXT In2 path: NV -> (74.30,17.80) -> (74.36,18.70) -> kept via
  (74.5,19.25) (two bends, west of DV's disc).
- DIR B journey: DV -> ray point -> THREAD POINT M=(73.028,18.952),
  the exact midpoint of DM via (73.625,19.125) r0.3 and CAP_DATA
  via (72.431,18.778) r0.3 (bisector: >=0.6215 from both centres at
  M; approach/exit legs run along the bisector ray) -> ray exit ->
  (71.375,19.125).
- DIR stub thread and ride shapes as t_bd9 (ride lanes re-centred
  for the new DV).
Stage 1 incumbent-tracked with immediate print; stage 2 ride on the
stage-1 winner."""
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
# thread geometry: midpoint of the two r0.3 vias + bisector ray dir
_C1 = (73.625, 19.125)
_C2 = (72.431, 18.778)
M = ((_C1[0] + _C2[0]) / 2, (_C1[1] + _C2[1]) / 2)
_ax = (_C1[0] - _C2[0], _C1[1] - _C2[1])
_al = math.hypot(*_ax)
RAY = (-_ax[1] / _al, _ax[0] / _al)   # perpendicular to C2->C1 axis
if RAY[1] > 0:
    RAY = (-RAY[0], -RAY[1])         # point the ray north (decreasing y)

def ray_pt(h):
    return (M[0] + h * RAY[0], M[1] + h * RAY[1])

def gate_stage1(nv, dv, b1, b2, in2pts, h_in, h_out, floor):
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
    ipath = [nv] + list(in2pts) + [NXT_VIA_OLD]
    for p, q in zip(ipath, ipath[1:]):
        w, a = seg_gate(1, p, q, 'ULPI_NXT', 0.1, extra=[dv_it], floor=floor)
        if w <= floor: return w, None
        if 'nxt_in2' not in det or w < det['nxt_in2'][0]:
            det['nxt_in2'] = (w, a)
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
    bpath = [dv, ray_pt(h_in), M, ray_pt(-h_out), DIR_B_END]
    w_all, a_all = 9e9, None
    for p, q in zip(bpath, bpath[1:]):
        w, a = seg_gate(2, p, q, 'ULPI_DIR', 0.1, extra=[nv_it], floor=floor)
        if w <= floor: return w, None
        if w < w_all: w_all, a_all = w, a
    det['dir_bseg'] = (w_all, a_all)
    return min(v[0] for v in det.values()), det

t0 = time.time()
best = (0.0, None)
n = 0
for nvx in (74.96, 74.99, 75.02):
    for nvy in (17.32, 17.36, 17.40):
        for dvx in (74.80, 74.84, 74.88):
            for dvy in (18.08, 18.16, 18.24):
                for b1x in (75.60, 75.65, 75.70):
                    for b2x in (75.40, 75.45, 75.50):
                        for ib in (((74.30, 17.80), (74.36, 18.70)),
                                   ((74.26, 17.85), (74.32, 18.75)),
                                   ((74.34, 17.75), (74.40, 18.65))):
                            for h_in in (0.4, 0.55):
                                for h_out in (0.7, 0.9):
                                    n += 1
                                    cfg = ((nvx, nvy), (dvx, dvy), (b1x, 17.32),
                                           (b2x, 17.85), ib, h_in, h_out)
                                    floor = best[0]
                                    w, det = gate_stage1(*cfg, floor)
                                    if det is not None and w > best[0]:
                                        best = (w, (cfg, det))
                                        print(f'  best {w:+.3f} NV={cfg[0]} DV={cfg[1]} '
                                              f'b1={cfg[2]} b2={cfg[3]} in2={ib} '
                                              f'h=({h_in},{h_out}) [{time.time()-t0:.0f}s]',
                                              flush=True)
print(f'\nstage 1 done: {n} configs, {time.time()-t0:.0f}s')
if best[1] is None:
    print('NO stage-1 configuration gates positive in family C v3')
    sys.exit(1)
score, (cfg, det) = best
nv, dv = cfg[0], cfg[1]
print(f'STAGE1 WINNER family C v3: margin {score:+.3f}')
print(f'  NV={nv} DV={dv} b1={cfg[2]} b2={cfg[3]} in2={cfg[4]} h=({cfg[5]},{cfg[6]})')
for k, v in det.items():
    print(f'  {k}: {v[0]:+.3f} binding {v[1]}')
print(f'  thread M={tuple(round(v,3) for v in M)} ray={tuple(round(v,3) for v in RAY)}')

nv_it = ('via', 'ULPI_NXT', (nv[0], nv[1], 0.25), 0.2)
dv_it = ('via', 'ULPI_DIR', (dv[0], dv[1], 0.25), 0.2)
bpath = [dv, ray_pt(cfg[5]), M, ray_pt(-cfg[6]), DIR_B_END]
dv_bsegs = [('seg', 'ULPI_DIR', (p[0], p[1], q[0], q[1], 0.1), 0.2)
            for p, q in zip(bpath, bpath[1:])]
ride_extra = [nv_it, dv_it] + dv_bsegs
mid = ((dv[0] + DIVE[0]) / 2, (dv[1] + DIVE[1]) / 2)
dvec = (DIVE[0] - dv[0], DIVE[1] - dv[1])
dl = math.hypot(*dvec)
perp = (-dvec[1] / dl, dvec[0] / dl)
dirh = (dvec[0] / dl, dvec[1] / dl)
print(f'  waist centres {dl:.3f} (ride corridor {dl-1.10:+.3f})')
best2 = (min(0.0, score), None)
for ex, ey in ((75.45, 18.30), (75.38, 18.15), (75.52, 18.38)):
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
                    joint = min(w_all, score)
                    if joint > best2[0]:
                        best2 = (joint, (pts, w_all, arg_all))
                        print(f'  ride best joint {joint:+.3f} ride {w_all:+.3f} '
                              f'waist={tuple(round(v,3) for v in wp)} lane={lx} '
                              f'wlane={wx2} binding {arg_all}', flush=True)
if best2[1] is None:
    print('NO ride gates positive over the family-C v3 winner')
    sys.exit(2)
joint, (pts, w_ride, arg_ride) = best2
print(f'\nJOINT WINNER family C v3: overall {joint:+.3f} (stage1 {score:+.3f}, '
      f'ride {w_ride:+.3f} binding {arg_ride})')
print('  ride:', [(round(x, 3), round(y, 3)) for x, y in pts])
json.dump({'family': 'C3', 'nxt_via': nv, 'dir_via': dv, 'stub_b1': cfg[2],
           'stub_b2': cfg[3], 'in2_path': [nv] + list(cfg[4]) + [NXT_VIA_OLD],
           'dir_b_path': bpath, 'ride': pts, 'stage1_margin': score,
           'ride_margin': w_ride},
          open('scratch/work/bd/design_bd_c3.json', 'w'), indent=1)
print('saved scratch/work/bd/design_bd_c3.json')

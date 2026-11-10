"""t_bd4: family C for the XI mouth on exp256.

Family B's stacking contradiction (NXT westward F run and DIR's F
stub both need the strip south of the U7 pad row) is broken by
changing WHICH net dives early:
- ULPI_NXT dives immediately: F stub (75.25,16.875) -> NEW via
  NV~(75.1,17.3) -> In2 leg rejoining the kept dive via (74.5,19.25)
  (same-net contact on In2 with the kept In2 diagonal). NXT's two
  old F legs are victims; the old via itself stays.
- ULPI_DIR via lands SOUTH at DV~(74.8,18.0); F stub steps east then
  dives SW: (75.75,16.875) -> bend ~(75.85,17.35) -> DV; B seg
  re-laid straight to (71.375,19.125). Waist DV<->STP dive ~1.27.
- XI ride on B: arc -> waist between DV and STP dive -> EAST lane
  x~75.62 (east of NV) -> west jog above the GND stitch via ->
  lane x75.02 -> NE jog -> PV (75.82,10.30).
Same exact gates as t_bd2/t_bd3 (bc's model), floor-pruned, staged.
"""
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

def gate_stage1(nv, dv, sb, floor):
    nv_it = ('via', 'ULPI_NXT', (nv[0], nv[1], 0.25), 0.2)
    dv_it = ('via', 'ULPI_DIR', (dv[0], dv[1], 0.25), 0.2)
    nxt_stub = ('seg', 'ULPI_NXT', (NXT_HEAD[0], NXT_HEAD[1], nv[0], nv[1], 0.1), 0.2)
    nxt_in2 = ('seg', 'ULPI_NXT', (nv[0], nv[1], NXT_VIA_OLD[0], NXT_VIA_OLD[1], 0.1), 0.2)
    det = {}
    w, a = via_gate(nv[0], nv[1], 'ULPI_NXT', extra_by_layer={0: [dv_it], 1: [dv_it], 2: [dv_it]}, floor=floor)
    if w <= floor: return w, None
    det['nxt_via'] = (w, a)
    w, a = seg_gate(0, NXT_HEAD, nv, 'ULPI_NXT', 0.1, extra=[dv_it], floor=floor)
    if w <= floor: return w, None
    det['nxt_stub'] = (w, a)
    w, a = seg_gate(1, nv, NXT_VIA_OLD, 'ULPI_NXT', 0.1, extra=[dv_it], floor=floor)
    if w <= floor: return w, None
    det['nxt_in2'] = (w, a)
    w, a = via_gate(dv[0], dv[1], 'ULPI_DIR', extra_by_layer={0: [nv_it, nxt_stub], 1: [nv_it], 2: [nv_it]}, floor=floor)
    if w <= floor: return w, None
    det['dir_via'] = (w, a)
    stub_pts = [DIR_HEAD] + ([sb] if sb else []) + [dv]
    w_all, a_all = 9e9, None
    for p, q in zip(stub_pts, stub_pts[1:]):
        w, a = seg_gate(0, p, q, 'ULPI_DIR', 0.1, extra=[nv_it, nxt_stub], floor=floor)
        if w <= floor: return w, None
        if w < w_all: w_all, a_all = w, a
    det['dir_stub'] = (w_all, a_all)
    w, a = seg_gate(2, dv, DIR_B_END, 'ULPI_DIR', 0.1, extra=[nv_it], floor=floor)
    if w <= floor: return w, None
    det['dir_bseg'] = (w, a)
    return min(v[0] for v in det.values()), det

t0 = time.time()
best = (0.0, None)
stub_bends = [None, (75.85, 17.35), (75.88, 17.28), (75.82, 17.42)]
n = 0
for nvx in (75.02, 75.06, 75.10, 75.14):
    for nvy in (17.22, 17.30, 17.38):
        for dvx in (74.72, 74.76, 74.80, 74.84, 74.88):
            for dvy in (17.92, 18.00, 18.08):
                for sb in stub_bends:
                    n += 1
                    w, det = gate_stage1((nvx, nvy), (dvx, dvy), sb, best[0])
                    if det is not None and w > best[0]:
                        best = (w, (nvx, nvy, dvx, dvy, sb, det))
                        print(f'  best {w:+.3f} NV=({nvx:.2f},{nvy:.2f}) DV=({dvx:.2f},{dvy:.2f}) stub={sb} [{time.time()-t0:.0f}s]', flush=True)
print(f'\nstage 1 done: {n} configs, {time.time()-t0:.0f}s')
if best[1] is None:
    print('NO stage-1 configuration gates positive in family C')
    sys.exit(1)
score, (nvx, nvy, dvx, dvy, sb, det) = best
print(f'STAGE1 WINNER family C: margin {score:+.3f}')
print(f'  NXT via -> ({nvx:.2f},{nvy:.2f}); DIR via -> ({dvx:.2f},{dvy:.2f}); stub bend {sb}')
for k, v in det.items():
    print(f'  {k}: {v[0]:+.3f} binding {v[1]}')

nv_it = ('via', 'ULPI_NXT', (nvx, nvy, 0.25), 0.2)
dv_it = ('via', 'ULPI_DIR', (dvx, dvy, 0.25), 0.2)
dv_bseg = ('seg', 'ULPI_DIR', (dvx, dvy, DIR_B_END[0], DIR_B_END[1], 0.1), 0.2)
ride_extra = [nv_it, dv_it, dv_bseg]
mid = ((dvx + DIVE[0]) / 2, (dvy + DIVE[1]) / 2)
dvec = (DIVE[0] - dvx, DIVE[1] - dvy)
dl = math.hypot(*dvec)
perp = (-dvec[1] / dl, dvec[0] / dl)
dirh = (dvec[0] / dl, dvec[1] / dl)
print(f'  waist centres {dl:.3f} (ride corridor {dl-1.10:+.3f})')

best2 = (min(0.0, score), None)
for ex, ey in ((75.45, 18.25), (75.38, 18.10), (75.52, 18.32)):
    for s in (-0.15, 0.0, 0.15):
        for t in (-0.06, -0.03, 0.0, 0.03, 0.06):
            wp = (mid[0] + s * dirh[0] + t * perp[0],
                  mid[1] + s * dirh[1] + t * perp[1])
            for lx in (75.58, 75.62, 75.66):
                pts = [ARC, (ex, ey), wp, (lx, 16.90), (lx, 16.30),
                       (75.02, 15.95), (75.02, 13.40), (75.32, 12.75), PV]
                w_all, arg_all = 9e9, None
                for p, q in zip(pts, pts[1:]):
                    w, a = seg_gate(2, p, q, 'XI', 0.1, extra=ride_extra, floor=best2[0])
                    if w < w_all:
                        w_all, arg_all = w, a
                    if w_all <= best2[0]:
                        break
                joint = min(w_all, score)
                if joint > best2[0]:
                    best2 = (joint, (pts, w_all, arg_all))
                    print(f'  ride best joint {joint:+.3f} ride {w_all:+.3f} exit=({ex},{ey}) waist={tuple(round(v,3) for v in wp)} lane={lx} binding {arg_all}', flush=True)
if best2[1] is None:
    print('NO ride gates positive over the family-C stage-1 winner')
    sys.exit(2)
joint, (pts, w_ride, arg_ride) = best2
print(f'\nJOINT WINNER family C: overall {joint:+.3f} (stage1 {score:+.3f}, ride {w_ride:+.3f} binding {arg_ride})')
print('  ride waypoints:', [(round(x, 3), round(y, 3)) for x, y in pts])
json.dump({'family': 'C', 'nxt_via': [nvx, nvy], 'dir_via': [dvx, dvy],
           'stub_bend': sb, 'ride': pts, 'stage1_margin': score,
           'ride_margin': w_ride},
          open('scratch/work/bd/design_bd_c.json', 'w'), indent=1)
print('saved scratch/work/bd/design_bd_c.json')

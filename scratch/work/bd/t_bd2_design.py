"""t_bd2: exact-gate scan for the XI mouth redesign on exp256 (bd).

Design family (brief: re-lay NXT escape bowed west, DIR via west,
user's bent B ride into PV):
- ULPI_DIR via moves west off (75.5,17.521); F stub re-laid from pad
  head (75.75,16.875) with one bend; B seg re-laid straight to the
  kept journey point (71.375,19.125).
- ULPI_NXT escape re-laid: pad head (75.25,16.875) -> bow point ->
  mid -> kept dive via (74.5,19.25). Old diagonal victims.
- Family B only: DM_PHY F loop shifted west (vertical x74.125 ->
  x74.05, both diagonals re-laid; pad stub and via-head seg kept).
- Stage 2: XI ride on B, arc via (75.625,18.625) -> exit -> waist
  point between DIR/STP dive discs -> west lane -> NE jog -> PV
  (75.82,10.30), gated against the stage-1 winner's new copper.

Gates: bc's exact dense-sample model (dist_to_item edge distance
minus new-item halfwidth minus pair-class clearance), near()-indexed,
floor-pruned. Victims are excluded from obstacle pools; new copper
gates against the board AND against the other new copper.
"""
import json, math, sys, time
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
FAMILY = sys.argv[1] if len(sys.argv) > 1 else 'B'

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
    if net == 'DM_PHY' and FAMILY == 'B':
        # the three F pieces of DM's loop that shift west
        if it[0] != 'seg':
            return False
        return seg_touch(it, 74.125, 17.375) or seg_touch(it, 74.125, 18.625)
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
NXT_VIA = (74.5, 19.25)
DM_STUB_END = (73.562, 17.0)
DM_VIA_HEAD = (73.875, 18.875)

def nxt_items(wx, wy, mx):
    return [('seg', 'ULPI_NXT', (NXT_HEAD[0], NXT_HEAD[1], wx, wy, 0.1), 0.2),
            ('seg', 'ULPI_NXT', (wx, wy, mx, 18.2, 0.1), 0.2),
            ('seg', 'ULPI_NXT', (mx, 18.2, NXT_VIA[0], NXT_VIA[1], 0.1), 0.2)]

def dm_items():
    return [('seg', 'DM_PHY', (DM_STUB_END[0], DM_STUB_END[1], 74.05, 17.375, 0.125), 0.2),
            ('seg', 'DM_PHY', (74.05, 17.375, 74.05, 18.625, 0.125), 0.2),
            ('seg', 'DM_PHY', (74.05, 18.625, DM_VIA_HEAD[0], DM_VIA_HEAD[1], 0.125), 0.2)]

def gate_config(vx, vy, wx, wy, mx, stub_bend, floor):
    """Return (score, detail dict) or (<=floor, None) early."""
    nxt = nxt_items(wx, wy, mx)
    dm = dm_items() if FAMILY == 'B' else []
    f_extra = nxt + dm
    det = {}
    # DIR via vs board + new F copper projected on all layers
    w, a = via_gate(vx, vy, 'ULPI_DIR',
                    extra_by_layer={0: f_extra}, floor=floor)
    if w <= floor:
        return w, None
    det['dir_via'] = (w, a)
    # DIR stub (F)
    stub_pts = [DIR_HEAD] + ([stub_bend] if stub_bend else []) + [(vx, vy)]
    for p, q in zip(stub_pts, stub_pts[1:]):
        w, a = seg_gate(0, p, q, 'ULPI_DIR', 0.1, extra=f_extra, floor=floor)
        if w <= floor:
            return w, None
        det.setdefault('dir_stub', (9e9, None))
        if w < det['dir_stub'][0]:
            det['dir_stub'] = (w, a)
    # DIR B seg
    w, a = seg_gate(2, (vx, vy), DIR_B_END, 'ULPI_DIR', 0.1, floor=floor)
    if w <= floor:
        return w, None
    det['dir_bseg'] = (w, a)
    # NXT legs (F) vs board + DIR via
    dir_via_it = ('via', 'ULPI_DIR', (vx, vy, 0.25), 0.2)
    for it in nxt:
        d = it[2]
        w, a = seg_gate(0, (d[0], d[1]), (d[2], d[3]), 'ULPI_NXT', 0.1,
                        extra=[dir_via_it] + dm, floor=floor)
        if w <= floor:
            return w, None
        det.setdefault('nxt', (9e9, None))
        if w < det['nxt'][0]:
            det['nxt'] = (w, a)
    # DM legs (F) vs board + DIR via + NXT
    for it in dm:
        d = it[2]
        w, a = seg_gate(0, (d[0], d[1]), (d[2], d[3]), 'DM_PHY', 0.125,
                        extra=[dir_via_it] + nxt, floor=floor)
        if w <= floor:
            return w, None
        det.setdefault('dm', (9e9, None))
        if w < det['dm'][0]:
            det['dm'] = (w, a)
    score = min(v[0] for v in det.values())
    return score, det

t0 = time.time()
best = (0.0, None)
stub_bends = [None, (75.55, 17.15), (75.58, 17.08), (75.48, 17.22)]
n_tested = 0
for wx in [74.40 + 0.04 * k for k in range(6)]:
    for wy in (16.98, 17.04, 17.10):
        for vx in [74.78 + 0.02 * k for k in range(14)]:
            for vy in (17.50, 17.55, 17.60, 17.65, 17.70):
                for mx in (74.50, 74.54, 74.58, 74.62, 74.66):
                    for sb in stub_bends:
                        n_tested += 1
                        w, det = gate_config(vx, vy, wx, wy, mx, sb, best[0])
                        if det is not None and w > best[0]:
                            best = (w, (vx, vy, wx, wy, mx, sb, det))
                            print(f'  best {w:+.3f} DIR=({vx:.2f},{vy:.2f}) '
                                  f'bow=({wx:.2f},{wy:.2f}) mx={mx:.2f} stub={sb} '
                                  f'[{time.time()-t0:.0f}s]', flush=True)
print(f'\nstage 1 done: {n_tested} configs, {time.time()-t0:.0f}s')
if best[1] is None:
    print('NO stage-1 configuration gates positive in family', FAMILY)
    sys.exit(1)
score, (vx, vy, wx, wy, mx, sb, det) = best
print(f'STAGE1 WINNER family {FAMILY}: margin {score:+.3f}')
print(f'  DIR via -> ({vx:.2f},{vy:.2f}); NXT bow ({wx:.2f},{wy:.2f}), mid x={mx:.2f}; stub bend {sb}')
for k, v in det.items():
    print(f'  {k}: {v[0]:+.3f} binding {v[1]}')

# ---- stage 2: the XI ride against the winner's copper -----------------------
ARC = (75.625, 18.625)
PV = (75.82, 10.30)
DIVE = (76.065, 17.96)
nxt = nxt_items(wx, wy, mx)
dm = dm_items() if FAMILY == 'B' else []
dir_via_it = ('via', 'ULPI_DIR', (vx, vy, 0.25), 0.2)
dir_bseg_it = ('seg', 'ULPI_DIR', (vx, vy, DIR_B_END[0], DIR_B_END[1], 0.1), 0.2)
ride_extra_b = [dir_via_it, dir_bseg_it]

mid = ((vx + DIVE[0]) / 2, (vy + DIVE[1]) / 2)
dvec = (DIVE[0] - vx, DIVE[1] - vy)
dl = math.hypot(*dvec)
perp = (-dvec[1] / dl, dvec[0] / dl)
dirh = (dvec[0] / dl, dvec[1] / dl)

best2 = (min(0.0, score), None)
for ex, ey in ((75.42, 18.20), (75.35, 18.05), (75.50, 18.30)):
    for s in (-0.15, 0.0, 0.15):
        for t in (-0.06, -0.03, 0.0, 0.03, 0.06):
            wp = (mid[0] + s * dirh[0] + t * perp[0],
                  mid[1] + s * dirh[1] + t * perp[1])
            for lx in (74.92, 74.97, 75.02):
                for jx, jy in ((75.32, 12.75), (75.42, 12.60)):
                    pts = [ARC, (ex, ey), wp, (lx, 16.55), (lx, 13.40),
                           (jx, jy), PV]
                    w_all, arg_all = 9e9, None
                    for p, q in zip(pts, pts[1:]):
                        w, a = seg_gate(2, p, q, 'XI', 0.1,
                                        extra=ride_extra_b,
                                        floor=best2[0])
                        if w < w_all:
                            w_all, arg_all = w, a
                        if w_all <= best2[0]:
                            break
                    joint = min(w_all, score)
                    if joint > best2[0]:
                        best2 = (joint, (pts, w_all, arg_all))
                        print(f'  ride best joint {joint:+.3f} ride {w_all:+.3f} '
                              f'exit=({ex},{ey}) waist={tuple(round(v,3) for v in wp)} '
                              f'lane={lx} jog=({jx},{jy}) binding {arg_all}', flush=True)
if best2[1] is None:
    print('NO ride gates positive over the stage-1 winner')
    sys.exit(2)
joint, (pts, w_ride, arg_ride) = best2
print(f'\nJOINT WINNER: overall margin {joint:+.3f} (stage1 {score:+.3f}, ride {w_ride:+.3f} binding {arg_ride})')
print('  ride waypoints:', [(round(x, 3), round(y, 3)) for x, y in pts])
json.dump({'family': FAMILY, 'dir_via': [vx, vy], 'nxt_bow': [wx, wy],
           'nxt_midx': mx, 'stub_bend': sb, 'ride': pts,
           'stage1_margin': score, 'ride_margin': w_ride},
          open('scratch/work/bd/design_bd.json', 'w'), indent=1)
print('saved scratch/work/bd/design_bd.json')

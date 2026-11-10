"""t_bd3: diagnostic for t_bd2 family B -- track the BEST stage-1
configuration regardless of sign and print its per-element detail,
so the binding fence is named with arithmetic instead of guessed.
Same gates/victims as t_bd2 family B; floor pruning disabled except
a loose -0.60 cutoff to keep it fast."""
import math, sys, time
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
    if net == 'DM_PHY':
        if it[0] != 'seg':
            return False
        return seg_touch(it, 74.125, 17.375) or seg_touch(it, 74.125, 18.625)
    return False

def seg_gate(li, a, b, net, hw, extra=(), step=0.04, floor=-9e9):
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

def nxt_items(wx, wy, mx):
    return [('seg', 'ULPI_NXT', (NXT_HEAD[0], NXT_HEAD[1], wx, wy, 0.1), 0.2),
            ('seg', 'ULPI_NXT', (wx, wy, mx, 18.2, 0.1), 0.2),
            ('seg', 'ULPI_NXT', (mx, 18.2, NXT_VIA[0], NXT_VIA[1], 0.1), 0.2)]

def dm_items():
    return [('seg', 'DM_PHY', (73.562, 17.0, 74.05, 17.375, 0.125), 0.2),
            ('seg', 'DM_PHY', (74.05, 17.375, 74.05, 18.625, 0.125), 0.2),
            ('seg', 'DM_PHY', (74.05, 18.625, 73.875, 18.875, 0.125), 0.2)]

def full_detail(vx, vy, wx, wy, mx, sb):
    nxt = nxt_items(wx, wy, mx)
    dm = dm_items()
    det = {}
    det['dir_via'] = via_gate(vx, vy, 'ULPI_DIR', extra_by_layer={0: nxt + dm})
    stub_pts = [DIR_HEAD] + ([sb] if sb else []) + [(vx, vy)]
    w_all, a_all = 9e9, None
    for p, q in zip(stub_pts, stub_pts[1:]):
        w, a = seg_gate(0, p, q, 'ULPI_DIR', 0.1, extra=nxt + dm)
        if w < w_all:
            w_all, a_all = w, a
    det['dir_stub'] = (w_all, a_all)
    det['dir_bseg'] = seg_gate(2, (vx, vy), DIR_B_END, 'ULPI_DIR', 0.1)
    dir_via_it = ('via', 'ULPI_DIR', (vx, vy, 0.25), 0.2)
    w_all, a_all = 9e9, None
    for it in nxt:
        d = it[2]
        w, a = seg_gate(0, (d[0], d[1]), (d[2], d[3]), 'ULPI_NXT', 0.1,
                        extra=[dir_via_it] + dm)
        if w < w_all:
            w_all, a_all = w, a
    det['nxt'] = (w_all, a_all)
    w_all, a_all = 9e9, None
    for it in dm:
        d = it[2]
        w, a = seg_gate(0, (d[0], d[1]), (d[2], d[3]), 'DM_PHY', 0.125,
                        extra=[dir_via_it] + nxt)
        if w < w_all:
            w_all, a_all = w, a
    det['dm'] = (w_all, a_all)
    return min(v[0] for v in det.values()), det

t0 = time.time()
tops = []
stub_bends = [None, (75.55, 17.15), (75.58, 17.08), (75.48, 17.22)]
for wx in [74.40 + 0.04 * k for k in range(6)]:
    for wy in (16.98, 17.04, 17.10):
        for vx in [74.78 + 0.02 * k for k in range(14)]:
            for vy in (17.50, 17.55, 17.60, 17.65, 17.70):
                for mx in (74.50, 74.54, 74.58, 74.62, 74.66):
                    for sb in stub_bends:
                        # cheap pre-gate: DIR via vs NXT legs only
                        nxt = nxt_items(wx, wy, mx)
                        w0, _a = via_gate(vx, vy, 'ULPI_DIR',
                                          extra_by_layer={0: nxt}, floor=-0.60)
                        if w0 <= -0.60:
                            continue
                        w, det = full_detail(vx, vy, wx, wy, mx, sb)
                        tops.append((w, vx, vy, wx, wy, mx, sb, det))
                        tops.sort(key=lambda t: -t[0])
                        tops = tops[:5]
print(f'diag done {time.time()-t0:.0f}s; top stage-1 configs (family B):')
for w, vx, vy, wx, wy, mx, sb, det in tops:
    print(f'  score {w:+.3f} DIR=({vx:.2f},{vy:.2f}) bow=({wx:.2f},{wy:.2f}) mx={mx:.2f} stub={sb}')
    for k, v in det.items():
        print(f'      {k}: {v[0]:+.3f} binding {v[1]}')

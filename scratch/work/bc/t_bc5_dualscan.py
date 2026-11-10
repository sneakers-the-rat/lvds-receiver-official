"""t_bc5: 2D via-landing scans for both XI mouth vias on exp256.

The bent B ride needs the waist between ULPI_DIR's dive via and
ULPI_STP's dive via: track centres on B must pass >=0.55 from both via
centres (via r0.25 + track hw0.1 + 0.20 clearance, both nets default
class), so the centres must be >=1.10 apart. Stock distance: 0.728.

A via landing is gated on ALL layers (through via) against every
foreign item, excluding the moving net's own ripped copper at the dive
(its stub/column head is re-laid). Legs are NOT gated here -- the via
disc is the hard constraint; compact leg re-lays follow a landing.
Then: joint test over all passing (DIR, STP) landing pairs.
"""
import math, sys
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

def touches(it, px, py):
    if it[0] == 'via':
        return abs(it[2][0] - px) < 0.01 and abs(it[2][1] - py) < 0.01
    if it[0] == 'seg':
        x1, y1, x2, y2, _h = it[2]
        return (abs(x1 - px) < 0.01 and abs(y1 - py) < 0.01) or \
               (abs(x2 - px) < 0.01 and abs(y2 - py) < 0.01)
    return False

DIR0 = (75.5, 17.521)
STP0 = (76.065, 17.96)

def via_gate(x, y, net, home):
    """Copper touching EITHER stock dive is excluded (both dives may
    move; their stubs/column heads are re-laid). The joint test then
    enforces the pair's centre distance, which subsumes via-via
    clearance between the two moved dives."""
    worst, arg = 9e9, None
    for li in range(3):
        seen = set()
        for it in items[li].near(li, x, y):
            if it[1] == net or id(it) in seen:
                continue
            seen.add(id(it))
            if touches(it, *DIR0) or touches(it, *STP0):
                continue
            d = dist_to_item(it, x, y) - 0.25 - pair_clr(net, it[1])
            if d < worst:
                worst, arg = d, (LAYN[li], it[1], it[0])
    return worst, arg

def scan(net, home, xs, ys, label):
    ok = []
    for x in xs:
        for y in ys:
            w, arg = via_gate(x, y, net, home)
            if w > 0:
                ok.append((w, x, y, arg))
    ok.sort(key=lambda t: -t[0])
    print(f'{label}: {len(ok)} passing landings')
    for w, x, y, arg in ok[:12]:
        print(f'   ({x:.2f},{y:.2f}) margin {w:+.3f} nearest {arg}')
    return ok

print('stock centre distance DIR<->STP dive:',
      round(math.hypot(DIR0[0] - STP0[0], DIR0[1] - STP0[1]), 3),
      '(waist needs >= 1.100)')

xs = [74.55 + 0.05 * k for k in range(21)]
ys = [16.95 + 0.05 * k for k in range(35)]
dir_ok = scan('ULPI_DIR', DIR0, xs, ys, 'DIR via 2D scan x[74.55,75.55] y[16.95,18.65]')

xs2 = [75.90 + 0.05 * k for k in range(18)]
ys2 = [17.55 + 0.05 * k for k in range(24)]
stp_ok = scan('ULPI_STP', STP0, xs2, ys2, 'STP dive 2D scan x[75.90,76.75] y[17.55,18.70]')

print('\njoint waist test (pairs with centre distance >= 1.10):')
found = 0
best_pair = (0.0, None, None)
for w1, x1, y1, _a in dir_ok:
    for w2, x2, y2, _b in stp_ok:
        d = math.hypot(x1 - x2, y1 - y2)
        if d > best_pair[0]:
            best_pair = (d, (x1, y1, w1), (x2, y2, w2))
        if d >= 1.10:
            print(f'  DIR ({x1:.2f},{y1:.2f}) [{w1:+.3f}]  STP ({x2:.2f},{y2:.2f}) '
                  f'[{w2:+.3f}]  centres {d:.3f}')
            found += 1
            if found >= 15:
                break
    if found >= 15:
        break
if not found:
    print('  NONE -- no individually-legal pair of landings opens the waist')
d, p1, p2 = best_pair
print(f'max centre distance over all passing pairs: {d:.3f} '
      f'(DIR {p1} / STP {p2}) vs 1.100 needed -- deficit {1.100 - d:.3f}')

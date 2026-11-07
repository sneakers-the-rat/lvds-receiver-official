"""t_ab17: U7 south-exit via packing solver (on exp213).

Question: can CK's dive via move east AND STP/DIR/NXT each get
a dive via, all DRC-legal at once? Hand attempts kept missing
standing items; this scans on-grid (0.125) candidate points
against repair.build_items with CK's old via + F stub + In2
southern leg RIPPED in memory, sequentially: CK (d0.6), STP,
DIR, NXT (d0.5), each placed via becoming an obstacle for the
next scan. A via point is legal if on EVERY layer its disc
keeps pair clearance (check_pcb classes) to all foreign items.
Also seg-tests CK's F stub and three In2 leg shapes for the
winning CK point (the direct vertical crossed a +3V3A In2
horizontal in t_ab16).
"""
import math, sys
sys.path.insert(0, 'hw')
import pcbnew
import repair, router
from router import netclass, dist_to_item

board = pcbnew.LoadBoard('scratch/work/t_ab17_base.kicad_pcb')
MM = pcbnew.ToMM
items, _ = repair.build_items(board)

extra = []  # placed solver vias: (x, y, r, net)
def via_margin(x, y, r, net):
    worst = 9.9
    for li in range(3):
        for it in items[li].near(li, x, y):
            if it[1] == net:
                continue
            need = r + max(netclass(net)[1],
                           netclass(it[1])[1] if it[1] else 0.2)
            worst = min(worst, dist_to_item(it, x, y) - need)
    for (ex, ey, er, en) in extra:
        if en == net:
            continue
        need = r + er + max(netclass(net)[1], netclass(en)[1])
        worst = min(worst, math.hypot(x - ex, y - ey) - need)
    return worst

def seg_margin(li, a, b, net, hw=0.1):
    worst = 9.9
    n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 0.03))
    for k in range(n + 1):
        x = a[0] + (b[0] - a[0]) * k / n
        y = a[1] + (b[1] - a[1]) * k / n
        for it in items[li].near(li, x, y):
            if it[1] == net:
                continue
            need = hw + max(netclass(net)[1],
                            netclass(it[1])[1] if it[1] else 0.2)
            worst = min(worst, dist_to_item(it, x, y) - need)
        for (ex, ey, er, en) in extra:
            if en == net:
                continue
            need = hw + er + max(netclass(net)[1], netclass(en)[1])
            worst = min(worst, math.hypot(x - ex, y - ey) - need)
    return worst

def scan(net, r, x0, x1, y0, y1, topn=12):
    out = []
    nx = int(round((x1 - x0) / 0.125)) + 1
    ny = int(round((y1 - y0) / 0.125)) + 1
    for i in range(nx):
        for j in range(ny):
            x, y = x0 + i * 0.125, y0 + j * 0.125
            m = via_margin(x, y, r, net)
            if m >= 0:
                out.append((m, x, y))
    out.sort(reverse=True)
    return out[:topn]

def ck_leg_ok(cx, cy):
    """In2 leg shapes from CK via (cx,cy) to trunk point
    (76.62,13.50); returns list of shape names that pass."""
    shapes = {
        'direct': [(cx, cy), (cx, 13.50), (76.62, 13.50)],
        'west-first': [(cx, cy), (74.875, cy), (74.875, 13.50),
                       (76.62, 13.50)],
        'step': [(cx, cy), (cx, 14.625), (76.625, 14.625),
                 (76.625, 13.50)],
    }
    ok = []
    for name, pts in shapes.items():
        m = min(seg_margin(1, a, b, 'ULPI_CK', 0.125)
                for a, b in zip(pts, pts[1:]))
        if m >= 0:
            ok.append((name, round(m, 3)))
    return ok

cks = scan('ULPI_CK', 0.30, 76.50, 77.50, 17.00, 18.00)
print(f'CK via candidates: {len(cks)}')
for m, x, y in cks:
    print(f'  CK ({x:.3f},{y:.3f}) margin {m:+.3f}')
solution = None
for cm, cx, cy in cks:
    legs = ck_leg_ok(cx, cy)
    stub_m = seg_margin(0, (76.75, 16.438), (cx, cy), 'ULPI_CK')
    print(f' CK ({cx:.3f},{cy:.3f}): legs={legs} stub={stub_m:+.3f}')
    if not legs:
        continue
    if stub_m < 0:
        continue
    extra.append((cx, cy, 0.30, 'ULPI_CK'))
    stps = scan('ULPI_STP', 0.25, 75.95, 77.35, 17.30, 18.15)
    print(f'   STP candidates with this CK: {len(stps)} {stps[:3]}')
    for sm, sx, sy in stps:
        extra.append((sx, sy, 0.25, 'ULPI_STP'))
        dirs = scan('ULPI_DIR', 0.25, 75.30, 76.10, 17.00, 17.90)
        for dm, dx, dy in dirs:
            extra.append((dx, dy, 0.25, 'ULPI_DIR'))
            nxts = scan('ULPI_NXT', 0.25, 74.70, 75.45, 17.00, 18.00)
            if nxts:
                solution = ((cm, cx, cy, legs, round(stub_m, 3)),
                            (sm, sx, sy), (dm, dx, dy), nxts[0])
                break
            extra.pop()
        if solution:
            break
        extra.pop()
    if solution:
        break
    extra.pop()

if solution:
    (ck, stp, dirv, nxt) = solution
    print(f'SOLUTION: CK via ({ck[1]:.3f},{ck[2]:.3f}) margin '
          f'{ck[0]:+.3f} legs={ck[3]} stub_margin={ck[4]}')
    print(f'  STP via ({stp[1]:.3f},{stp[2]:.3f}) margin {stp[0]:+.3f}')
    print(f'  DIR via ({dirv[1]:.3f},{dirv[2]:.3f}) margin {dirv[0]:+.3f}')
    print(f'  NXT via ({nxt[1]:.3f},{nxt[2]:.3f}) margin {nxt[0]:+.3f}')
else:
    print('NO COMPLETE QUADRUPLE FOUND')

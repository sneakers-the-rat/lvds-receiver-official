"""t_ba11: C23 relocation site scan, district south of U7.
Board facts via pcbnew (footprints, courtyard bboxes, exact U7
south-row pad rects) + model pool gates for the F feed from
U7.29 and GND via sites near pad2. Candidates: centre grid
x[76.2,78.2] x y[9.8,11.0], rots 0/180 (0603 pads +-0.775)."""
import sys
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
import wx
_app = wx.App(False)
import pcbnew
from t_ax0_pre import load_board_pool, C, item_margin

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp252.kicad_pcb')
MM = 1e6

print('--- footprints with bbox intersecting x[70,82] y[7,13.5] ---')
fps = []
for fp in b.GetFootprints():
    bb = fp.GetBoundingBox()
    fx0, fx1 = bb.GetLeft() / MM, bb.GetRight() / MM
    fy0, fy1 = -bb.GetBottom() / MM, -bb.GetTop() / MM
    if fx0 < 82 and fx1 > 70 and fy0 < 13.5 and fy1 > 7:
        pos = fp.GetPosition()
        print(f'  {fp.GetReference()} at ({pos.x/MM:.2f},{-pos.y/MM:.2f}) '
              f'bbox x[{fx0:.2f},{fx1:.2f}] y[{fy0:.2f},{fy1:.2f}]')
        fps.append((fp.GetReference(), fx0, fx1, fy0, fy1))

print('--- U7 south-row pads (y<12.2) exact rects ---')
u7 = None
for fp in b.GetFootprints():
    if fp.GetReference() == 'U7':
        u7 = fp
for p in u7.Pads():
    pos = p.GetPosition()
    cx, cy = pos.x / MM, -pos.y / MM
    if cy < 12.2:
        sz = p.GetSize()
        print(f'  U7.{p.GetPadName()} {p.GetNetname()} centre '
              f'({cx:.3f},{cy:.3f}) size ({sz.x/MM:.2f}x{sz.y/MM:.2f})')

pool = load_board_pool('hw/pdlvds_rx.exp252.kicad_pcb')


def gate_track(l, net, x1, y1, x2, y2, hw=0.10):
    it = ('seg', net, (x1, y1, x2, y2, hw), 0.2)
    worst = 9.9
    for o in pool[l]:
        if o[1] == net:
            continue
        m = item_margin(l, it, [o])
        if m < worst:
            worst = m
    return worst


def gate_via(x, y, net='GND'):
    worst = 9.9
    it = ('via', net, (x, y, 0.25), 0.2)
    for l in range(3):
        for o in pool[l]:
            if o[1] == net:
                continue
            m = item_margin(l, it, [o])
            if m < worst:
                worst = m
    return worst


print('--- candidate sites ---')
best = []
for rot in (0, 180):
    for cx10 in range(762, 783, 2):
        for cy10 in range(98, 111, 2):
            cx, cy = cx10 / 10.0, cy10 / 10.0
            # courtyard proxy: 0603 courtyard ~2.4 x 1.7
            x0, x1, y0, y1 = cx - 1.2, cx + 1.2, cy - 0.85, cy + 0.85
            clash = None
            for (ref, fx0, fx1, fy0, fy1) in fps:
                if ref == 'C23':
                    continue
                if x0 < fx1 and fx0 < x1 and y0 < fy1 and fy0 < y1:
                    clash = ref
                    break
            if clash:
                continue
            if rot == 0:
                p1 = (cx - 0.775, cy)
                p2 = (cx + 0.775, cy)
            else:
                p1 = (cx + 0.775, cy)
                p2 = (cx - 0.775, cy)
            # F feed U7.29 (75.75,11.5625) -> south -> east at run_y
            # -> south into pad1; best over run heights
            feed = -9.9
            for run_y in (10.72, 10.82, 10.92, 11.02):
                if run_y < p1[1] + 0.18:
                    continue
                g1 = gate_track(0, 'PHY_1V8A', 75.75, 11.5625, 75.75, run_y)
                g2 = gate_track(0, 'PHY_1V8A', 75.75, run_y, p1[0], run_y)
                g3 = gate_track(0, 'PHY_1V8A', p1[0], run_y, p1[0], p1[1])
                feed = max(feed, min(g1, g2, g3))
            # GND via sites near pad2 (incl. stub offsets)
            via_best = -9.9
            via_at = None
            for dx in (-0.75, -0.5, -0.25, 0.0, 0.25, 0.5, 0.75):
                for dy in (-1.0, -0.75, -0.5, -0.25, 0.25, 0.5, 0.75, 1.0):
                    vx, vy = p2[0] + dx, p2[1] + dy
                    gv = gate_via(vx, vy)
                    if gv > via_best:
                        via_best, via_at = gv, (round(vx, 2), round(vy, 2))
            best.append((round(min(feed, via_best), 3), rot, (cx, cy),
                         tuple(round(v, 2) for v in p1),
                         tuple(round(v, 2) for v in p2),
                         round(feed, 3), round(via_best, 3), via_at))
best.sort(reverse=True)
for row in best[:10]:
    print('  score', row)
print('=== done ===')

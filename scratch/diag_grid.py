import math, sys
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch/heal8')
import pcbnew, repair, router
from router import netclass
b = pcbnew.LoadBoard('scratch/stitch182b.kicad_pcb')
items, _ = repair.build_items(b)
VIA_R, MARGIN, gnd_clr = 0.3, 0.05, 0.2
holes = []
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        p = pcbnew.ToMM(t.GetPosition()); holes.append((p[0], p[1], pcbnew.ToMM(t.GetDrill())/2))
for fp in b.GetFootprints():
    for pad in fp.Pads():
        if pad.GetDrillSize().x > 0:
            p = pcbnew.ToMM(pad.GetPosition()); holes.append((p[0], p[1], pcbnew.ToMM(pad.GetDrillSize().x)/2))
in1f = []
for t in b.GetTracks():
    if t.GetLayer() == pcbnew.In1_Cu and t.GetNetname() != 'GND':
        in1f.append((t.GetNetname(), pcbnew.ToMM(t.GetStart()), pcbnew.ToMM(t.GetEnd()), pcbnew.ToMM(t.GetWidth())/2))
def spd(x, y, a, bb):
    px, py = x-a[0], y-a[1]; dx, dy = bb[0]-a[0], bb[1]-a[1]
    L2 = dx*dx+dy*dy; t = 0.0 if L2 == 0 else max(0.0, min(1.0, (px*dx+py*dy)/L2))
    return math.hypot(px-t*dx, py-t*dy)
def via_ok(x, y):
    for hx, hy, hr in holes:
        if math.hypot(x-hx, y-hy) - 0.15 - hr < 0.25: return False
    for li in range(3):
        for it in items[li].near(li, x, y):
            if it[1] == 'GND': continue
            if router.dist_to_item(it, x, y) < VIA_R + max(gnd_clr, netclass(it[1])[1]) + MARGIN: return False
    for net, a, bb, hw in in1f:
        if spd(x, y, a, bb) < hw + VIA_R + max(gnd_clr, netclass(net)[1]) + MARGIN: return False
    return True
def stub_ok(x1, y1, x2, y2):
    hw = 0.125
    steps = max(2, int(math.hypot(x2-x1, y2-y1)/0.2))
    for i in range(steps+1):
        x = x1+(x2-x1)*i/steps; y = y1+(y2-y1)*i/steps
        for it in items[0].near(0, x, y):
            if it[1] == 'GND': continue
            if router.dist_to_item(it, x, y) < hw + max(gnd_clr, netclass(it[1])[1]) + MARGIN: return False
    return True
TX, TY = 25.35, -2.0
print('map x[19..33] y[-8..4]: V=via_ok S=via+stub .=neither  (cols 0.5mm, rows 1mm) target U10.5 at (25.35,-2)')
for gy in range(-8, 5):
    row = ''
    for gx2 in range(19*2, 33*2+1):
        x, y = gx2/2, float(gy)
        if abs(x-TX) < 0.3 and abs(y-TY) < 0.6: row += 'T'; continue
        v = via_ok(x, y)
        row += ('S' if v and stub_ok(TX, TY, x, y) else 'V' if v else '.')
    print(f'y={gy:3d} {row}')

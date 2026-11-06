import math, sys
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch/heal8')
import pcbnew, repair, router
from router import netclass
b = pcbnew.LoadBoard('scratch/stitch182b.kicad_pcb')
items, _ = repair.build_items(b)
VIA_R = 0.3
for cx, cy, name in [(25.35, -2.0, 'U10.5'), (22.27, -1.5, 'C29.2')]:
    print(f'--- blockers near {name} ({cx},{cy})')
    seen = {}
    for li in range(3):
        for it in items[li].near(li, cx, cy):
            if it[1] == 'GND': continue
            d = router.dist_to_item(it, cx, cy)
            if d < 4:
                key = (li, it[0], it[1])
                if key not in seen or d < seen[key]: seen[key] = d
    for (li, kind, net), d in sorted(seen.items(), key=lambda kv: kv[1])[:10]:
        print(f'   layer {li} {kind} {net}: dist {d:.2f} (need >= {VIA_R + max(0.2, netclass(net)[1]) + 0.05:.2f})')
    # holes
    print('   holes within 3mm:')
    for t in b.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            p = pcbnew.ToMM(t.GetPosition())
            if math.hypot(p[0]-cx, p[1]-cy) < 3: print('     via', t.GetNetname(), (round(p[0],2), round(p[1],2)))
    for fp in b.GetFootprints():
        for pad in fp.Pads():
            if pad.GetDrillSize().x > 0:
                p = pcbnew.ToMM(pad.GetPosition())
                if math.hypot(p[0]-cx, p[1]-cy) < 3: print('     PTH', fp.GetReference(), pad.GetNumber(), pad.GetNetname(), (round(p[0],2), round(p[1],2)))

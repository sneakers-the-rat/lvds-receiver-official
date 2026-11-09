import sys, json, math
sys.path.insert(0, 'scratch/work/ax')
H = {'__name__': 'ax252head'}
src = open('scratch/work/ax/t_ax252_design214ae.py').read()
exec(src.split("\nbox = (64.0")[0], H)
pool = H['pool']
add_items = H['add_items']
journey_items_dense = H['journey_items_dense']
D = json.load(open('scratch/work/ax/design214_ax252.json'))
for J in D['stp_legs']:
    add_items(journey_items_dense(J, 'ULPI_STP', hw=0.10))
add_items({0: [('seg', 'ULPI_STP', (76.25, 16.95, 76.05, 18.0, 0.1), 0.2),
               ('via', 'ULPI_STP', (76.065, 17.99, 0.25), 0.2)]})

def df_pt_rect(it, cx, cy, hw, hh):
    kind, d = it[0], it[2]
    if kind == 'pad':
        pcx, pcy, phw, phh, rot = d
        return math.hypot(max(abs(cx - pcx) - (hw + phw), 0.0),
                          max(abs(cy - pcy) - (hh + phh), 0.0))
    if kind == 'seg':
        x1, y1, x2, y2, shw = d
        # distance from rect (cx,cy,hw,hh) to segment: sample segment finely
        best = 1e9
        n = 24
        for i in range(n + 1):
            t = i / n
            px, py = x1 + t * (x2 - x1), y1 + t * (y2 - y1)
            dd = math.hypot(max(abs(px - cx) - hw, 0.0),
                            max(abs(py - cy) - hh, 0.0))
            best = min(best, dd)
        return best - shw
    return math.hypot(max(abs(cx - d[0]) - hw, 0.0),
                      max(abs(cy - d[1]) - hh, 0.0)) - d[2]

for (cx, cy, rot) in ((78.15, 17.5, 0), (78.1, 17.5, 0), (78.2, 17.45, 0),
                      (78.15, 17.55, 0), (78.05, 17.5, 0)):
    pads = [(cx - 0.48, cy, 'PHY_1V8'), (cx + 0.48, cy, 'GND')]
    ok = True
    for (px, py, net) in pads:
        worst = (1e9, None)
        for it in pool[0]:
            if it[1] == net:
                continue
            g = df_pt_rect(it, px, py, 0.28, 0.31) - max(0.2, it[3])
            if g < worst[0]:
                worst = (g, it)
        print(f'  site ({cx},{cy}) rot {rot} pad {net} ({px},{py}): '
              f'worst {worst[0]:+.3f} vs {worst[1][1]} {worst[1][0]}',
              flush=True)
        if worst[0] < 0:
            ok = False
    # annulus overlap: PHY pad rect vs via (78.1,17.5) r0.3
    px, py = pads[0][0], pads[0][1]
    dx = max(abs(78.1 - px) - 0.28, 0.0)
    dy = max(abs(17.5 - py) - 0.31, 0.0)
    print(f'    PHY pad-via centre dist {math.hypot(78.1-px, 17.5-py):.3f} '
          f'rect-disc gap {math.hypot(dx, dy):.3f} (<=0.3 = annulus overlap)',
          flush=True)
    print(f'  site ({cx},{cy}):', 'PAD-LEGAL' if ok else 'ILLEGAL',
          flush=True)

import sys, json, math
sys.path.insert(0, 'scratch/work/ax')
src = open('scratch/work/ax/t_ax252_design214ae.py').read()
exec(src.split("\nbox = (64.0")[0])
D = json.load(open('scratch/work/ax/design214_ax252.json'))
for J in D['stp_legs']:
    add_items(journey_items_dense(J, 'ULPI_STP', hw=0.10))
add_items({0: [('seg', 'ULPI_STP', (76.25, 16.95, 76.05, 18.0, 0.1), 0.2),
               ('via', 'ULPI_STP', (76.065, 17.99, 0.25), 0.2)]})
staged = [it for it in pool[0] if it[0] == 'pad'
          and abs(it[2][1] - 18.6) < 0.01 and it[2][0] in (79.12, 80.08)]
rip_items(staged)
add_items({0: [('pad', 'PHY_1V8', (72.02, 18.0, 0.280, 0.310, 0.0), 0.2),
               ('pad', 'GND', (72.98, 18.0, 0.280, 0.310, 0.0), 0.2)]})
add_items({l: [('via', 'GND', (73.434, 17.685, 0.25), 0.2)]
           for l in range(3)})

def df_pt(it, px, py):
    kind, d = it[0], it[2]
    if kind == 'pad':
        cx, cy, hw, hh, rot = d
        dx, dy = px - cx, py - cy
        c, s = math.cos(-rot), math.sin(-rot)
        lx, ly = dx * c - dy * s, dx * s + dy * c
        return math.hypot(max(abs(lx) - hw, 0.0), max(abs(ly) - hh, 0.0))
    if kind == 'seg':
        x1, y1, x2, y2, hw = d
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px-x1)*dx + (py-y1)*dy)/L2))
        return math.hypot(px - (x1 + t*dx), py - (y1 + t*dy)) - hw
    return math.hypot(px - d[0], py - d[1]) - d[2]

for (px, py, label) in ((72.02, 18.0, 'START C22 PHY pad'),
                        (77.25, 17.188, 'GOAL F seg joint'),
                        (78.1, 17.5, 'GOAL via')):
    print(f'--- {label} ({px},{py}) ---', flush=True)
    for lay in range(3):
        rows = []
        for it in pool[lay]:
            if it[1] == 'PHY_1V8':
                continue
            g = df_pt(it, px, py) - max(0.2, it[3])
            if g < 0.45:
                rows.append((round(g, 3), it[1], it[0], it[2]))
        rows.sort()
        print(f'  L{lay}:', rows[:5], flush=True)

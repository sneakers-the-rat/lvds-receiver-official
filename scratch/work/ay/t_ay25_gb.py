import sys, json, math
sys.path.insert(0, 'scratch/work/ax')
src = open('scratch/work/ax/t_ax252_design214ae.py').read()
exec(src.split("\nbox = (64.0")[0])
D = json.load(open('scratch/work/ax/design214_ax252.json'))
for J in D['stp_legs']:
    add_items(journey_items_dense(J, 'ULPI_STP', hw=0.10))

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

for (px, py) in ((73.5, 16.0), (74.0, 15.75), (74.5, 15.5), (73.5, 15.0)):
    rows = []
    for it in pool[2]:
        if it[1] == 'PHY_1V8':
            continue
        g = df_pt(it, px, py) - max(0.2, it[3])
        if g < 0.7:
            rows.append((round(g, 3), it[1], it[0], it[2]))
    rows.sort()
    print(f'B G at ({px},{py}):', rows[:5], flush=True)

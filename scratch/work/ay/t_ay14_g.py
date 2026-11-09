import sys, json, math
sys.path.insert(0, 'scratch/work/ax')
src = open('scratch/work/ax/t_ax252_design214ae.py').read()
exec(src.split("\nbox = (64.0")[0])

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

for (px, py) in ((75.375, 19.625), (76.0, 19.5), (77.0, 19.3),
                 (78.0, 18.5), (80.875, 16.375)):
    rows = []
    for it in pool[1]:
        if it[1] == 'CDR_SQUELCH':
            continue
        g = df_pt(it, px, py) - max(0.2, it[3])
        if g < 0.6:
            rows.append((round(g, 3), it[1], it[0], it[2]))
    rows.sort()
    print(f'In2 G at ({px},{py}):', rows[:4], flush=True)

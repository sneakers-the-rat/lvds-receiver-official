import sys, json, math
sys.path.insert(0, 'scratch/work/ax')

# full t_ax252 prep pool (items 1-9 + PG/HV journeys in the pool)
src = open('scratch/work/ax/t_ax252_design214ae.py').read()
head = src.split("\nbox = (64.0")[0]
exec(head)

D = json.load(open('scratch/work/ax/design214_ax252.json'))
# add STP legs + F stub to the pool so fix gates see STP copper
for J in D['stp_legs']:
    add_items(journey_items_dense(J, 'ULPI_STP', hw=0.10))
add_items({0: [('seg', 'ULPI_STP', (76.25, 16.95, 76.05, 18.0, 0.1), 0.2),
               ('via', 'ULPI_STP', (76.065, 17.99, 0.25), 0.2)]})


def df_pt(it, x, y):
    kind, d = it[0], it[2]
    if kind == 'pad':
        cx, cy, hw, hh, rot = d
        dx, dy = x - cx, y - cy
        c, s = math.cos(-rot), math.sin(-rot)
        lx, ly = dx * c - dy * s, dx * s + dy * c
        return math.hypot(max(abs(lx) - hw, 0.0), max(abs(ly) - hh, 0.0))
    if kind == 'seg':
        x1, y1, x2, y2, hw = d
        px, py = x - x1, y - y1
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, (px * dx + py * dy) / L2))
        return math.hypot(px - t * dx, py - t * dy) - hw
    return math.hypot(x - d[0], y - d[1]) - d[2]


def G_pt(l, x, y, net):
    best, who = 9.9, None
    for it in pool[l]:
        if it[1] == net:
            continue
        v = df_pt(it, x, y) - max(0.2, it[3])
        if v < best:
            best, who = v, it
    return best, who


def pad_margin(cx, cy, hw, hh, net):
    """min edge clearance of a candidate F pad rect vs all F items."""
    best, who = 9.9, None
    for it in pool[0]:
        if it[1] == net:
            continue
        kind, d = it[0], it[2]
        if kind == 'pad':
            dx = max(abs(d[0] - cx) - (hw + d[2]), 0.0)
            dy = max(abs(d[1] - cy) - (hh + d[3]), 0.0)
            dist = math.hypot(dx, dy)
        elif kind == 'seg':
            # distance from rect to segment centreline (sampled finely
            # + endpoints/rect corners): use rect-excess on a fine
            # param sweep of the segment
            x1, y1, x2, y2, shw = d
            dist = 9.9
            for k in range(21):
                t = k / 20.0
                px, py = x1 + t * (x2 - x1), y1 + t * (y2 - y1)
                ex = max(abs(px - cx) - hw, 0.0)
                ey = max(abs(py - cy) - hh, 0.0)
                dist = min(dist, math.hypot(ex, ey) - shw)
        else:
            ex = max(abs(d[0] - cx) - hw, 0.0)
            ey = max(abs(d[1] - cy) - hh, 0.0)
            dist = math.hypot(ex, ey) - d[2]
        m = dist - max(0.2, it[3])
        if m < best:
            best, who = m, it
    return best, who


# ---------- (a) C20 at (76.2,18.73), dive via (76.065,17.96) ----------
print('=== (a) C20 shifted site ===', flush=True)
for (cx, cy, net) in ((75.72, 18.73, 'XI'), (76.68, 18.73, 'GND')):
    m, who = pad_margin(cx, cy, 0.28, 0.31, net)
    print(f'  pad {net} ({cx},{cy}): margin {m:+.3f} vs {L.fmt_it(who)}',
          flush=True)
for l in range(3):
    g, who = G_pt(l, 76.065, 17.96, 'ULPI_STP')
    print(f'  dive via (76.065,17.96) G[{l}] = {g:+.3f} vs {L.fmt_it(who)}',
          flush=True)
# XI via (75.625,18.625) inside new pad1 rect?
print('  XI via in pad1 rect:',
      abs(75.625 - 75.72) <= 0.28 and abs(18.625 - 18.73) <= 0.31, flush=True)
# GND via (77.25,18.375) disc vs new pad2 rect
dx = max(abs(77.25 - 76.68) - 0.28, 0.0)
dy = max(abs(18.375 - 18.73) - 0.31, 0.0)
print(f'  GND via-to-pad2 rect dist {math.hypot(dx, dy):.3f} (r 0.30)',
      flush=True)

# ---------- (c) PHY_1V8 south via scan ----------
print('=== (c) PHY via scan ===', flush=True)
best = None
for ix in range(21):
    for iy in range(21):
        x = 77.86 + 0.02 * ix
        y = 9.88 + 0.02 * iy
        worst = 9.9
        for l in (0, 2, 1):
            g, _ = G_pt(l, x, y, 'PHY_1V8')
            # via edge clearance = G - 0.25 (via radius demand on top
            # of the track gate G already nets out req; viafit uses
            # G >= 0.25 for a 0.25-radius via)
            worst = min(worst, g)
        if best is None or worst > best[0]:
            best = (worst, x, y)
print(f'  best viafit-style min-G {best[0]:+.3f} at ({best[1]:.2f},'
      f'{best[2]:.2f})', flush=True)
for (x, y) in ((77.98, 10.02), (best[1], best[2])):
    print(f'  candidate ({x},{y}):', flush=True)
    for l in range(3):
        g, who = G_pt(l, x, y, 'PHY_1V8')
        print(f'    G[{l}] = {g:+.3f} vs {L.fmt_it(who)}', flush=True)

# ---------- (b) C22 site scan ----------
print('=== (b) C22 site scan ===', flush=True)
# remove prep's C22 pads from the pool first
c22old = [it for it in pool[0] if it[0] == 'pad' and it[1] in ('PHY_1V8', 'GND')
          and abs(it[2][1] - 18.6) < 0.01 and it[2][0] in (79.12, 80.08)]
rip_items(c22old)
print('  ripped prep C22 pads:', len(c22old), flush=True)
cands = []
for ix in range(71):
    for iy in range(61):
        cx = 77.8 + 0.1 * ix
        cy = 15.5 + 0.1 * iy
        # U5 refdes parked at (79.0,18.85): keep C22 body clear
        if 77.9 <= cx <= 80.3 and 17.8 <= cy <= 19.9:
            continue
        for rot, (o1, o2) in ((0, ((-0.48, 0.0), (0.48, 0.0))),
                              (90, ((0.0, -0.48), (0.0, 0.48)))):
            m1, _ = pad_margin(cx + o1[0], cy + o1[1], 0.28, 0.31, 'PHY_1V8')
            m2, _ = pad_margin(cx + o2[0], cy + o2[1], 0.28, 0.31, 'GND')
            m = min(m1, m2)
            if m >= 0.03:
                cands.append((m, cx, cy, rot))
cands.sort(reverse=True)
print('  sites with both-pad margin >= +0.03:', len(cands), flush=True)
for c in cands[:12]:
    print('   ', c, flush=True)
# F-web A* for the top candidates: pad1 -> PHY via (78.1,17.5)
winner = None
for (m, cx, cy, rot) in cands[:8]:
    if rot == 0:
        p1 = (cx - 0.48, cy)
    else:
        p1 = (cx, cy - 0.48)
    astar = make_astar((76.0, 86.0, 13.0, 23.0), 0.05)
    J = astar('PHY_1V8', ((0,), p1[0], p1[1]), (0, 78.1, 17.5), hw=0.10)
    print(f'  web A* from ({p1[0]:.2f},{p1[1]:.2f}) [centre ({cx},{cy}) '
          f'rot {rot} margin {m:+.3f}]:', 'FOUND' if J else 'NONE',
          flush=True)
    if J and winner is None:
        winner = (cx, cy, rot, J)
out = {}
if winner:
    out['c22_site'] = winner[:3]
    out['c22_web'] = winner[3]
    print('  C22 WINNER:', winner[:3], flush=True)
json.dump(out, open('scratch/work/ax/design251fix.json', 'w'))
print('FIXDESIGN DONE', flush=True)

"""t_ax9: window-point candidates NE of the original (67.4,5.65).
For each candidate W: fresh exp241 pool + SCL via + In2 approach seg;
print via margins per layer, approach margin, then M1 (GND In2
staircase re-lay A* (66.375,6.125)->(67.375,4.125) hw0.125) verdict
and, if found, its gate vs the via."""
import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa


def chain_segs(pool, net, l, start, end):
    segs = [it for it in pool[l] if it[1] == net and it[0] == 'seg']
    bypt = {}
    for it in segs:
        d = it[2]
        bypt.setdefault((round(d[0], 3), round(d[1], 3)), []).append(it)
        bypt.setdefault((round(d[2], 3), round(d[3], 3)), []).append(it)
    out = []
    cur = (round(start[0], 3), round(start[1], 3))
    goal = (round(end[0], 3), round(end[1], 3))
    guard = 0
    while cur != goal and guard < 500:
        guard += 1
        cands = []
        for it in bypt.get(cur, []):
            if it in out:
                continue
            d = it[2]
            a = (round(d[0], 3), round(d[1], 3))
            b = (round(d[2], 3), round(d[3], 3))
            far = b if a == cur else a
            dist = (far[0] - goal[0]) ** 2 + (far[1] - goal[1]) ** 2
            cands.append((dist, it, far))
        if not cands:
            return None
        cands.sort(key=lambda t: t[0])
        _, nxt, far = cands[0]
        out.append(nxt)
        cur = far
    return out


for W in ((67.28, 5.8), (67.25, 5.8), (67.3, 5.85), (67.35, 5.8),
          (67.28, 5.9), (67.32, 5.75)):
    pool = load_board_pool()
    via = ('via', 'I2C_SCL', (W[0], W[1], 0.25), 0.2)
    seg = ('seg', 'I2C_SCL', (66.875, 6.75, W[0], W[1], 0.10), 0.2)
    ms = []
    for l in range(3):
        others = [o for o in pool[l] if o[1] != 'I2C_SCL']
        mm, binder = L.pt_margin(l, W[0], W[1], 'I2C_SCL', 0.25, others)
        ms.append((mm, binder))
    sm, sb = L.seg_margin(1, (66.875, 6.75), W, 'I2C_SCL', 0.10,
                          [o for o in pool[1] if o[1] != 'I2C_SCL'])
    print(f'W={W}: via margins ' +
          ' '.join(f'L{l} {m:+.3f}' for l, (m, b) in enumerate(ms)) +
          f' | approach {sm:+.3f}', flush=True)
    for l, (m, b) in enumerate(ms):
        if m < 0.06:
            print(f'    L{l} binder: {L.fmt_it(b)}', flush=True)
    add_items({0: [via], 1: [via], 2: [via], 1 + 0: []})
    pool[1].append(seg)
    rip = chain_segs(pool, 'GND', 1, (66.375, 6.125), (67.375, 4.125))
    if rip is None:
        print('    M1 chain walk FAILED', flush=True)
        continue
    n = rip_items(rip)
    assert n == len(rip)
    astar = make_astar((65.4, 68.2, 3.4, 7.0), 0.025)
    J = astar('GND', ((1,), 66.375, 6.125), (1, 67.375, 4.125), hw=0.125)
    print(f'    M1 A* (rip {len(rip)}): {"FOUND" if J else "NONE"}',
          flush=True)
    if J:
        its = journey_items_dense(J, 'GND', hw=0.125)
        worst = 9.9
        wb = None
        for l in range(3):
            for it in its[l]:
                for o in pool[l]:
                    if o[1] == 'GND':
                        continue
                    m = item_margin(l, it, [o])
                    if m < worst:
                        worst, wb = m, o
        print(f'    M1 gate worst {worst:+.3f} vs {L.fmt_it(wb)}',
              flush=True)

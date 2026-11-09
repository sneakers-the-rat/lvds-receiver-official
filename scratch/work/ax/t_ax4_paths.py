"""t_ax4: PATH S test.
1) F chains in the west-run box (61,70,10.5,14.5) and the south
   column / east-return box (61.5,66.5,-4.5,13).
2) ML A* with box extended south (60,72,-5,14.5): frag0 via ->
   pocket via on F; also -> fanout points."""
import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
from collections import defaultdict

pool = load_board_pool()


def chains(net, l, box):
    segs = [it for it in pool[l] if it[1] == net and it[0] == 'seg']
    bypt = defaultdict(list)
    for i, it in enumerate(segs):
        d = it[2]
        bypt[(round(d[0], 3), round(d[1], 3))].append(i)
        bypt[(round(d[2], 3), round(d[3], 3))].append(i)
    used = set()
    out = []
    for i, it in enumerate(segs):
        if i in used:
            continue
        used.add(i)
        d = it[2]
        chain = [(d[0], d[1]), (d[2], d[3])]
        for end in (0, -1):
            while True:
                p = chain[end]
                nxt = None
                for j in bypt.get((round(p[0], 3), round(p[1], 3)), []):
                    if j not in used:
                        nxt = j
                        break
                if nxt is None:
                    break
                used.add(nxt)
                dd = segs[nxt][2]
                a, b = (dd[0], dd[1]), (dd[2], dd[3])
                far = b if (round(a[0], 3), round(a[1], 3)) == \
                    (round(p[0], 3), round(p[1], 3)) else a
                if end == 0:
                    chain.insert(0, far)
                else:
                    chain.append(far)
        if any(box[0] < x < box[1] and box[2] < y < box[3]
               for (x, y) in chain):
            out.append((d[4], chain))
    return out


def simplify(chain, tol=0.02):
    if len(chain) <= 2:
        return chain
    out = [chain[0]]
    for a, b, c in zip(chain, chain[1:], chain[2:]):
        v1 = (b[0] - a[0], b[1] - a[1])
        v2 = (c[0] - b[0], c[1] - b[1])
        if abs(v1[0] * v2[1] - v1[1] * v2[0]) > tol:
            out.append(b)
    out.append(chain[-1])
    return out


nets = set()
for l in range(3):
    for it in pool[l]:
        nets.add(it[1])
for box, tag in (((61, 70, 10.5, 14.5), 'WEST-RUN'),
                 ((61.5, 66.5, -4.5, 13), 'SOUTH-COL')):
    print(f'=== F chains in {tag} {box} ===', flush=True)
    for net in sorted(nets):
        for hw, ch in chains(net, 0, box):
            pts = simplify(ch)
            s = '->'.join(f'({x:.2f},{y:.2f})' for (x, y) in pts)
            print(f'  {net} hw{hw:.3f} n={len(ch)}: {s}', flush=True)
    print(f'--- F pads/vias in {tag} ---', flush=True)
    seen = set()
    for it in pool[0]:
        if it[0] in ('pad', 'via'):
            cx, cy = C(it)
            if box[0] < cx < box[1] and box[2] < cy < box[3]:
                k = (it[0], it[1], round(cx, 3), round(cy, 3))
                if k not in seen:
                    seen.add(k)
                    print(f'  {L.fmt_it(it)}', flush=True)

print('=== A* extended box (60,72,-5,14.5) ===', flush=True)
astar = make_astar((60.0, 72.0, -5.0, 14.5), 0.025)
for goal in ((0, 69.35, 1.4), (0, 66.5, 1.63), (0, 66.15, 2.1)):
    J = astar('I2C_SCL', ((0, 1, 2), 69.625, 12.625), goal, hw=0.10)
    print(f'A* frag0via -> L{goal[0]} ({goal[1]},{goal[2]}): '
          f'{"FOUND" if J else "NONE"}', flush=True)
    if J:
        print('  vias:', J['vias'], flush=True)
        for r in J['runs']:
            print(f"  L{r['layer']} n={len(r['pts'])} "
                  f"{r['pts'][0]} .. {r['pts'][-1]}", flush=True)
        import json
        json.dump(J, open('scratch/work/ax/pathS_astar.json', 'w'))
        break

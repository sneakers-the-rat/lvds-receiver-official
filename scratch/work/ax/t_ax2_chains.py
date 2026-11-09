"""t_ax2: coalesced chain survey of exp241 in the SCL corridor.
Reconstructs polylines per net/layer from micro-segs; prints chains
intersecting the box, all vias in the box, and U9/U14/R20 pads."""
import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
from collections import defaultdict

pool = load_board_pool()
BOX = (63.5, 71.0, -1.0, 9.0)


def inbox(x, y, pad=0.0):
    return BOX[0] - pad < x < BOX[1] + pad and BOX[2] - pad < y < BOX[3] + pad


def chains(net, l):
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
        hw = d[4]
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
        out.append((hw, chain))
    return out


def simplify(chain, tol=0.01):
    if len(chain) <= 2:
        return chain
    out = [chain[0]]
    for a, b, c in zip(chain, chain[1:], chain[2:]):
        v1 = (b[0] - a[0], b[1] - a[1])
        v2 = (c[0] - b[0], c[1] - b[1])
        cross = v1[0] * v2[1] - v1[1] * v2[0]
        if abs(cross) > tol:
            out.append(b)
    out.append(chain[-1])
    return out


for net in ('I2C_SCL', 'GND', 'CDR_LOL', 'CAP_CLK', 'CAP_DATA', 'I2C_SDA',
            '+3V3A', 'TMP_ALERT', 'HV_SHDN', 'PG_3V3'):
    for l in range(3):
        for hw, ch in chains(net, l):
            if any(inbox(x, y, 1.0) for (x, y) in ch):
                pts = simplify(ch)
                s = '->'.join(f'({x:.2f},{y:.2f})' for (x, y) in pts)
                print(f'{net} L{l} hw{hw:.3f} n={len(ch)}: {s}', flush=True)

print('--- vias in box ---', flush=True)
seen = set()
for l in range(3):
    for it in pool[l]:
        if it[0] == 'via' and inbox(it[2][0], it[2][1]):
            k = (it[1], round(it[2][0], 3), round(it[2][1], 3))
            if k not in seen:
                seen.add(k)
                print(f'  via {it[1]} ({it[2][0]:.3f},{it[2][1]:.3f}) '
                      f'r{it[2][2]:.3f}', flush=True)

print('--- pads in box ---', flush=True)
for it in pool[0]:
    if it[0] == 'pad' and inbox(it[2][0], it[2][1]):
        print(f'  pad {it[1]} ({it[2][0]:.3f},{it[2][1]:.3f}) '
              f'hw{it[2][2]:.3f}x{it[2][3]:.3f} rot{it[2][4]:.2f}', flush=True)

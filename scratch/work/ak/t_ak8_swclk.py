"""t_ak8: SWCLK joint optimizer -- DAC_SYNC via relocation D (d0.6)
+ SWCLK dive S (d0.5), exact item model on exp221.
Rips: DAC via (90.125,-17.875), its F stub seg from (90.25,-17.163)
and B seg to (90.125,-16.125). Gates: D and S on 3 layers vs each
other + statics; DAC F stub (90.25,-17.163)->D; DAC B seg
D->(90.125,-16.125); SWCLK F stub (90.75,-17.20)->S; SWCLK journey
flood from S on B (then In2) to J4.4 centre (92.52,-23.52).
Usage: t_ak8_swclk.py board"""
import collections, math, sys
sys.path.insert(0, 'hw')
sys.path.insert(0, 'scratch/work/ai')
import wx
_app = wx.App(False)
import pcbnew
from t_ai_lib import load_items, pt_margin, seg_margin, in_box_pool

board = pcbnew.LoadBoard(sys.argv[1])
items = load_items(board)


def is_seg(it, net, a, b):
    if it[0] != 'seg' or it[1] != net:
        return False
    d = it[2]
    return (abs(d[0] - a[0]) < 0.01 and abs(d[1] - a[1]) < 0.01 and
            abs(d[2] - b[0]) < 0.01 and abs(d[3] - b[1]) < 0.01) or \
           (abs(d[0] - b[0]) < 0.01 and abs(d[1] - b[1]) < 0.01 and
            abs(d[2] - a[0]) < 0.01 and abs(d[3] - a[1]) < 0.01)


statics = {0: [], 1: [], 2: []}
nrip = 0
for li in range(3):
    for it in items[li]:
        drop = False
        if it[0] == 'via' and it[1] == 'DAC_SYNC' and \
                abs(it[2][0] - 90.125) < 0.01 and \
                abs(it[2][1] + 17.875) < 0.01:
            drop = True
        if is_seg(it, 'DAC_SYNC', (90.25, -17.163), (90.125, -17.875)):
            drop = True
        if is_seg(it, 'DAC_SYNC', (90.125, -17.875), (90.125, -16.125)):
            drop = True
        if drop:
            nrip += 1
        else:
            statics[li].append(it)
print(f'ripped {nrip}')

WIN = (88.0, 93.0, -20.0, -15.5)
pools = {li: in_box_pool(statics, WIN, pad=1.2)[li] for li in range(3)}
FBOX = (88.5, 94.5, -25.5, -16.0)
fpools = {li: in_box_pool(statics, FBOX, pad=1.2)[li] for li in range(3)}


def flood(li, net, hw, S, T, extra_vias):
    pool = fpools[li] + [('via', n, (p[0], p[1], r), 0.2)
                         for (n, p, r) in extra_vias]
    X0, X1, Y0, Y1 = FBOX
    STEP = 0.0625
    passable = set()
    NX = int(round((X1 - X0) / STEP)) + 1
    NY = int(round((Y1 - Y0) / STEP)) + 1
    for ix in range(NX):
        for iy in range(NY):
            x, y = X0 + ix * STEP, Y0 + iy * STEP
            m, _ = pt_margin(li, x, y, net, hw, pool)
            if m >= 0:
                passable.add((ix, iy))
    si = (int(round((S[0] - X0) / STEP)), int(round((S[1] - Y0) / STEP)))
    passable.add(si)
    seen = {si}
    dq = collections.deque([si])
    while dq:
        c = dq.popleft()
        cx, cy = X0 + c[0] * STEP, Y0 + c[1] * STEP
        if math.hypot(cx - T[0], cy - T[1]) <= hw + 0.08:
            return True
        for ddx in (-1, 0, 1):
            for ddy in (-1, 0, 1):
                n = (c[0] + ddx, c[1] + ddy)
                if n in passable and n not in seen:
                    seen.add(n)
                    dq.append(n)
    return False


sols = []
Ds = []
gx = 89.55
while gx <= 90.15:
    gy = -18.65
    while gy <= -17.55:
        D = (round(gx, 4), round(gy, 4))
        ok = True
        dm = 9
        for li in range(3):
            m, _ = pt_margin(li, D[0], D[1], 'DAC_SYNC', 0.30, pools[li])
            dm = min(dm, m)
            if m < 0:
                ok = False
        if ok:
            m1, _ = seg_margin(0, (90.25, -17.163), D, 'DAC_SYNC', 0.1,
                               pools[0])
            m2, _ = seg_margin(2, D, (90.125, -16.125), 'DAC_SYNC', 0.1,
                               pools[2])
            if m1 >= 0 and m2 >= 0:
                Ds.append((min(dm, m1, m2), D))
        gy += 0.03125
    gx += 0.03125
print(f'feasible DAC positions: {len(Ds)}')
for dm, D in sorted(Ds, reverse=True)[:6]:
    print(f'   D={D} margin {dm:+.3f}')

best = []
for dm, D in Ds:
    gx = 90.25
    while gx <= 90.95:
        gy = -18.45
        while gy <= -17.45:
            S = (round(gx, 4), round(gy, 4))
            if math.hypot(S[0] - D[0], S[1] - D[1]) < 0.75:
                gy += 0.03125
                continue
            ok = True
            sm = 9
            poolsD = {li: pools[li] + [('via', 'DAC_SYNC',
                                        (D[0], D[1], 0.30), 0.2)]
                      for li in range(3)}
            for li in range(3):
                m, _ = pt_margin(li, S[0], S[1], 'SWCLK', 0.25,
                                 poolsD[li])
                sm = min(sm, m)
                if m < 0:
                    ok = False
            if ok:
                m1, _ = seg_margin(0, (90.75, -17.20), S, 'SWCLK', 0.1,
                                   poolsD[0])
                if m1 >= 0:
                    best.append((min(sm, m1), D, S))
            gy += 0.03125
        gx += 0.03125
print(f'(D,S) pairs passing via+stub gates: {len(best)}')
best.sort(reverse=True)
landed = 0
for m, D, S in best[:14]:
    okB = flood(2, 'SWCLK', 0.1, S, (92.52, -23.52),
                [('DAC_SYNC', D, 0.30), ('SWCLK', S, 0.25)])
    okI = False
    if not okB:
        okI = flood(1, 'SWCLK', 0.1, S, (92.52, -23.52),
                    [('DAC_SYNC', D, 0.30), ('SWCLK', S, 0.25)])
    print(f'  D={D} S={S} minmargin {m:+.3f} floodB={okB} floodIn2={okI}')
    if okB or okI:
        landed += 1
print(f'pairs with a flooded journey: {landed}')

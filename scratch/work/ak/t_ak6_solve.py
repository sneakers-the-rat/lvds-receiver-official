"""t_ak6: PHY_1V8A option (d) -- SE-lobe re-solve.
Model = exp221 items + t_aj7's proven PHY_1V8A design (stub, notch
via, B journey, SCL via move, +3V3D via shrink) + XO tail ripped.
Variables: +3V3A S1 In2 joint cluster shift west by s; PHY_1V8
B-return corner D=(76.8,10.988) shift (de,dn); PHY via P micro-shift.
Scan XO dive X over the SE lobe; gate X (3 layers), XO's F stub,
XO's B flood to (74.125,12.25). Stage 1 gates vs local fences only;
stage 2 full re-gate incl. moved statics. Usage: t_ak6_solve.py"""
import collections, math, sys
sys.path.insert(0, 'hw')
sys.path.insert(0, 'scratch/work/ai')
import wx
_app = wx.App(False)
import pcbnew
from t_ai_lib import (load_items, pt_margin, seg_margin,
                      in_box_pool, fmt_it)

SRC = 'hw/pdlvds_rx.exp221.kicad_pcb'
items = load_items(pcbnew.LoadBoard(SRC))


def is_seg(it, net, a, b):
    if it[0] != 'seg' or it[1] != net:
        return False
    d = it[2]
    return (abs(d[0] - a[0]) < 0.01 and abs(d[1] - a[1]) < 0.01 and
            abs(d[2] - b[0]) < 0.01 and abs(d[3] - b[1]) < 0.01) or \
           (abs(d[0] - b[0]) < 0.01 and abs(d[1] - b[1]) < 0.01 and
            abs(d[2] - a[0]) < 0.01 and abs(d[3] - a[1]) < 0.01)


def is_via(it, net, p):
    return it[0] == 'via' and it[1] == net and \
        abs(it[2][0] - p[0]) < 0.01 and abs(it[2][1] - p[1]) < 0.01


RIP_EXACT = [
    ('seg', 'XO', (76.75, 11.125), (76.5, 10.75)),
    ('seg', 'XO', (76.5, 10.75), (76.0, 10.625)),
    ('seg', 'XO', (76.0, 10.625), (74.125, 12.25)),
    ('via', 'XO', (76.0, 10.625)),
    ('via', '+3V3D', (70.875, 12.625)),
    ('via', 'I2C_SCL', (69.625, 12.625)),
    ('seg', 'I2C_SCL', (69.625, 12.625), (69.675, 12.75)),
]
# SCL segs touching the old via point (either endpoint) also rip:
SCL_OLD = (69.625, 12.625)


def build_statics():
    out = {0: [], 1: [], 2: []}
    n = 0
    for li in range(3):
        for it in items[li]:
            drop = False
            for spec in RIP_EXACT:
                if spec[0] == 'seg' and is_seg(it, spec[1], spec[2],
                                               spec[3]):
                    drop = True
                if spec[0] == 'via' and is_via(it, spec[1], spec[2]):
                    drop = True
            if it[0] == 'seg' and it[1] == 'I2C_SCL':
                d = it[2]
                if (abs(d[0] - SCL_OLD[0]) < 0.01 and
                        abs(d[1] - SCL_OLD[1]) < 0.01) or \
                   (abs(d[2] - SCL_OLD[0]) < 0.01 and
                        abs(d[3] - SCL_OLD[1]) < 0.01):
                    drop = True
            if drop:
                n += 1
            else:
                out[li].append(it)
    print(f'ripped {n} entries')
    return out


VP2 = (75.7375, 10.75)
GOALV = (69.9375, 15.375)


def phy_adds():
    adds = []
    def seg(net, li, a, b, hw=0.1):
        adds.append(('seg', net, (a[0], a[1], b[0], b[1], hw), li))
    def via(net, p, r=0.25):
        adds.append(('via', net, (p[0], p[1], r), None))
    seg('PHY_1V8A', 0, (75.75, 11.562), (75.72, 11.0))
    seg('PHY_1V8A', 0, (75.72, 11.0), VP2)
    via('PHY_1V8A', VP2)
    BPTS = [VP2, (75.3, 11.35), (74.9, 11.75), (74.2, 12.25),
            (73.5, 12.55), (73.3, 12.2), (73.22, 11.94),
            (72.92, 11.62), (72.35, 11.65), (71.9, 11.95),
            (71.3, 12.1), (70.7, 11.85), (70.3, 12.15), (70.2, 12.5),
            (70.18, 12.75), (70.1, 13.3), (70.0, 14.3), GOALV]
    for a, b in zip(BPTS, BPTS[1:]):
        seg('PHY_1V8A', 2, a, b)
    via('PHY_1V8A', GOALV)
    via('+3V3D', (70.875, 12.625))
    via('I2C_SCL', (69.5, 12.75), 0.3)
    seg('I2C_SCL', 0, (69.675, 12.75), (69.5, 12.75))
    seg('I2C_SCL', 1, (69.5, 12.75), (67.0, 12.7))
    seg('I2C_SCL', 1, (67.0, 12.7), (65.0, 12.5))
    return adds


S1_PTS = [(76.625, 10.25), (76.625, 10.5), (76.25, 9.875)]
D_PT = (76.8, 10.988)
P_PT = (77.8688, 10.0563)


def shift_pt(p, pts, d):
    for q in pts:
        if abs(p[0] - q[0]) < 0.01 and abs(p[1] - q[1]) < 0.01:
            return (p[0] + d[0], p[1] + d[1])
    return p


def apply_vars(statics, s, de, dn, pp):
    """Return modified copy: S1 cluster west by s; PHY return corner
    D by (de,dn); PHY via P by pp (its 3 segs follow)."""
    out = {0: [], 1: [], 2: []}
    for li in range(3):
        for it in statics[li]:
            k, n, d, c = it
            if k == 'seg':
                a, b = (d[0], d[1]), (d[2], d[3])
                if n == '+3V3A' and li == 1:
                    a = shift_pt(a, S1_PTS, (-s, 0))
                    b = shift_pt(b, S1_PTS, (-s, 0))
                if n == 'PHY_1V8' and li == 2:
                    a = shift_pt(a, [D_PT], (de, dn))
                    b = shift_pt(b, [D_PT], (de, dn))
                    a = shift_pt(a, [P_PT], pp)
                    b = shift_pt(b, [P_PT], pp)
                if n == 'PHY_1V8' and li == 0:
                    a = shift_pt(a, [P_PT], pp)
                    b = shift_pt(b, [P_PT], pp)
                d = (a[0], a[1], b[0], b[1], d[4])
            elif k == 'via' and n == 'PHY_1V8':
                if abs(d[0] - P_PT[0]) < 0.01 and \
                        abs(d[1] - P_PT[1]) < 0.01:
                    d = (d[0] + pp[0], d[1] + pp[1], d[2])
            out[li].append((k, n, d, c))
    return out


def flood(pool, net, hw, S, T, box):
    X0, X1, Y0, Y1 = box
    STEP = 0.0625
    NX = int(round((X1 - X0) / STEP)) + 1
    NY = int(round((Y1 - Y0) / STEP)) + 1
    passable = set()
    for ix in range(NX):
        for iy in range(NY):
            x, y = X0 + ix * STEP, Y0 + iy * STEP
            m, _ = pt_margin(2, x, y, net, hw, pool)
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


statics = build_statics()
ADDS = phy_adds()
add_by_layer = {0: [], 1: [], 2: []}
for (k, n, d, li) in ADDS:
    if k == 'via':
        for l2 in range(3):
            add_by_layer[l2].append((k, n, d, 0.2))
    else:
        add_by_layer[li].append((k, n, d, 0.2))

BOXL = (74.0, 79.0, 8.0, 12.6)
sols = []
for s in (0, 0.125, 0.25, 0.375, 0.5):
    for de in (0, 0.125, 0.25):
        for dn in (0, -0.125):
            for pp in ((0, 0), (-0.0625, 0), (0, -0.0625)):
                mod = apply_vars(statics, s, de, dn, pp)
                pools = {li: in_box_pool(mod, BOXL, pad=1.2)[li]
                         + add_by_layer[li] for li in range(3)}
                gx = 76.15
                while gx <= 77.05:
                    gy = 10.30
                    while gy <= 11.05:
                        X = (round(gx, 4), round(gy, 4))
                        ok = True
                        for li in range(3):
                            m, _ = pt_margin(li, X[0], X[1], 'XO',
                                             0.25, pools[li])
                            if m < 0:
                                ok = False
                                break
                        if ok:
                            m1, _ = seg_margin(
                                0, (76.75, 11.30), X, 'XO', 0.1,
                                pools[0])
                            if m1 >= 0:
                                sols.append((s, de, dn, pp, X))
                                print(f'STAGE1 s={s} de={de} dn={dn} '
                                      f'pp={pp} X={X}')
                        gy += 0.0625
                    gx += 0.0625
print(f'stage1 survivors: {len(sols)}')

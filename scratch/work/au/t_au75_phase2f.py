"""t_au75: phase 2f - correct order.
Assembly WITHOUT either arrival run2; conflict rips; arrival
re-plans as a search over orders/layer modes with rollback;
detours (fixed detour2); fanout + heal2; full gate; fragments
with copper-touch union. Saves build_au75.json (+ stage1)."""
import wx
_app = wx.App(False)
import sys, json, math
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'p2f'}
src71 = open('scratch/work/au/t_au71_phase2b.py').read()
exec(src71.split("add_new('data_tail'")[0], g)
pool = g['pool']
NEW = g['NEW']
JOURNEYS = g['JOURNEYS']
add_new = g['add_new']
C = g['C']
J67 = json.load(open('scratch/work/au/heals_au67.json'))
J30 = json.load(open('scratch/work/as/journey30_CAP_DATA_DC.json'))
TAIL = J67['data_tail']
truns = [r for r in TAIL['runs']
         if not (r['layer'] == 1 and tuple(r['pts'][0]) == (64.7, 15.45))]
assert len(truns) == len(TAIL['runs']) - 1, 'data run2 not dropped'
add_new('data_tail', dict(vias=TAIL['vias'], runs=truns), 'CAP_DATA',
        0.10)
J9 = json.load(open('scratch/work/au/journey_au9_CLK.json'))
runs = []
for run in J9['runs']:
    pts = [tuple(p) for p in run['pts']]
    if run['layer'] == 1 and len(pts) == 2:
        continue
    if run['layer'] == 1 and pts[0] == (64.75, 16.95):
        continue
    if run['layer'] == 2 and pts[0] == (70.0, 1.8):
        i = pts.index((69.55, 2.7))
        runs.append(dict(layer=2, pts=[list(p) for p in pts[i:]]))
    else:
        runs.append(run)
add_new('clk9', dict(vias=J9['vias'], runs=runs), 'CAP_CLK', 0.10)
exec(src71[src71.index("def item_margin"):src71.index("def fragments")],
     g)
item_margin = g['item_margin']
make_astar = g['make_astar']
RIP2 = g['RIP2']
frag_src = src71[src71.index("def fragments"):src71.index("def detour")]
exec(frag_src.replace("< 0.02", "< 0.04"), g)
fragments = g['fragments']
print('assembly + rips done', flush=True)


def snap():
    return ({l: len(NEW[l]) for l in range(3)},
            {l: len(pool[l]) for l in range(3)}, set(JOURNEYS))


def restore(s):
    nl, pl, jk = s
    for l in range(3):
        del NEW[l][nl[l]:]
        del pool[l][pl[l]:]
    for k in list(JOURNEYS):
        if k not in jk:
            del JOURNEYS[k]


astarA = make_astar((60.0, 78.0, 10.0, 28.0), 0.025)
LOCK = {'in2': (False, True, False), 'B': (False, False, True),
        'multi': None}
SPEC = {'DATA': ('CAP_DATA', (64.7, 15.45), (1, 72.6, 19.3)),
        'CLK': ('CAP_CLK', (64.75, 16.95), (1, 70.1, 21.8))}
ORDERS = [('DATA', 'in2', 'CLK', 'in2'), ('CLK', 'in2', 'DATA', 'in2'),
          ('DATA', 'multi', 'CLK', 'in2'), ('CLK', 'multi', 'DATA', 'in2'),
          ('DATA', 'B', 'CLK', 'in2'), ('CLK', 'B', 'DATA', 'in2'),
          ('DATA', 'in2', 'CLK', 'multi'), ('CLK', 'in2', 'DATA', 'multi')]
solved = None
for (n1, m1, n2, m2) in ORDERS:
    s = snap()
    ok = True
    for (nm, md) in ((n1, m1), (n2, m2)):
        net, (sx, sy), (gl, gx, gy) = SPEC[nm]
        starts = (gl,) if md != 'multi' else (0, 1, 2)
        J = astarA(net, (starts, sx, sy), (gl, gx, gy), hw=0.10,
                   layer_lock=LOCK[md])
        print(f'arrival {nm} ({md}):', 'FOUND' if J else 'NONE',
              flush=True)
        if J is None:
            ok = False
            break
        add_new(f'arr_{nm.lower()}', J, net, 0.10)
    if ok:
        solved = (n1, m1, n2, m2)
        break
    restore(s)
print('arrivals:', solved, flush=True)
json.dump(dict(
    journeys=JOURNEYS,
    fixed={str(l): [[it[0], it[1], list(it[2]), it[3]]
                     for it in g['FIXED'][l]] for l in range(3)},
    rip2={net: [[it[0], it[1], list(it[2]), it[3]] for it in lst]
          for net, lst in RIP2.items()},
    arrivals=solved, clk_via=(70.2, 1.8), exit_via=(69.075, 2.8),
    u9_shift=1.25), open('scratch/work/au/build_au75_stage1.json', 'w'))
print('saved stage1', flush=True)
if not solved:
    print('ARRIVALS UNSOLVED - stopping before detours', flush=True)
    sys.exit(0)


def detour2(net, box, hw, layer_lock=None, step=0.05):
    astar = make_astar(box, step)
    bx0, bx1, by0, by1 = box
    n = 0
    while True:
        fr = fragments(net, box)
        if len(fr) <= 1:
            print(f'  {net}: connected', flush=True)
            return True
        pairs = []
        for i in range(len(fr)):
            for j in range(i + 1, len(fr)):
                for (l1, p1) in fr[i]['terms']:
                    for (l2, p2) in fr[j]['terms']:
                        if not (bx0 + 0.1 < p1[0] < bx1 - 0.1
                                and by0 + 0.1 < p1[1] < by1 - 0.1
                                and bx0 + 0.1 < p2[0] < bx1 - 0.1
                                and by0 + 0.1 < p2[1] < by1 - 0.1):
                            continue
                        pairs.append((math.hypot(p1[0] - p2[0],
                                                  p1[1] - p2[1]),
                                      (l1, p1), (l2, p2)))
        pairs.sort()
        done = False
        for (_, (l1, p1), (l2, p2)) in pairs[:14]:
            starts = (l1,) if layer_lock else (0, 1, 2)
            J = astar(net, (starts, p1[0], p1[1]), (l2, p2[0], p2[1]),
                      hw=hw, layer_lock=layer_lock)
            if J is not None:
                J['runs'][0]['pts'][0] = [p1[0], p1[1]]
                J['runs'][-1]['pts'][-1] = [p2[0], p2[1]]
                n += 1
                add_new(f'detour_{net}_{n}', J, net, hw)
                print(f'  {net}: detour {n} {p1} -> {p2} '
                      f'vias={J["vias"]}', flush=True)
                done = True
                break
        if not done:
            print(f'  {net}: NO detour for {len(fr)} fragments',
                  flush=True)
            return False
        if n > 12:
            return False


print('PG detours:', flush=True)
detour2('PG_3V3', (54.0, 74.0, -18.0, 18.0), 0.125)
print('+3V3D detours:', flush=True)
detour2('+3V3D', (66.0, 78.0, 16.0, 28.0), 0.15)
print('XO detours:', flush=True)
detour2('XO', (64.0, 78.0, 8.0, 24.0), 0.10,
        layer_lock=(False, True, False), step=0.025)
astarF = make_astar((66.0, 72.5, -0.5, 6.0), 0.025)
for goal in ((0, 66.025, 2.1), (0, 66.45, 2.1), (0, 66.3, 2.05)):
    J = astarF('I2C_SCL', ((0, 1, 2), 69.35, 1.40), goal, hw=0.10)
    print(f'SCL fanout goal {goal}:', 'FOUND' if J else 'NONE',
          flush=True)
    if J:
        add_new('scl_ffan', J, 'I2C_SCL', 0.10)
        break
J = astarF('+3V3A', ((0, 1, 2), 71.375, 0.875), (0, 69.125, 4.375),
           hw=0.10)
print('heal2 final:', 'FOUND' if J else 'NONE', flush=True)
if J:
    add_new('v3a_heal2', J, '+3V3A', 0.10)
bad = 0
for l in range(3):
    for nit in NEW[l]:
        m = item_margin(l, nit, pool[l])
        if m < -0.001:
            bad += 1
            if bad <= 15:
                print(f'GATE FAIL L{l} {m:+.3f}', flush=True)
print(f'full gate: {bad} failures', flush=True)


def pt_seg(px, py, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy)
                     / max(1e-9, vx * vx + vy * vy)))
    return math.hypot(px - (ax + t * vx), py - (ay + t * vy))


def gap(l, a, b):
    """copper gap between same-net items a,b on layer l (pad only L0)"""
    ka, kb = a[0], b[0]
    if ka == 'pad' or kb == 'pad':
        if ka != 'pad':
            a, b = b, a
            ka, kb = kb, ka
        d = a[2]
        x0, x1 = d[0] - d[2] / 2, d[0] + d[2] / 2
        y0, y1 = d[1] - d[3] / 2, d[1] + d[3] / 2
        if kb == 'via':
            cx = min(max(b[2][0], x0), x1)
            cy = min(max(b[2][1], y0), y1)
            return math.hypot(b[2][0] - cx, b[2][1] - cy) - b[2][2]
        if kb == 'seg':
            e = b[2]
            if x0 <= e[0] <= x1 and y0 <= e[1] <= y1:
                return -1
            if x0 <= e[2] <= x1 and y0 <= e[3] <= y1:
                return -1
            return min(pt_seg(e[0], e[1], x0, y0, x1, y0),
                       pt_seg(e[0], e[1], x0, y1, x1, y1),
                       pt_seg(e[0], e[1], x0, y0, x0, y1),
                       pt_seg(e[0], e[1], x1, y0, x1, y1)) - e[4]
        return 9.9
    if ka == 'via' and kb == 'via':
        return math.hypot(a[2][0] - b[2][0], a[2][1] - b[2][1]) \
            - a[2][2] - b[2][2]
    if ka == 'via' and kb == 'seg':
        e = b[2]
        return pt_seg(a[2][0], a[2][1], e[0], e[1], e[2], e[3]) \
            - a[2][2] - e[4]
    if ka == 'seg' and kb == 'via':
        return gap(l, b, a)
    if ka == 'seg' and kb == 'seg':
        d1, d2 = a[2], b[2]
        dd = min(pt_seg(d1[0], d1[1], d2[0], d2[1], d2[2], d2[3]),
                 pt_seg(d1[2], d1[3], d2[0], d2[1], d2[2], d2[3]),
                 pt_seg(d2[0], d2[1], d1[0], d1[1], d1[2], d1[3]),
                 pt_seg(d2[2], d2[3], d1[0], d1[1], d1[2], d1[3]))
        def orient(p, q, r):
            return (q[0] - p[0]) * (r[1] - p[1]) \
                - (q[1] - p[1]) * (r[0] - p[0])
        p1, p2 = (d1[0], d1[1]), (d1[2], d1[3])
        p3, p4 = (d2[0], d2[1]), (d2[2], d2[3])
        if orient(p1, p2, p3) * orient(p1, p2, p4) < 0 and \
                orient(p3, p4, p1) * orient(p3, p4, p2) < 0:
            dd = 0.0
        return dd - d1[4] - d2[4]
    return 9.9


def fragments2(net, box):
    bx0, bx1, by0, by1 = box
    items = []
    for l in range(3):
        for it in pool[l]:
            if it[1] != net:
                continue
            cx, cy = C(it)
            if bx0 - 3 < cx < bx1 + 3 and by0 - 3 < cy < by1 + 3:
                items.append((l, it))
    par = list(range(len(items)))

    def find(a):
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            li, a = items[i]
            lj, b = items[j]
            if li == lj and gap(li, a, b) <= 0.02:
                ri, rj = find(i), find(j)
                if ri != rj:
                    par[ri] = rj
            elif a[0] == 'via' and b[0] == 'via':
                ri, rj = find(i), find(j)
                if ri != rj:
                    par[ri] = rj
    groups = {}
    for i in range(len(items)):
        groups.setdefault(find(i), []).append(items[i])
    return list(groups.values())


import t_ai_lib as L
for net, box in (('CAP_CLK', (55.0, 80.0, -2.0, 30.0)),
                 ('CAP_DATA', (55.0, 80.0, -2.0, 30.0)),
                 ('I2C_SCL', (60.0, 80.0, -2.0, 16.0)),
                 ('I2C_SDA', (60.0, 80.0, -2.0, 16.0)),
                 ('+3V3A', (60.0, 80.0, -2.0, 16.0)),
                 ('TMP_ALERT', (60.0, 72.0, -6.0, 8.0))):
    gr = fragments2(net, box)
    sizes = sorted((len(x) for x in gr), reverse=True)
    print(f'fragments2 {net}: {len(gr)} sizes {sizes[:6]}', flush=True)
    for x in gr:
        if len(x) <= 4:
            print('  small:', [L.fmt_it(it) for (_, it) in x],
                  flush=True)
json.dump(dict(
    journeys=JOURNEYS,
    fixed={str(l): [[it[0], it[1], list(it[2]), it[3]]
                     for it in g['FIXED'][l]] for l in range(3)},
    rip2={net: [[it[0], it[1], list(it[2]), it[3]] for it in lst]
          for net, lst in RIP2.items()},
    arrivals=solved, clk_via=(70.2, 1.8), exit_via=(69.075, 2.8),
    u9_shift=1.25), open('scratch/work/au/build_au75.json', 'w'))
print('saved build_au75.json', flush=True)
print('done', flush=True)

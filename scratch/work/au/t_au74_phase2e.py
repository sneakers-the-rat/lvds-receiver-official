"""t_au74: phase 2e.
- CLK arrival run2 re-planned with DATA tail (original) as fence
  (In2-only, then multi-layer).
- detour2 fixed: union tol 0.04, endpoint snapping, in-box pairs.
Saves build_au74.json."""
import wx
_app = wx.App(False)
import sys, json, math
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'p2e'}
src73 = open('scratch/work/au/t_au73_phase2d.py').read()
base = src73.split("J = astarNE('CAP_DATA'")[0]
exec(base, g)
pool = g['pool']
journey_items_dense = g['journey_items_dense']
add_new = g['add_new']
make_astar = g['make_astar']
NEW = g['NEW']
C = g['C']
item_margin = g['item_margin']
import t_ai_lib as L

# DATA tail full original
J30 = json.load(open('scratch/work/as/journey30_CAP_DATA_DC.json'))
pts0 = J30['runs'][0]['pts']
TAIL = dict(vias=J30['vias'],
            runs=[dict(layer=1, pts=pts0[213:])] + J30['runs'][1:])
add_new('data_tail', TAIL, 'CAP_DATA', 0.10)
# CLK9 minus run2 (the In2 arrival (64.75,16.95)->(70.1,21.8))
J9 = json.load(open('scratch/work/au/journey_au9_CLK.json'))
runs = []
for run in J9['runs']:
    pts = [tuple(p) for p in run['pts']]
    if run['layer'] == 1 and len(pts) == 2:
        continue
    if run['layer'] == 2 and pts[0] == (70.0, 1.8):
        i = pts.index((69.55, 2.7))
        runs.append(dict(layer=2, pts=[list(p) for p in pts[i:]]))
    elif run['layer'] == 1 and pts[0] == (64.75, 16.95):
        continue  # run2 dropped, re-planned below
    else:
        runs.append(run)
CLK9P = dict(vias=J9['vias'], runs=runs)
add_new('clk9', CLK9P, 'CAP_CLK', 0.10)
astarNE = make_astar((60.0, 78.0, 10.0, 28.0), 0.025)
J = astarNE('CAP_CLK', ((1,), 64.75, 16.95), (1, 70.1, 21.8), hw=0.10,
            layer_lock=(False, True, False))
mode = 'in2'
if J is None:
    J = astarNE('CAP_CLK', ((0, 1, 2), 64.75, 16.95), (1, 70.1, 21.8),
                hw=0.10)
    mode = 'multi'
print(f'CLK run2 re-plan ({mode}):', 'FOUND' if J else 'NONE',
      flush=True)
if J:
    add_new('clk_run2', J, 'CAP_CLK', 0.10)
print('model assembled', flush=True)

TARGETS = {'PG_3V3': (54.0, 74.0, -18.0, 18.0),
           '+3V3D': (66.0, 78.0, 16.0, 28.0),
           'XO': (64.0, 78.0, 8.0, 24.0)}
RIP2 = {net: [] for net in TARGETS}
for net, (bx0, bx1, by0, by1) in TARGETS.items():
    seen = set()
    for l in range(3):
        cand = [it for it in pool[l] if it[1] == net
                and bx0 < C(it)[0] < bx1 and by0 < C(it)[1] < by1]
        for nit in NEW[l]:
            ncx, ncy = C(nit)
            if not (bx0 - 2 < ncx < bx1 + 2 and by0 - 2 < ncy < by1 + 2):
                continue
            for it in cand:
                key = (l, it[0], it[2])
                if key in seen:
                    continue
                if item_margin(l, nit, [it]) < 0:
                    seen.add(key)
                    RIP2[net].append(it)
    print(f'{net}: rip {len(RIP2[net])} items', flush=True)
for net, lst in RIP2.items():
    for it in lst:
        for l in range(3):
            if it in pool[l]:
                pool[l].remove(it)

src71 = open('scratch/work/au/t_au71_phase2b.py').read()
frag_src = src71[src71.index("def fragments"):src71.index("def detour")]
frag_src = frag_src.replace("< 0.02", "< 0.04")
exec(frag_src, g)
fragments = g['fragments']


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
                # snap endpoints to exact terminals
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
detour2('+3V3D', (66.0, 78.0, 16.0, 28.0), 0.15, step=0.025)
print('XO detours:', flush=True)
detour2('XO', (64.0, 78.0, 8.0, 24.0), 0.10,
        layer_lock=(False, True, False), step=0.025)
astarF = make_astar((66.0, 72.5, -0.5, 6.0), 0.025)
J = astarF('I2C_SCL', ((0, 1, 2), 69.35, 1.40), (0, 66.2, 2.08), hw=0.10)
print('SCL fanout final:', 'FOUND' if J else 'NONE', flush=True)
if J:
    add_new('scl_ffan', J, 'I2C_SCL', 0.10)
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
                print(f'GATE FAIL L{l} {m:+.3f} NEW {L.fmt_it(nit)}',
                      flush=True)
print(f'full gate: {bad} failures', flush=True)
for net, box in (('CAP_CLK', (55.0, 80.0, -2.0, 30.0)),
                 ('CAP_DATA', (55.0, 80.0, -2.0, 30.0)),
                 ('PG_3V3', (50.0, 78.0, -20.0, 30.0)),
                 ('+3V3D', (60.0, 80.0, 10.0, 30.0)),
                 ('XO', (60.0, 80.0, 5.0, 26.0)),
                 ('I2C_SCL', (60.0, 80.0, -2.0, 16.0)),
                 ('I2C_SDA', (60.0, 80.0, -2.0, 16.0)),
                 ('+3V3A', (60.0, 80.0, -2.0, 16.0))):
    fr = fragments(net, box)
    sizes = sorted((len(f['items']) for f in fr), reverse=True)
    print(f'fragments {net}: {len(fr)} sizes {sizes[:6]}', flush=True)
json.dump(dict(
    journeys=g['JOURNEYS'],
    fixed={str(l): [[it[0], it[1], list(it[2]), it[3]]
                     for it in g['FIXED'][l]] for l in range(3)},
    rip2={net: [[it[0], it[1], list(it[2]), it[3]] for it in lst]
          for net, lst in RIP2.items()},
    clk_via=(70.2, 1.8), exit_via=(69.075, 2.8), u9_shift=1.25),
    open('scratch/work/au/build_au74.json', 'w'))
print('saved build_au74.json', flush=True)
print('done', flush=True)

"""t_aw7: coexistence probe for dip vs ride in the goal pocket.
State A (ride first): emit ride (composed), then dip tries with
goal layers 1/0/2. State B (dip first): emit dip (ML, as in t_aw4
run 1), print its In2 run points in the pocket box, then composed
ride over a dive grid."""
import wx
_app = wx.App(False)
import sys, json, math
sys.path.insert(0, 'scratch/work/au')

def build():
    g = {'__name__': 'aw7'}
    src = open('scratch/work/au/t_au97_phase2y.py').read()
    exec(src.split("# 1. RBIAS tail re-lay")[0], g)
    pool = g['pool']
    C = g['C']
    R2 = lambda v: round(v, 3)
    rip19 = [it for it in pool[1] if it[0] == 'seg' and it[1] == 'RBIAS']
    assert len(rip19) == 19
    for it in rip19:
        pool[1].remove(it)
    def shrink_pad(net, old_cx, new_cx, cy=18.0):
        for l in range(3):
            for it in list(pool[l]):
                if it[0] == 'pad' and it[1] == net:
                    cc = C(it)
                    if abs(cc[0] - old_cx) < 0.01 and abs(cc[1] - cy) < 0.01:
                        pool[l].remove(it)
                        pool[l].append(('pad', net,
                                         (new_cx, cy, 0.28, 0.31, 0), it[3]))
                        return True
        return False
    for net, o, n in [('PHY_1V8', 71.725, 72.02), ('GND', 73.275, 72.98),
                      ('+3V3A', 67.975, 68.27), ('GND', 69.525, 69.23)]:
        assert shrink_pad(net, o, n)
    # X2 move to (75.75,32.25) rot0 - pads only (dip/ride don't need webs)
    for l in range(3):
        for it in list(pool[l]):
            if it[0] == 'pad' and (R2(it[2][0]), R2(it[2][1])) in \
                    {(70.45, 24.575), (72.55, 24.575), (72.55, 22.925),
                     (70.45, 22.925)}:
                pool[l].remove(it)
    for (net, dx, dy) in [('+3V3D', -1.05, 0.825), ('GND', 1.05, 0.825),
                          ('REFCLK', 1.05, -0.825), ('+3V3D', -1.05, -0.825)]:
        pool[0].append(('pad', net, (75.75 + dx, 32.25 + dy, 0.65, 0.55, 0),
                        0.2))
    # REFCLK via + F segs rip (rounded)
    def rip_rounded(l, net, geo, kind):
        n = 0
        for it in list(pool[l]):
            if it[0] != kind or it[1] != net:
                continue
            if kind == 'seg':
                key = tuple(R2(v) for v in it[2][:4])
                want = tuple(R2(v) for v in geo)
            else:
                key = (R2(it[2][0]), R2(it[2][1]))
                want = (R2(geo[0]), R2(geo[1]))
            if key == want:
                pool[l].remove(it)
                n += 1
        assert n == 1, f'rip {kind} {net} {geo} L{l}: {n}'
    for l in range(3):
        rip_rounded(l, 'REFCLK', (71.875, 23.375), 'via')
    rip_rounded(0, 'REFCLK', (72.3, 22.925, 72.55, 22.925), 'seg')
    rip_rounded(0, 'REFCLK', (71.875, 23.375, 72.3, 22.925), 'seg')
    return g

def ride_composed(g, dive):
    pool = g['pool']
    a_rb = g['make_astar']((67.0, 75.5, 10.5, 22.5), step=0.025)
    J1 = a_rb('RBIAS', ((1,), 73.875, 11.625), (1, dive[0], dive[1]),
              0.125, layer_lock=(False, True, False))
    if J1 is None:
        return None, 'In2 leg NONE'
    J2 = a_rb('RBIAS', ((2,), dive[0], dive[1]), (2, 69.625, 20.625),
              0.125, layer_lock=(False, False, True))
    if J2 is None:
        return None, 'B hop NONE'
    return dict(vias=[list(dive)], runs=J1['runs'] + J2['runs']), 'ok'

print('########## STATE A: ride first ##########', flush=True)
g = build()
pool = g['pool']
try_emit = g['try_emit']
Jr, why = ride_composed(g, (69.925, 20.475))
print(f'ride composed: {why}', flush=True)
assert Jr is not None and try_emit('rbias_relay', Jr, 'RBIAS', 0.125)
print('ride pts near pocket (In2 leg, x<71.5):', flush=True)
for r in Jr['runs']:
    if r['layer'] == 1:
        pts = [p for p in r['pts'] if p[0] < 71.5]
        print(f'  In2 leg tail pts: {pts[-14:]}', flush=True)
a_dip = g['make_astar']((66.0, 76.0, 16.5, 27.5), step=0.025)
for gl in (1, 0, 2):
    J = a_dip('XO', ((0,), 71.625, 25.625), (gl, 68.875, 20.375), 0.10)
    print(f'dip goal layer {gl}: ' +
          ('NONE' if J is None else
           f'vias={J["vias"]} '
           f'runs={[(r["layer"], len(r["pts"])) for r in J["runs"]]}'),
          flush=True)
    if J is not None:
        for r in J['runs']:
            if r['layer'] == 1:
                pts = [p for p in r['pts'] if p[0] < 71.5]
                print(f'  dip In2 tail pts: {pts[-14:]}', flush=True)
        break

print('########## STATE B: dip first ##########', flush=True)
g = build()
pool = g['pool']
try_emit = g['try_emit']
a_dip = g['make_astar']((66.0, 76.0, 16.5, 27.5), step=0.025)
J = a_dip('XO', ((0,), 71.625, 25.625), (1, 68.875, 20.375), 0.10)
assert J is not None, 'dip NONE in state B'
print(f'dip: vias={J["vias"]} '
      f'runs={[(r["layer"], len(r["pts"])) for r in J["runs"]]}', flush=True)
assert try_emit('xo_bridge', J, 'XO', 0.10)
for r in J['runs']:
    if r['layer'] == 1:
        pts = [p for p in r['pts'] if p[0] < 72.5]
        print(f'dip In2 run pts (x<72.5): {pts}', flush=True)
print('ride composed over dive grid (dip emitted):', flush=True)
found = []
for dxi in range(0, 13):
    for dyi in range(0, 11):
        dive = (69.45 + 0.1 * dxi, 19.95 + 0.1 * dyi)
        Jr, why = ride_composed(g, dive)
        if Jr is not None:
            ok = try_emit('rbias_relay', Jr, 'RBIAS', 0.125)
            print(f'  dive {dive}: composed OK, gate {"EMITTED" if ok else "REFUSED"}',
                  flush=True)
            if ok:
                found.append(dive)
                break
    if found:
        break
if not found:
    print('  no dive in grid composes+emits', flush=True)
print('done', flush=True)

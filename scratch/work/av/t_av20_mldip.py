"""t_av20: multi-layer dip A* in the full current state.
State: au93 + staircase rip (19) + C49 E+0.5 + web + DIR re-lay
(NO dummies). Dip: stub (71.875,19.625) B -> (68.875,20.375) In2,
any layers. Then RBIAS ride attempts."""
import wx
_app = wx.App(False)
import sys
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'av20'}
src = open('scratch/work/au/t_au97_phase2y.py').read()
exec(src.split("# 1. RBIAS tail re-lay")[0], g)
pool = g['pool']
item_centre = g['C']
fragments = g['fragments']
gate_pairs = g['gate_pairs']
try_emit = g['try_emit']
journey_items_dense = g['journey_items_dense']
make_astar = g['make_astar']
NET_HW = g['NET_HW']
import t_ai_lib as L

R2 = lambda v: round(v, 3)

def rip_rounded(layer, net, pred):
    n = 0
    for it in list(pool[layer]):
        if it[1] == net and pred(it):
            pool[layer].remove(it)
            n += 1
    return n

# staircase rip (keep stub + vertical)
STUB = (73.875, 11.625, 73.875, 12.875)
VERT = (73.875, 12.875, 73.875, 16.375)
def is_stair(it):
    return it[0] == 'seg' and tuple(R2(v) for v in it[2]) not in (STUB, VERT)
n = rip_rounded(1, 'RBIAS', is_stair)
print(f'staircase rip: {n}', flush=True)
assert n == 19

# C49 move
C49O = (70.0, 19.5)
C49N = (70.5, 19.5)
def c49_pad(net, cx):
    for l in range(3):
        for it in pool[l]:
            if it[0] == 'pad' and it[1] == net:
                cc = item_centre(it)
                if abs(cc[0] - cx) < 0.01 and abs(cc[1] - 19.5) < 0.01:
                    return l, it
    return None
res = {}
for net, cx in (('+3V3A', 69.225), ('GND', 70.775)):
    r = c49_pad(net, cx)
    res[net] = r
    l, it = r
    pool[l].remove(it)
    kind, ntn, (ccx, ccy, hw_, hh, rot), clr = it
    pool[l].append(('pad', ntn, (ccx + 0.5, ccy, hw_, hh, rot), clr))
# web re-lay (t_av16 exact items)
for l in list(pool):
    for it in list(pool[l]):
        if it[0] == 'seg' and it[1] == '+3V3A':
            x1, y1, x2, y2, hw_ = it[2]
            if (abs(x2 - 69.225) < 0.01 and abs(y2 - 19.5) < 0.01
                    and abs(hw_ - 0.150) < 0.001):
                pool[l].remove(it)
                print(f'  C49 web end seg removed L{l}: {L.fmt_it(it)}',
                      flush=True)
ast = make_astar((66.0, 74.0, 15.0, 23.0), step=0.025)
J = ast('+3V3A', ((0,), 69.725, 19.5), (0, 69.225, 19.5), 0.15)
assert J is not None
assert try_emit('c49_web_v3a', J, '+3V3A', 0.15), 'C49 web gate refused'
print('C49 moved + web', flush=True)

# DIR re-lay (no dummies)
DIR_SEG = (71.375, 19.125, 68.875, 29.0)
n = rip_rounded(2, 'ULPI_DIR',
                lambda it: it[0] == 'seg'
                and tuple(R2(v) for v in it[2][:4]) == DIR_SEG)
assert n == 1
a_dir = make_astar((68.3, 74.8, 18.6, 29.6), step=0.025)
J = a_dir('ULPI_DIR', ((2,), 71.375, 19.125), (2, 68.875, 29.0), 0.10)
assert J is not None
assert try_emit('dir_tail_relay', J, 'ULPI_DIR', 0.10), 'DIR gate refused'
print('DIR re-laid', flush=True)

# MULTI-LAYER DIP
a_dip = make_astar((67.5, 75.5, 14.5, 23.5), step=0.025)
J = None
for hw in (0.10, 0.125):
    J = a_dip('XO', ((2,), 71.875, 19.625), (1, 68.875, 20.375), hw)
    print(f'dip hw={hw}: ' +
          ('NONE' if J is None else
           f'vias={J["vias"]} runs={[(r["layer"], len(r["pts"])) for r in J["runs"]]}'),
          flush=True)
    if J is not None:
        break
if J is not None:
    fails = gate_pairs(J, 'XO', hw)
    print(f'xo_bridge gate fails={len(fails)}', flush=True)
    for (m, l, it, o) in fails[:8]:
        print(f'    {m:+.3f} L{l} {L.fmt_it(it)} vs {L.fmt_it(o)}',
              flush=True)
    if not fails:
        assert try_emit('xo_bridge', J, 'XO', hw)
        frags = fragments('XO', (66, 78, 9, 26))
        print(f'XO fragments after bridge: {len(frags)} '
              f'sizes {[len(f["items"]) for f in frags]}', flush=True)

# RBIAS ride (dip in pool either way)
a_rb = make_astar((67.0, 75.0, 10.5, 22.5), step=0.025)
for hw in (0.125, 0.10):
    J2 = a_rb('RBIAS', ((0, 1, 2), 73.875, 11.625), (2, 69.625, 20.625),
              hw)
    print(f'ride hw={hw}: ' +
          ('NONE' if J2 is None else
           f'vias={J2["vias"]} runs={[(r["layer"], len(r["pts"])) for r in J2["runs"]]}'),
          flush=True)
    if J2 is not None:
        fails = gate_pairs(J2, 'RBIAS', hw)
        print(f'ride gate fails={len(fails)}', flush=True)
        for (m, l, it, o) in fails[:8]:
            print(f'    {m:+.3f} L{l} {L.fmt_it(it)} vs {L.fmt_it(o)}',
                  flush=True)
        break
print('done', flush=True)

"""t_au76: DATA run2 diagnostic in the au75 model state.
1. Gate J30's original run2 verbatim vs the current pool.
2. Ablations: DATA run2 A* with each candidate fence net removed
   from the arrival box.
3. Widest-path bottleneck on In2 + fence attribution."""
import wx
_app = wx.App(False)
import sys, json, math
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'diag'}
src75 = open('scratch/work/au/t_au75_phase2f.py').read()
exec(src75.split("astarA = make_astar")[0], g)
pool = g['pool']
add_new = g['add_new']
C = g['C']
import t_ai_lib as L
import t_au1_lib as U

item_margin = g['item_margin']
make_astar = g['make_astar']
journey_items_dense = g.get('journey_items_dense') \
    or g['g']['journey_items_dense']

# 1. gate J30 run2 verbatim
J30 = json.load(open('scratch/work/as/journey30_CAP_DATA_DC.json'))
run2 = dict(vias=[], runs=[J30['runs'][2]])
items = journey_items_dense(run2, 'CAP_DATA', hw=0.10)
worst = []
for l in range(3):
    for it in items[l]:
        m = item_margin(l, it, pool[l])
        worst.append((m, l, it))
worst.sort(key=lambda t: t[0])
print('J30 run2 verbatim gate - worst 6:', flush=True)
for m, l, it in worst[:6]:
    print(f'  {m:+.3f} L{l} {L.fmt_it(it)}', flush=True)
    if m < 0.05:
        d = it[2]
        cx, cy = (d[0] + d[2]) / 2, (d[1] + d[3]) / 2
        near = [o for o in pool[l]
                if o[1] != 'CAP_DATA'
                and abs(C(o)[0] - cx) < 2.5 and abs(C(o)[1] - cy) < 2.5]
        for o in near:
            mm = item_margin(l, it, [o])
            if mm < 0.1:
                print(f'      vs {mm:+.3f} {L.fmt_it(o)}', flush=True)

# 2. ablations
astarA = make_astar((60.0, 78.0, 10.0, 28.0), 0.025)
BOX = (60.0, 78.0, 10.0, 28.0)


def try_data(tag, dropnets=()):
    saved = {}
    for l in range(3):
        saved[l] = pool[l]
        pool[l] = [it for it in pool[l]
                   if not (it[1] in dropnets
                           and BOX[0] < C(it)[0] < BOX[1]
                           and BOX[2] < C(it)[1] < BOX[3])]
    J = astarA('CAP_DATA', ((1,), 64.7, 15.45), (1, 72.6, 19.3),
               hw=0.10, layer_lock=(False, True, False))
    print(f'DATA run2 [{tag}]:', 'FOUND' if J else 'NONE', flush=True)
    for l in range(3):
        pool[l] = saved[l]
    return J


try_data('baseline')
for net in ('PG_3V3', 'XO', '+3V3D', 'CAP_CLK', 'CDR_DATN',
            'CDR_DATP'):
    try_data(f'minus {net}', (net,))
try_data('minus PG+XO+3V3D+CLK', ('PG_3V3', 'XO', '+3V3D', 'CAP_CLK'))

# 3. widest bottleneck on In2
G = U.build_fields(pool, 'CAP_DATA')
w = U.widest(G, 'CAP_DATA')
print('widest machinery ready (see t_au1 usage in file)', flush=True)
print('done', flush=True)

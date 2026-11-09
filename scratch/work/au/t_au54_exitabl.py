"""t_au54: exit ablation in heal1-placed model."""
import wx
_app = wx.App(False)
import sys, json
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'p1b'}
src53 = open('scratch/work/au/t_au53_exitmask.py').read()
head = src53.split("J = entry_astar")[0]
exec(head, g)
pool_full = g['pool']
run_astar = g['run_astar']
import t_au1_lib as U
C = U.item_centre
J53 = json.load(open('scratch/work/au/heals_au53.json'))

def try_exit(poolx, tag):
    g['pool'] = poolx
    # run_astar/build_G read 'pool' from g (exec globals)
    J = run_astar('CAP_CLK', ((0, 1, 2), 70.2, 1.8), (2, 69.55, 2.70))
    print(f'{tag}:', 'FOUND' if J else 'NONE', flush=True)
    if J:
        print('   vias', J['vias'],
              [(r['layer'], r['pts'][0], r['pts'][-1]) for r in J['runs']],
              flush=True)

try_exit(pool_full, 'full (heal1 placed)')
def minus(net, box=None):
    out = {}
    for l in range(3):
        out[l] = []
        for it in pool_full[l]:
            if it[1] == net:
                if box is None:
                    continue
                cx, cy = C(it)
                if box[0] < cx < box[1] and box[2] < cy < box[3]:
                    continue
            out[l].append(it)
    return out
try_exit(minus('I2C_SCL', (66.0, 72.5, -0.5, 6.0)), 'minus bheal')
try_exit(minus('I2C_SDA', (66.0, 72.5, -0.5, 6.0)), 'minus hop+SDA pocket')
try_exit(minus('+3V3A', (66.0, 72.5, -0.5, 6.0)), 'minus heal1')
try_exit(minus('PG_3V3', (60.0, 72.0, -2.0, 17.0)), 'minus PG pocket')
try_exit(minus('CAP_DATA', (66.0, 72.5, -0.5, 6.0)), 'minus DATA pocket')
print('done')

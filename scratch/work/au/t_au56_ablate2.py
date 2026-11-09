"""t_au56: correct exit ablation (single exec context, pool rebuilt
per variant from a pristine base). Base = esc-rips+FIXED+CLK v5.
Variants add subsets of {bheal, hop, heal1F} then try the exit."""
import wx
_app = wx.App(False)
import sys, json
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'p1b'}
src = open('scratch/work/au/t_au43_phase1b.py').read()
exec(src.split("J40 = json.load")[0], g)
exec(src[src.index("def entry_astar"):src.index("out = {}")], g)
exec(src[src.index("FBOX ="):src.index("J = fastest('+3V3A'")], g)
BASE = {l: list(g['pool'][l]) for l in range(3)}
fastest = g['fastest']
journey_items_dense = g['journey_items_dense']
J40 = json.load(open('scratch/work/au/joint_au40.json'))
J53 = json.load(open('scratch/work/au/heals_au53.json'))


def set_pool(extra):
    g['pool'] = {l: list(BASE[l]) for l in range(3)}
    for J, net, hw in extra:
        for l, its in journey_items_dense(J, net, hw=hw).items():
            g['pool'][l] += its


def try_exit(tag):
    J = fastest('CAP_CLK', ((0, 1, 2), 70.2, 1.8), (2, 69.55, 2.70))
    print(f'{tag}: exit', 'FOUND' if J else 'NONE', flush=True)
    return J


BHEAL = (J40['jobs']['bheal'], 'I2C_SCL', 0.10)
HOP = (J40['jobs']['hop'], 'I2C_SDA', 0.125)
set_pool([BHEAL, HOP])
try_exit('bheal+hop')
# heal1 F-only in this state
J1 = fastest('+3V3A', ((0,), 68.225, 2.75), (0, 69.125, 4.375),
             hw=0.10)
print('heal1 multi-layer here:', 'FOUND' if J1 else 'NONE',
      'vias', J1['vias'] if J1 else None, flush=True)
set_pool([BHEAL])
try_exit('bheal only')
set_pool([HOP])
try_exit('hop only')
set_pool([])
try_exit('neither')
print('done', flush=True)

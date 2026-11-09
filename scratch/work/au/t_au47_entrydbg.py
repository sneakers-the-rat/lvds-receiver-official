"""t_au47: rebuild t_au46 state stepwise; probe entry start field."""
import wx
_app = wx.App(False)
import sys, json
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'p1b'}
src = open('scratch/work/au/t_au43_phase1b.py').read()
exec(src.split("J40 = json.load")[0], g)
exec(src[src.index("def entry_astar"):src.index("out = {}")], g)
pool = g['pool']
entry_astar = g['entry_astar']
journey_items_dense = g['journey_items_dense']
import t_ai_lib as L

def probe(tag):
    m, w = L.pt_margin(1, 69.9, 3.175, 'CAP_DATA', 0.10,
                       [o for o in pool[1] if o[1] != 'CAP_DATA'])
    print(f'{tag}: entry start field {m:+.3f} vs {L.fmt_it(w)}', flush=True)

probe('base+CLKvia')
J40 = json.load(open('scratch/work/au/joint_au40.json'))
for nm in ('bheal', 'hop'):
    J = J40['jobs'][nm]
    net = {'bheal': 'I2C_SCL', 'hop': 'I2C_SDA'}[nm]
    hw = 0.125 if nm == 'hop' else 0.10
    for l, its in journey_items_dense(J, net, hw=hw).items():
        pool[l] += its
probe('after bheal+hop')
J = entry_astar('CAP_DATA', 1, 69.9, 3.175, 63.85, 6.3,
                (60.0, 72.0, -1.0, 10.0))
print('entry here:', 'FOUND' if J else 'NONE', flush=True)

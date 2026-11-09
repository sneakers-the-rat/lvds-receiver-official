"""t_au57: order 4 — bheal, hop, heal1 MULTI-LAYER, exit, entry,
tail, heal2. Saves heals_au57.json."""
import wx
_app = wx.App(False)
import sys, json
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'p1b'}
src = open('scratch/work/au/t_au43_phase1b.py').read()
exec(src.split("J40 = json.load")[0], g)
exec(src[src.index("def entry_astar"):src.index("out = {}")], g)
exec(src[src.index("FBOX ="):src.index("J = fastest('+3V3A'")], g)
pool = g['pool']
fastest = g['fastest']
entry_astar = g['entry_astar']
journey_items_dense = g['journey_items_dense']
J40 = json.load(open('scratch/work/au/joint_au40.json'))


def add_j(J, net, hw=0.10):
    for l, its in journey_items_dense(J, net, hw=hw).items():
        pool[l] += its


add_j(J40['jobs']['bheal'], 'I2C_SCL', 0.10)
add_j(J40['jobs']['hop'], 'I2C_SDA', 0.125)
out = {}
J = fastest('+3V3A', ((0,), 68.225, 2.75), (0, 69.125, 4.375), hw=0.10)
print('heal1 multi:', 'FOUND' if J else 'NONE',
      'vias', J['vias'] if J else None, flush=True)
if J:
    out['v3a_heal1'] = J
    add_j(J, '+3V3A', 0.10)
Jx = None
for goal in ((69.55, 2.70), (69.4, 2.8)):
    J = fastest('CAP_CLK', ((0, 1, 2), 70.2, 1.8), (2, goal[0], goal[1]))
    if J:
        Jx = J
        out['clk_exit'] = J
        out['clk_rejoin'] = goal
        print(f'exit -> {goal}: FOUND vias={J["vias"]}', flush=True)
        break
if Jx:
    add_j(Jx, 'CAP_CLK', 0.10)
else:
    print('exit: NONE', flush=True)
J = entry_astar('CAP_DATA', 1, 69.9, 3.175, 63.85, 6.3,
                (60.0, 72.0, -1.0, 10.0))
print('DATA entry:', 'FOUND' if J else 'NONE', flush=True)
if J:
    out['data_entry'] = J
    add_j(J, 'CAP_DATA')
    J30 = json.load(open('scratch/work/as/journey30_CAP_DATA_DC.json'))
    pts0 = J30['runs'][0]['pts']
    TAIL = dict(vias=J30['vias'],
                runs=[dict(layer=1, pts=pts0[213:])] + J30['runs'][1:])
    out['data_tail'] = TAIL
    add_j(TAIL, 'CAP_DATA')
J = fastest('+3V3A', ((0,), 71.375, 0.875), (0, 69.125, 4.375),
            hw=0.10)
print('heal2:', 'FOUND' if J else 'NONE', flush=True)
if J:
    out['v3a_heal2'] = J
json.dump(out, open('scratch/work/au/heals_au57.json', 'w'))
print('done', flush=True)

"""t_au60: pocket v6 - U9 west 1.25. Order: bheal, hop, exit,
heal1, SCL fanout, DATA entry + tail, heal2. Saves heals_au60.json
(includes u9_shift=1.25)."""
import wx
_app = wx.App(False)
import sys, json
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'p1b'}
src = open('scratch/work/au/t_au43_phase1b.py').read()
head = src.split("J40 = json.load")[0]
head = head.replace("d[0] - 1.0", "d[0] - 1.25")
head = head.replace("(68.45, 2.1), (69.05, 2.05)",
                    "(67.975, 2.1), (69.05, 2.05)")
head = head.replace("TMP = [(66.275, 3.4)", "TMP = [(66.025, 3.4)")
exec(head, g)
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
add_j(J40['jobs']['exit'], 'CAP_CLK', 0.10)
out = {'u9_shift': 1.25, 'clk_exit': J40['jobs']['exit'],
       'clk_rejoin': (69.55, 2.70)}
J = fastest('+3V3A', ((0,), 67.975, 2.75), (0, 69.125, 4.375), hw=0.10)
print('heal1 v6:', 'FOUND' if J else 'NONE', flush=True)
if J:
    print('  vias', J['vias'], flush=True)
    out['v3a_heal1'] = J
    add_j(J, '+3V3A', 0.10)
J = fastest('I2C_SCL', ((0,), 69.35, 1.40), (0, 66.025, 2.10), hw=0.10)
print('SCL fanout v6:', 'FOUND' if J else 'NONE', flush=True)
if J:
    out['scl_ffan'] = J
    add_j(J, 'I2C_SCL', 0.10)
J = entry_astar('CAP_DATA', 1, 69.9, 3.175, 63.85, 6.3,
                (60.0, 72.0, -1.0, 10.0))
print('DATA entry v6:', 'FOUND' if J else 'NONE', flush=True)
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
print('heal2 v6:', 'FOUND' if J else 'NONE', flush=True)
if J:
    out['v3a_heal2'] = J
json.dump(out, open('scratch/work/au/heals_au60.json', 'w'))
print('done', flush=True)

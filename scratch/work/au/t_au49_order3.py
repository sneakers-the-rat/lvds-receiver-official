"""t_au49: order 3 — au40 exit placed, heal1 multi-layer (entry
absent), then DATA entry re-run, tail, heal2."""
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
entry_astar = g['entry_astar']
journey_items_dense = g['journey_items_dense']
fastest = g['fastest']


def add_j(J, net, hw=0.10):
    for l, its in journey_items_dense(J, net, hw=hw).items():
        pool[l] += its


J40 = json.load(open('scratch/work/au/joint_au40.json'))
for nm in ('bheal', 'hop', 'exit'):
    J = J40['jobs'][nm]
    net = {'bheal': 'I2C_SCL', 'hop': 'I2C_SDA', 'exit': 'CAP_CLK'}[nm]
    hw = 0.125 if nm == 'hop' else 0.10
    add_j(J, net, hw)
out = {'clk_exit': J40['jobs']['exit'], 'clk_rejoin': (69.55, 2.70)}
J = fastest('+3V3A', ((0,), 68.225, 2.75), (0, 69.125, 4.375), hw=0.10)
print('heal1 (exit placed, no entry):', 'FOUND' if J else 'NONE',
      flush=True)
if J:
    print('  vias', J['vias'],
          [(r['layer'], r['pts'][0], r['pts'][-1]) for r in J['runs']],
          flush=True)
    out['v3a_heal1'] = J
    add_j(J, '+3V3A', 0.10)
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
J = fastest('+3V3A', ((0,), 71.375, 0.875), (0, 69.125, 4.375), hw=0.10)
print('heal2:', 'FOUND' if J else 'NONE', flush=True)
if J:
    out['v3a_heal2'] = J
json.dump(out, open('scratch/work/au/heals_au49.json', 'w'))
print('done', flush=True)

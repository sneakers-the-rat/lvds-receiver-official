"""t_au46: resolve heal1-vs-exit ordering. v5 model WITHOUT the
au40 exit: heal1 A* (F) first, then exit A* (multi-layer), then
DATA entry + tail, then heal2 attempt. Saves heals_au46.json."""
import wx
_app = wx.App(False)
import sys, json
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'p1b'}
src = open('scratch/work/au/t_au43_phase1b.py').read()
head = src.split("J40 = json.load")[0]
exec(head, g)
pool = g['pool']
fastest = g['fastest']
entry_astar = g['entry_astar']
journey_items_dense = g['journey_items_dense']
seg_ = g['seg_']
via_ = g['via_']

# CLK v5 via + stub (no exit yet)
via_(pool, 'CAP_CLK', 70.2, 1.8)
seg_(pool, 0, 'CAP_CLK', (71.338, 1.75), (70.62, 1.79))
seg_(pool, 0, 'CAP_CLK', (70.62, 1.79), (70.2, 1.8))
J40 = json.load(open('scratch/work/au/joint_au40.json'))
for nm in ('bheal', 'hop'):
    J = J40['jobs'][nm]
    net = {'bheal': 'I2C_SCL', 'hop': 'I2C_SDA'}[nm]
    hw = 0.125 if nm == 'hop' else 0.10
    for l, its in journey_items_dense(J, net, hw=hw).items():
        pool[l] += its
print('model (no exit) built', flush=True)
out = {}


def add_j(J, net, hw=0.10):
    for l, its in journey_items_dense(J, net, hw=hw).items():
        pool[l] += its


J = fastest('+3V3A', ((0,), 68.225, 2.75), (0, 69.125, 4.375), hw=0.10)
print('heal1 (no exit):', 'FOUND' if J else 'NONE', flush=True)
if J:
    out['v3a_heal1'] = J
    add_j(J, '+3V3A', 0.10)
J = fastest('CAP_CLK', ((0, 1, 2), 70.2, 1.8), (2, 69.55, 2.70))
print('exit (after heal1):', 'FOUND' if J else 'NONE', flush=True)
if J:
    out['clk_exit'] = J
    print('  vias', J['vias'],
          [(r['layer'], r['pts'][0], r['pts'][-1]) for r in J['runs']],
          flush=True)
    add_j(J, 'CAP_CLK', 0.10)
    for (vx, vy) in J['vias']:
        pass  # journey_items_dense already added via items
J = entry_astar('CAP_DATA', 1, 69.9, 3.175, 63.85, 6.3,
                (60.0, 72.0, -1.0, 10.0))
print('DATA entry (final cfg):', 'FOUND' if J else 'NONE', flush=True)
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
print('heal2 (final cfg):', 'FOUND' if J else 'NONE', flush=True)
if J:
    out['v3a_heal2'] = J
json.dump(out, open('scratch/work/au/heals_au46.json', 'w'))
print('done', flush=True)

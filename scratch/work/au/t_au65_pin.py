"""t_au65: v6 + exit dive pinned at (69.025,2.8). Order: bheal,
hop, heal1 F-only (reservation disc at the dive point), exit
(F-run A* to the dive point + B join seg, gated), SCL fanout,
DATA entry + tail, heal2. Saves heals_au65.json."""
import wx
_app = wx.App(False)
import sys, json
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'p1b'}
src = open('scratch/work/au/t_au60_v6.py').read()
exec(src.split("\nout = {")[0], g)
pool = g['pool']
fastest = g['fastest']
entry_astar = g['entry_astar']
journey_items_dense = g['journey_items_dense']
def seg_(store, l, net, a, b, hw=0.10, clr=0.2):
    store[l].append(('seg', net, (a[0], a[1], b[0], b[1], hw), clr))


def via_(store, net, x, y, r=0.25, clr=0.2):
    for l in range(3):
        store[l].append(('via', net, (x, y, r), clr))
import t_ai_lib as L
J40 = json.load(open('scratch/work/au/joint_au40.json'))

# NOTE: src60 head already placed bheal+hop+exit(au40). Remove the
# au40 exit items (CAP_CLK items in pocket box beyond via/stub):
import t_au1_lib as U
C = U.item_centre


def is_au40_exit(it):
    if it[1] != 'CAP_CLK':
        return False
    if it[0] == 'via':
        return abs(it[2][0] - 68.975) < 0.01 and abs(it[2][1] - 2.8) < 0.01
    return it[2][0] < 70.3 and it[2][2] < 70.3


for l in range(3):
    pool[l] = [it for it in pool[l] if not is_au40_exit(it)]
print('au40 exit removed', flush=True)


def add_j(J, net, hw=0.10):
    for l, its in journey_items_dense(J, net, hw=hw).items():
        pool[l] += its


out = {'u9_shift': 1.25}
# reservation disc for heal1's A*
via_(pool, 'CAP_CLK', 69.025, 2.8)
J = fastest('+3V3A', ((0,), 67.975, 2.75), (0, 69.125, 4.375),
            hw=0.10)
# remove the reservation (real exit items re-added below)
for l in range(3):
    pool[l] = [it for it in pool[l]
               if not (it[0] == 'via' and it[1] == 'CAP_CLK'
                       and abs(it[2][0] - 69.025) < 0.01
                       and abs(it[2][1] - 2.8) < 0.01)]
print('heal1 (dive reserved):', 'FOUND' if J else 'NONE', flush=True)
if J:
    print('  heal1 vias (must be []):', J['vias'], flush=True)
    out['v3a_heal1'] = J
    add_j(J, '+3V3A', 0.10)
# exit: F run A* to the dive point, then via + B join
J = fastest('CAP_CLK', ((0,), 70.2, 1.8), (0, 69.025, 2.8))
print('exit F run:', 'FOUND' if J else 'NONE', flush=True)
if J:
    out['clk_exit_frun'] = J
    add_j(J, 'CAP_CLK', 0.10)
    via_(pool, 'CAP_CLK', 69.025, 2.8)
    m, w = L.seg_margin(2, (69.025, 2.8), (69.55, 2.7), 'CAP_CLK', 0.10,
                        [o for o in pool[2] if o[1] != 'CAP_CLK'])
    print(f'exit B join gate: {m:+.3f} vs {L.fmt_it(w)}', flush=True)
    if m >= 0:
        seg_(pool, 2, 'CAP_CLK', (69.025, 2.8), (69.55, 2.7))
        out['clk_exit_bjoin'] = [(69.025, 2.8), (69.55, 2.7)]
        out['clk_rejoin'] = (69.55, 2.70)
J = fastest('I2C_SCL', ((0,), 69.35, 1.40), (0, 66.025, 2.10), hw=0.10)
print('SCL fanout:', 'FOUND' if J else 'NONE', flush=True)
if J:
    out['scl_ffan'] = J
    add_j(J, 'I2C_SCL', 0.10)
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
json.dump(out, open('scratch/work/au/heals_au65.json', 'w'))
print('done', flush=True)

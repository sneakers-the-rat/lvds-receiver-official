import sys, json
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
import t_ax0_pre as P
pool = load_board_pool('hw/pdlvds_rx.exp248.kicad_pcb')

print('== items in C14 target box (73,77,33,36.5):', flush=True)
seen = set()
for lay in range(3):
    for it in pool[lay]:
        d = it[2]
        if 73 < d[0] < 77 and 33 < d[1] < 36.5:
            s = 'L%d ' % lay + L.fmt_it(it)
            if s not in seen:
                seen.add(s)
                print('  ', s, flush=True)

# 1. move C14 in the model: rip both pads + REFCLKN stub seg
c14_old = [it for it in pool[0]
           if it[0] == 'pad' and abs(it[2][1] - 36.75) < 0.01
           and it[2][0] in (71.225, 72.775)]
stub = [it for it in pool[0] if it[1] == 'REFCLKN' and it[0] == 'seg'
        and abs(it[2][0] - 71.7) < 0.01 and abs(it[2][1] - 37.55) < 0.01]
print('C14 pads found:', len(c14_old), 'stub segs:', len(stub), flush=True)
n = rip_items(c14_old + stub)
print('ripped:', n, flush=True)
newpads = {}
for net, cx in (('REFCLKN', 73.975), ('GND', 75.525)):
    pad = ('pad', net, (cx, 34.75, 0.450, 0.475, 0.0), 0.2)
    newpads[net] = pad
add_items({0: list(newpads.values())})

def gate(its, net):
    worst = (9.9, None, None)
    for l in range(3):
        for it in its[l]:
            for o in pool[l]:
                if o[1] == net:
                    continue
                m = item_margin(l, it, [o])
                if m < worst[0]:
                    worst = (m, it, o)
    return worst

# 2. REFCLKN rejoin: new pad -> existing via (71.7,37.55)
astar = make_astar((70.0, 76.0, 32.0, 39.0), 0.05)
J0 = astar('REFCLKN', ((0,), 73.975, 34.75), (0, 71.7, 37.55), hw=0.10)
print('REFCLKN rejoin:', 'FOUND' if J0 else 'NONE', flush=True)
if J0:
    print('  vias:', J0['vias'], flush=True)
    its0 = journey_items_dense(J0, 'REFCLKN', hw=0.10)
    w = gate(its0, 'REFCLKN')
    print(f'  gate worst {w[0]:+.3f} {L.fmt_it(w[1])} vs {L.fmt_it(w[2])}',
          flush=True)
    add_items(its0)

# 3. SDA re-lay with LOS-slot blocker
blocker = ('seg', 'ZZBLOCK', (69.0, 36.5, 70.6, 36.5, 0.10), 0.35)
pool[0].append(blocker)
for _d in P._ns.values():
    _d['pool'] = pool
astar = make_astar((67.0, 74.0, 30.0, 39.0), 0.05)
J1 = astar('I2C_SDA', ((0,), 68.6875, 37.0), (0, 72.125, 32.625),
           hw=0.125)
print('SDA re-lay:', 'FOUND' if J1 else 'NONE', flush=True)
if J1:
    print('  vias:', J1['vias'], flush=True)
    for r in J1['runs']:
        print('  run L%d' % r['layer'], r['pts'], flush=True)
    pool[0].remove(blocker)
    for _d in P._ns.values():
        _d['pool'] = pool
    old = chain_segs(pool, 'I2C_SDA', 0, (68.6875, 37.0), (72.125, 32.625))
    n = rip_items(old)
    print('  SDA old chain ripped:', n, flush=True)
    its1 = journey_items_dense(J1, 'I2C_SDA', hw=0.125)
    add_items(its1)
    w = gate(its1, 'I2C_SDA')
    print(f'  gate worst {w[0]:+.3f} {L.fmt_it(w[1])} vs {L.fmt_it(w[2])}',
          flush=True)

# 4. LOS full route
astar2 = make_astar((66.0, 95.0, -1.0, 39.0), 0.05)
J2 = astar2('CDR_LOS', ((0,), 68.6875, 36.5), (0, 92.6625, 1.75), hw=0.10)
print('LOS full:', 'FOUND' if J2 else 'NONE', flush=True)
if J2:
    print('  vias:', J2['vias'], flush=True)
    its2 = journey_items_dense(J2, 'CDR_LOS', hw=0.10)
    w = gate(its2, 'CDR_LOS')
    print(f'  gate worst {w[0]:+.3f} {L.fmt_it(w[1])} vs {L.fmt_it(w[2])}',
          flush=True)
    json.dump({'refclkn': J0, 'sda': J1, 'los': J2},
              open('scratch/work/ax/los_design_ax92.json', 'w'))
    print('saved los_design_ax92.json', flush=True)

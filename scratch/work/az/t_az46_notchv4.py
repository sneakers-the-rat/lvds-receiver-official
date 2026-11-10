"""t_az45: notch re-lay v3 gated on the FAITHFUL exp251 pool
(nothing else ripped). Via -> (75.27,10.33); F stub
(75.72,11.0)->(75.49,10.69)->via; B head via->(75.05,10.95)
->(74.90,11.75). Rips: old via, F seg2, B head, B leg1.
"""
import sys
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa

BOARD = 'hw/pdlvds_rx.exp251.kicad_pcb'
BOX = (58.0, 96.0, -30.0, 34.0)


def seg(net, x1, y1, x2, y2, hw=0.10, clr=0.25):
    return ('seg', net, (x1, y1, x2, y2, hw), clr)


def via(net, x, y, r=0.25, clr=0.25):
    return ('via', net, (x, y, r), clr)


def gate_items(items_by_layer, label, thresh=0.30):
    worst = []
    for l in range(3):
        for it in items_by_layer.get(l, []):
            for o in pool[l]:
                if o[1] == it[1]:
                    continue
                m = item_margin(l, it, [o])
                if m < thresh:
                    worst.append((round(m, 3), l, it, o))
    worst.sort(key=lambda t: t[0])
    print(f'{label}: {len(worst)} pairs < {thresh}; worst 8:')
    for w in worst[:8]:
        print('   ', w)
    return worst


def rip_pair(net, l, a, b):
    out = []
    for it in pool[l]:
        if it[1] != net or it[0] != 'seg':
            continue
        d = it[2]
        if (abs(d[0] - a[0]) < 0.01 and abs(d[1] - a[1]) < 0.01
                and abs(d[2] - b[0]) < 0.01 and abs(d[3] - b[1]) < 0.01) or \
           (abs(d[0] - b[0]) < 0.01 and abs(d[1] - b[1]) < 0.01
                and abs(d[2] - a[0]) < 0.01 and abs(d[3] - a[1]) < 0.01):
            out.append(it)
    if out:
        rip_items(out)
    return len(out)


pool = load_board_pool(BOARD)
print('faithful 1V8A frags:', len(fragments('PHY_1V8A', BOX)))
nv = [it for it in pool[0] if it[1] == 'PHY_1V8A' and it[0] == 'via'
      and abs(it[2][0] - 75.7375) < 0.01 and abs(it[2][1] - 10.75) < 0.01]
rip_items(nv)
m = 0
m += rip_pair('PHY_1V8A', 0, (75.72, 11.0), (75.7375, 10.75))
m += rip_pair('PHY_1V8A', 2, (75.7375, 10.75), (75.30, 11.35))
m += rip_pair('PHY_1V8A', 2, (75.30, 11.35), (74.90, 11.75))
print('ripped via:', len(nv), 'segs:', m)
NN = {0: [seg('PHY_1V8A', 75.72, 11.0, 75.49, 10.69),
          seg('PHY_1V8A', 75.49, 10.69, 75.27, 10.33),
          via('PHY_1V8A', 75.27, 10.33)],
      1: [via('PHY_1V8A', 75.27, 10.33)],
      2: [via('PHY_1V8A', 75.27, 10.33),
          seg('PHY_1V8A', 75.27, 10.33, 75.05, 10.95),
          seg('PHY_1V8A', 75.05, 10.95, 74.90, 11.75)]}
add_items(NN)
gate_items(NN, 'notch v4 gate (faithful pool)')
print('1V8A frags:', len(fragments('PHY_1V8A', BOX)))
print('=== done ===')

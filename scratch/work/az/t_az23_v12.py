"""t_az23: v12 XI design — west B ride + F feed; only fence moved
is XO's F escape (jog east to x76.78). No notch/STP/PHY changes.
XI: via (74.0,10.2); B ride (74.0,10.2)->(74.45,11.0)
 ->(74.45,12.3)->(74.15,13.0)->(74.15,16.5)->(74.6,17.8)
 ->(75.2,18.4)->arc via (75.625,18.625);
 F feed (74.0,10.2)->(74.8,10.15)->(75.6,10.0)->(76.2,10.2)
 ->(76.34,10.5)->(76.34,10.9)->(76.25,11.2)->(76.25,11.562).
XO jog: rip chain (76.75,11.125)->(75.9,9.7); new
 (76.75,11.125)->(76.78,10.7)->(76.78,10.0)->(76.3,9.85)
 ->(75.9,9.7).
"""
import sys
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

BOARD = 'hw/pdlvds_rx.exp251.kicad_pcb'
BOX = (58.0, 96.0, -30.0, 34.0)


def seg(net, x1, y1, x2, y2, hw=0.10, clr=0.2):
    return ('seg', net, (x1, y1, x2, y2, hw), clr)


def via(net, x, y, r=0.25, clr=0.2):
    return ('via', net, (x, y, r), clr)


def path_items(net, layer, pts, hw=0.10, clr=0.2):
    out = []
    for i in range(len(pts) - 1):
        out.append(seg(net, pts[i][0], pts[i][1], pts[i + 1][0],
                       pts[i + 1][1], hw, clr))
    return {layer: out}


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


pool = load_board_pool(BOARD)
print('faithful fragments XI:', len(fragments('XI', BOX)),
      'XO:', len(fragments('XO', BOX)))

try:
    ch = chain_segs(pool, 'XO', 0, (76.75, 11.125), (75.9, 9.7))
    rip_items(ch)
    print('XO chain ripped:', len(ch))
except SystemExit as e:
    print('XO chain FAILED', e)
N2 = {0: [seg('XO', 76.75, 11.125, 76.78, 10.70),
          seg('XO', 76.78, 10.70, 76.78, 10.00),
          seg('XO', 76.78, 10.00, 76.30, 9.85),
          seg('XO', 76.30, 9.85, 75.90, 9.70)], 1: [], 2: []}
add_items(N2)
print('XO fragments after jog:', len(fragments('XO', BOX)))
gate_items(N2, 'XO jog gate')

XI_V = {l: [via('XI', 74.0, 10.2)] for l in range(3)}
XI_B = path_items('XI', 2, [(74.0, 10.2), (74.45, 11.0),
                            (74.45, 12.3), (74.15, 13.0),
                            (74.15, 16.5), (74.6, 17.8),
                            (75.2, 18.4), (75.625, 18.625)])
XI_F = path_items('XI', 0, [(74.0, 10.2), (74.8, 10.15),
                            (75.6, 10.0), (76.2, 10.2),
                            (76.34, 10.5), (76.34, 10.9),
                            (76.25, 11.2), (76.25, 11.562)])
gate_items(XI_V, 'XI via gate')
gate_items(XI_B, 'XI B ride gate')
gate_items(XI_F, 'XI F feed gate')
add_items(XI_V); add_items(XI_B); add_items(XI_F)
print('XI fragments final:', len(fragments('XI', BOX)))
print('=== done ===')

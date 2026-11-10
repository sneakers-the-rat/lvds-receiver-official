"""t_az28: v13 XI design.
- CK In2 vertical re-lay with west jog at y9.4-11.0 (buys dive
  margin): rip the single seg (74.625,13.5)-(74.625,6.375);
  new (74.625,13.5)->(74.625,11.0)->(74.55,10.2)->(74.625,9.4)
  ->(74.625,6.375).
- XO F escape jog east x76.85 (as v12b).
- XI: via (75.2,10.2); F feed (75.2,10.2)->(75.75,10.05)
  ->(76.34,10.3)->(76.34,10.9)->(76.25,11.2)->(76.25,11.562);
  B ride (75.2,10.2)->(74.6,11.0)->(73.9,11.45)->(73.3,11.9)
  ->(72.9,12.15)->(72.5,12.2)->(70.6,12.25)->(70.0,12.4)
  ->(69.8,13.3)->(69.95,14.8)->(70.6,16.3)->(71.8,18.3)
  ->(72.9,18.6)->(74.3,18.55)->(75.625,18.625).
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
      'XO:', len(fragments('XO', BOX)),
      'CK:', len(fragments('ULPI_CK', BOX)))

# CK vertical re-lay
ck = [it for it in pool[1] if it[1] == 'ULPI_CK' and it[0] == 'seg'
      and abs(it[2][0] - 74.625) < 0.01 and abs(it[2][2] - 74.625) < 0.01
      and abs(it[2][1] - 13.5) < 0.01 and abs(it[2][3] - 6.375) < 0.01]
print('CK vertical segs found:', len(ck))
rip_items(ck)
NCK = {1: [seg('ULPI_CK', 74.625, 13.5, 74.625, 11.0, 0.125),
           seg('ULPI_CK', 74.625, 11.0, 74.55, 10.2, 0.125),
           seg('ULPI_CK', 74.55, 10.2, 74.625, 9.4, 0.125),
           seg('ULPI_CK', 74.625, 9.4, 74.625, 6.375, 0.125)]}
add_items(NCK)
print('CK fragments after re-lay:', len(fragments('ULPI_CK', BOX)))
gate_items(NCK, 'CK jog gate')

# XO jog v2
try:
    ch = chain_segs(pool, 'XO', 0, (76.75, 11.125), (75.9, 9.7))
    rip_items(ch)
    print('XO chain ripped:', len(ch))
except SystemExit as e:
    print('XO chain FAILED', e)
N2 = {0: [seg('XO', 76.75, 11.125, 76.80, 10.75),
          seg('XO', 76.80, 10.75, 76.85, 10.30),
          seg('XO', 76.85, 10.30, 76.85, 10.15),
          seg('XO', 76.85, 10.15, 76.30, 9.88),
          seg('XO', 76.30, 9.88, 75.90, 9.70)], 1: [], 2: []}
add_items(N2)
print('XO fragments after jog:', len(fragments('XO', BOX)))
gate_items(N2, 'XO jog gate')

XI_V = {l: [via('XI', 75.2, 10.2)] for l in range(3)}
XI_F = path_items('XI', 0, [(75.2, 10.2), (76.05, 10.12),
                            (76.38, 10.5), (76.38, 10.9),
                            (76.25, 11.2), (76.25, 11.562)])
XI_B = path_items('XI', 2, [(75.2, 10.2), (74.6, 10.85),
                            (72.9, 10.8), (71.5, 11.1),
                            (70.2, 11.65), (69.75, 12.35),
                            (69.6, 13.4), (69.75, 15.4),
                            (70.5, 17.0), (71.8, 18.3),
                            (72.9, 18.6), (74.3, 18.55),
                            (75.625, 18.625)])
gate_items(XI_V, 'XI via gate')
gate_items(XI_F, 'XI F feed gate')
gate_items(XI_B, 'XI B ride gate')
add_items(XI_V); add_items(XI_F); add_items(XI_B)
print('XI fragments final:', len(fragments('XI', BOX)))
print('=== done ===')

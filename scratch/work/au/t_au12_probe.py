"""t_au12: print DATA30's entry points; probe exact margins along
candidate NW entry lines on In2 in the settled model + CLK9."""
import sys, math, json
import numpy as np
sys.path.insert(0, 'scratch/work/au')
import t_au1_lib as U
import t_ai_lib as L
import pcbnew

J = json.load(open('scratch/work/as/journey30_CAP_DATA_DC.json'))
run = J['runs'][0]
pts = run['pts']
print('DATA30 L1 run first 30 pts:', pts[:30], flush=True)
print('DATA30 L1 pts near x=66:', [p for p in pts if 65.5 < p[0] < 66.5][:8],
      flush=True)

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
items_full = L.load_items(board)
PG_PRED = lambda l, it: l == 2 and it[1] == 'PG_3V3' \
    and 60 < U.item_centre(it)[0] < 70 and 0 < U.item_centre(it)[1] < 16
P3F_PRED = lambda l, it: l == 0 and it[1] == '+3V3D' \
    and it[0] in ('seg', 'via') \
    and 68 < U.item_centre(it)[0] < 77 and 19 < U.item_centre(it)[1] < 27
XO_PRED = lambda l, it: l == 1 and it[1] == 'XO' \
    and 66 < U.item_centre(it)[0] < 76 and 16 < U.item_centre(it)[1] < 23
pool = {l: [it for it in items_full[l] if not PG_PRED(l, it)
            and not P3F_PRED(l, it) and not XO_PRED(l, it)]
        for l in range(3)}
clk_items = U.journey_items('scratch/work/au/journey_au9_CLK.json',
                            'CAP_CLK')
union = {l: pool[l] + clk_items[l] for l in range(3)}

LINES = {
    'NW1': [(69.9, 3.18), (68.6, 4.3), (67.4, 5.6), (66.2, 7.2),
            (65.2, 8.8)],
    'NW2': [(69.9, 3.18), (68.9, 4.6), (67.8, 6.0), (66.6, 7.6),
            (65.4, 9.2)],
    'NW3': [(69.9, 3.18), (69.3, 4.9), (68.2, 6.6), (66.9, 8.3),
            (65.8, 9.9)],
    'W1': [(69.9, 3.18), (68.4, 3.6), (67.2, 4.6), (66.0, 6.2),
           (65.0, 8.0)],
}
for name, line in LINES.items():
    worst = (9.9, None, None)
    for a, b in zip(line, line[1:]):
        box = (min(a[0], b[0]) - 2.2, max(a[0], b[0]) + 2.2,
               min(a[1], b[1]) - 2.2, max(a[1], b[1]) + 2.2)
        local = L.in_box_pool(union, box, pad=0.6)
        m, w = L.seg_margin(1, a, b, 'CAP_DATA', 0.10, local[1])
        if m < worst[0]:
            worst = (m, (a, b), w)
    print(f'{name}: worst {worst[0]:+.3f} on {worst[1]} vs '
          f'{L.fmt_it(worst[2])}', flush=True)
print('done', flush=True)

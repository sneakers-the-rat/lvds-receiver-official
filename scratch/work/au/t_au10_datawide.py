"""t_au10: DATA widest + binds in the settled model
(full - PG - P3F - XObox + CLK-au9 items)."""
import sys, math, json, heapq
import numpy as np
sys.path.insert(0, 'scratch/work/au')
import t_au1_lib as U
import t_ai_lib as L
import pcbnew

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
comb = {l: pool[l] + clk_items[l] for l in range(3)}
G, AM = {}, {}
for l in range(3):
    G[l], AM[l], _ = U.build_field(comb[l], 'CAP_DATA')

bv, came, goal = U.widest(G, 'CAP_DATA')
print(f'DATA widest: {bv:+.3f}', flush=True)
binds = U.bind_items(G, AM, comb, 'CAP_DATA', (came, goal), bv, tol=0.01)
for (l, idx, it, desc) in binds:
    print(f'   bind L{l} {L.fmt_it(it)} @ {desc}', flush=True)
print('done', flush=True)

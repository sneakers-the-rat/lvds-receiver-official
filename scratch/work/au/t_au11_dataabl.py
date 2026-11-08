"""t_au11: DATA ablations in the settled model (full - PG - P3F -
XObox + CLK-au9). Candidates: THR_DAC vias (66.625,4.875) and
(64.875,6.625), GND stitch via (67.375,4.125), SCL In2 chain."""
import sys, math, json
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
base = {l: pool[l] + clk_items[l] for l in range(3)}

CANDS = {
    'THR66': lambda l, it: it[0] == 'via' and it[1] == 'THR_DAC'
        and abs(it[2][0] - 66.625) < 0.1 and abs(it[2][1] - 4.875) < 0.1,
    'THR64': lambda l, it: it[0] == 'via' and it[1] == 'THR_DAC'
        and abs(it[2][0] - 64.875) < 0.1 and abs(it[2][1] - 6.625) < 0.1,
    'GND67': lambda l, it: it[0] == 'via' and it[1] == 'GND'
        and abs(it[2][0] - 67.375) < 0.1 and abs(it[2][1] - 4.125) < 0.1,
    'SCLCH': lambda l, it: l == 1 and it[1] == 'I2C_SCL'
        and 62 < U.item_centre(it)[0] < 72
        and -1 < U.item_centre(it)[1] < 13,
}
for combo in ['THR66', 'THR64', 'GND67', 'THR66+THR64',
              'THR66+THR64+GND67', 'SCLCH', 'THR66+SCLCH']:
    names = combo.split('+')
    preds = [CANDS[n] for n in names]
    comb = {l: [it for it in base[l]
                if not any(p(l, it) for p in preds)] for l in range(3)}
    n = sum(len(base[l]) - len(comb[l]) for l in range(3))
    G = {}
    for l in range(3):
        G[l], _, _ = U.build_field(comb[l], 'CAP_DATA')
    bv, _, _ = U.widest(G, 'CAP_DATA')
    print(f'== {combo} ({n} items): DATA widest {bv:+.3f}', flush=True)
print('done', flush=True)

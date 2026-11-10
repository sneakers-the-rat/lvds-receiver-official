"""t_ba31: joint micro-optimization. C22 at (77.3,10.15)
rot 270 (pads + hop). STP southern: t_ba23 truncated at the
B descent's (76.2,10.5) point; transition via V on a grid;
B run (76.2,10.5)->V; In2 run V->(77.2,5.9); rest of t_ba23
kept. GND via G on a grid; stub pad2 (77.3,9.67)->G.
Score = min margin over {STP new items, GND via+stub, C22
hop}; report combos with min >= 0 (or the best few)."""
import sys, json, itertools
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

BOARD = 'hw/pdlvds_rx.exp252.kicad_pcb'
BOX = (58.0, 96.0, -30.0, 34.0)
LAYN = {0: 'F', 1: 'In2', 2: 'B'}
pool0 = load_board_pool(BOARD)

# base rip: STP southern chain + mid wander (t_ba23 rule)
rip = []
for l in range(3):
    for it in pool0[l]:
        if it[1] != 'ULPI_STP' or it[0] not in ('seg', 'via'):
            continue
        cc = C(it)
        if 75.5 <= cc[0] <= 78.5 and 7.0 <= cc[1] <= 14.0:
            rip.append(it)
        elif 0.5 < cc[1] < 7.5 and cc[0] > 72.0:
            rip.append(it)

ST = json.load(open('scratch/work/ba/design_stp_south.json'))
runs = ST['runs']
bpts = [tuple(p) for p in runs[0]['pts']]
i_cut = min(range(len(bpts)),
            key=lambda i: (bpts[i][0] - 76.2) ** 2 + (bpts[i][1] - 10.5) ** 2)
head = bpts[:i_cut + 1]
tail_runs = runs[2:]  # B, F, B runs after the In2 run
tail_vias = ST['vias'][1:]


def worst(items_by_layer, pool):
    w, wo = 9.9, None
    for l in range(3):
        for it in items_by_layer.get(l, []):
            for o in pool[l]:
                if o[1] == it[1]:
                    continue
                cc, ci = C(o), C(it)
                if abs(cc[0] - ci[0]) > 4 or abs(cc[1] - ci[1]) > 4:
                    continue
                m = item_margin(l, it, [o])
                if m < w:
                    w, wo = m, (LAYN[l], o[1])
    return w, wo


def build_stp(vx, vy):
    """items for the adjusted STP south given transition via."""
    r = [{'layer': 2, 'pts': [list(p) for p in head] +
          [[vx, vy]]},
         {'layer': 1, 'pts': [[vx, vy], [77.2, 5.9]]}] + \
        [dict(x) for x in tail_runs]
    vias = [[vx, vy]] + tail_vias
    return journey_items_dense({'runs': r, 'vias': vias},
                               'ULPI_STP', hw=0.10)


HOP = {0: [('seg', 'PHY_1V8', (77.3, 10.63, 77.90, 10.08, 0.10), 0.25)]}
PADS = {0: [('pad', 'PHY_1V8', (77.3, 10.63, 0.31, 0.28, 0.0), 0.25),
            ('pad', 'GND', (77.3, 9.67, 0.31, 0.28, 0.0), 0.2)]}

results = []
for vx in [76.9, 77.0, 77.1, 77.2, 77.3, 77.4, 77.5]:
    for vy in [9.5, 9.6, 9.7, 9.8, 9.9, 10.0, 10.1]:
        pool = load_board_pool(BOARD)
        rip_items([it for it in rip])
        JI = build_stp(vx, vy)
        w_stp, wo_stp = worst(JI, pool)
        if w_stp < 0:
            continue
        add_items(JI)
        for gx in [76.7, 76.8, 76.9, 77.0, 77.1]:
            for gy in [9.5, 9.6, 9.7, 9.8]:
                GV = {l: [('via', 'GND', (gx, gy, 0.25), 0.2)]
                      for l in range(3)}
                w_gv, _ = worst(GV, pool)
                if w_gv < 0:
                    continue
                GS = {0: [('seg', 'GND', (77.3, 9.67, gx, gy, 0.10), 0.2)]}
                w_gs, _ = worst(GS, pool)
                if w_gs < 0:
                    continue
                w_hop, _ = worst(HOP, pool)
                w_pad, _ = worst(PADS, pool)
                results.append((round(min(w_stp, w_gv, w_gs, w_hop,
                                          w_pad), 3),
                                (vx, vy), (gx, gy),
                                round(w_stp, 3), round(w_gv, 3),
                                round(w_gs, 3), round(w_hop, 3),
                                round(w_pad, 3)))
results.sort(reverse=True)
print(f'{len(results)} clean combos; best 8:')
for r in results[:8]:
    print('  ', r)
print('=== done ===')

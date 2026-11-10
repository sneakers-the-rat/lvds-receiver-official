"""t_ba33: two routes to a clean joint config.
A) t_ba23 STP placed; GND via grid EAST of pad2 (77.3,9.67):
   x[77.4,78.15] y[9.35,10.0]; gate via + stub.
B) STP4b: transition via (76.35,9.05), B descent extended
   (76.2,10.5)->(76.35,9.05), In2 straight (76.35,9.05)->
   (77.2,5.9), t_ba23 tail; gate STP, then GND via
   (76.95,9.6) + stub with STP4b placed.
C22 pads/hop already proven at (77.3,10.15) r270 (t_ba32)."""
import sys, json
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

BOARD = 'hw/pdlvds_rx.exp252.kicad_pcb'
BOX = (58.0, 96.0, -30.0, 34.0)
LAYN = {0: 'F', 1: 'In2', 2: 'B'}


def base_pool():
    pool = load_board_pool(BOARD)
    rip = []
    for l in range(3):
        for it in pool[l]:
            if it[1] != 'ULPI_STP' or it[0] not in ('seg', 'via'):
                continue
            cc = C(it)
            if 75.5 <= cc[0] <= 78.5 and 7.0 <= cc[1] <= 14.0:
                rip.append(it)
            elif 0.5 < cc[1] < 7.5 and cc[0] > 72.0:
                rip.append(it)
    rip_items(rip)
    return pool


def gate(pool, items_by_layer, label, quiet=False):
    ps = []
    for l in range(3):
        for it in items_by_layer.get(l, []):
            for o in pool[l]:
                if o[1] == it[1]:
                    continue
                cc, ci = C(o), C(it)
                if abs(cc[0] - ci[0]) > 4 or abs(cc[1] - ci[1]) > 4:
                    continue
                m = item_margin(l, it, [o])
                if m < 0.15:
                    ps.append((round(m, 3), LAYN[l], o[1],
                               (round(ci[0], 2), round(ci[1], 2)),
                               (round(cc[0], 2), round(cc[1], 2))))
    ps.sort(key=lambda t: t[0])
    n = sum(1 for p in ps if p[0] < 0)
    if not quiet:
        print(f'{label}: neg {n}, worst 6: {ps[:6]}')
    return n, (ps[0][0] if ps else 9.9)


ST = json.load(open('scratch/work/ba/design_stp_south.json'))
runs, bpts = ST['runs'], [tuple(p) for p in ST['runs'][0]['pts']]
i_cut = min(range(len(bpts)),
            key=lambda i: (bpts[i][0] - 76.2) ** 2 + (bpts[i][1] - 10.5) ** 2)
head = [list(p) for p in bpts[:i_cut + 1]]

# ---- variant A ----
pool = base_pool()
add_items(journey_items_dense(ST, 'ULPI_STP', hw=0.10))
print('--- A: t_ba23 placed, GND via east grid ---')
best = []
for i in range(16):
    for j in range(14):
        vx, vy = 77.4 + i * 0.05, 9.35 + j * 0.05
        gv = {l: [('via', 'GND', (vx, vy, 0.25), 0.2)] for l in range(3)}
        n, w = gate(pool, gv, '', quiet=True)
        if n:
            continue
        gs = {0: [('seg', 'GND', (77.3, 9.67, vx, vy, 0.10), 0.2)]}
        n2, w2 = gate(pool, gs, '', quiet=True)
        if n2:
            continue
        best.append((round(min(w, w2), 3), (round(vx, 2), round(vy, 2))))
best.sort(reverse=True)
print('A clean GND vias:', best[:5])

# ---- variant B ----
pool = base_pool()
runsB = [{'layer': 2, 'pts': head + [[76.35, 9.05]]},
         {'layer': 1, 'pts': [[76.35, 9.05], [77.2, 5.9]]}] + runs[2:]
STB = {'runs': runsB, 'vias': [[76.35, 9.05]] + ST['vias'][1:]}
JIB = journey_items_dense(STB, 'ULPI_STP', hw=0.10)
n, w = gate(pool, JIB, 'B: STP4b')
if n == 0:
    json.dump(STB, open('scratch/work/ba/design_stp_south4.json', 'w'))
    add_items(JIB)
    print('B: STP4b placed; frags', len(fragments('ULPI_STP', BOX)))
    gate(pool, {l: [('via', 'GND', (76.95, 9.60, 0.25), 0.2)]
                for l in range(3)}, 'B: GND via (76.95,9.6)')
    gate(pool, {0: [('seg', 'GND', (77.3, 9.67, 76.95, 9.60, 0.10), 0.2)]},
         'B: GND stub')
    gate(pool, {0: [('seg', 'PHY_1V8', (77.3, 10.63, 77.90, 10.08, 0.10),
                     0.25)]}, 'B: pad1 hop re-gate')
print('=== done ===')

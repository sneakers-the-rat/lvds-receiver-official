"""t_ba55: XI full joint design on exp253 (model).
Rips: STP western B excursion; STP7 B descent (re-lay at
x76.48); XO F staircase foot (jog). XI: B west channel
(74.9) -> via (74.9,12.85) -> In2 diagonal -> pocket via
(grid-optimised in the four-fence lens) -> F legs -> U7.28.
Gates at every step; designs saved if clean."""
import sys, json
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

BOARD = 'hw/pdlvds_rx.exp253.kicad_pcb'
BOX = (58.0, 96.0, -30.0, 34.0)
LAYN = {0: 'F', 1: 'In2', 2: 'B'}
pool = load_board_pool(BOARD)


def gate(items_by_layer, label, nets, thr=0.15):
    ps = []
    for l in range(3):
        for it in items_by_layer.get(l, []):
            for o in pool[l]:
                if o[1] in nets:
                    continue
                cc, ci = C(o), C(it)
                if abs(cc[0] - ci[0]) > 3.5 or abs(cc[1] - ci[1]) > 3.5:
                    continue
                m = item_margin(l, it, [o])
                if m < thr:
                    ps.append((round(m, 3), LAYN[l], o[1],
                               (round(ci[0], 2), round(ci[1], 2)),
                               (round(cc[0], 2), round(cc[1], 2))))
    ps.sort(key=lambda t: t[0])
    print(f'{label}: neg {sum(1 for p in ps if p[0] < 0)}, '
          f'worst 6: {ps[:6]}')
    return ps


# 1. excursion
rip = [it for it in pool[2]
       if it[1] == 'ULPI_STP' and it[0] == 'seg'
       and 74.3 <= C(it)[0] <= 76.0 and 13.4 <= C(it)[1] <= 17.2]
rip_items(rip)
print(f'excursion ripped {len(rip)}')

# 2. STP7 descent re-lay
ripd = [it for it in pool[2]
        if it[1] == 'ULPI_STP' and it[0] == 'seg'
        and 76.1 <= C(it)[0] <= 76.35 and 9.2 <= C(it)[1] <= 13.6]
print(f'descent rip: {len(ripd)} segs')
rip_items(ripd)
DESC = {2: [('seg', 'ULPI_STP', (76.10, 13.50, 76.48, 12.55, 0.10), 0.2),
            ('seg', 'ULPI_STP', (76.48, 12.55, 76.48, 10.15, 0.10), 0.2),
            ('seg', 'ULPI_STP', (76.48, 10.15, 76.445, 9.03, 0.10), 0.2)],
        0: [], 1: []}
gate(DESC, 'descent relay', ('ULPI_STP',))
add_items(DESC)
print('STP frags:', len(fragments('ULPI_STP', BOX)))

# 3. XO foot jog
ripx = [it for it in pool[0]
        if it[1] == 'XO' and it[0] == 'seg'
        and 75.85 <= C(it)[0] <= 76.52 and 9.6 <= C(it)[1] <= 10.28]
print(f'XO foot rip: {len(ripx)} segs')
rip_items(ripx)
print('XO frags mid:', len(fragments('XO', BOX)))
JOG = {0: [('seg', 'XO', (75.90, 9.70, 76.28, 10.0, 0.10), 0.2),
           ('seg', 'XO', (76.28, 10.0, 76.52, 10.22, 0.10), 0.2)],
       1: [], 2: []}
gate(JOG, 'XO jog', ('XO',))
add_items(JOG)
print('XO frags after:', len(fragments('XO', BOX)))

# 4. pocket via grid optimisation: fences = XO (F), 1V8A (F+B),
#    STP descent (B), +3V3A (In2). Score = min margin over
#    all layers vs all nets except XI.
best = None
for gx in range(7586, 7601, 2):
    for gy in range(1030, 1047, 2):
        x, y = gx / 100.0, gy / 100.0
        worst = 9.9
        for l in range(3):
            it = ('via', 'XI', (x, y, 0.25), 0.2)
            for o in pool[l]:
                if o[1] == 'XI':
                    continue
                cc = C(o)
                if abs(cc[0] - x) > 2.0 or abs(cc[1] - y) > 2.0:
                    continue
                m = item_margin(l, it, [o])
                if m < worst:
                    worst = m
        if best is None or worst > best[0]:
            best = (worst, x, y)
print(f'pocket via optimum: margin {best[0]:+.3f} at '
      f'({best[1]:.2f},{best[2]:.2f})')
VX, VY = best[1], best[2]

# 5. XI journey
XIB = {2: [('seg', 'XI', (75.625, 18.625, 74.95, 18.35, 0.10), 0.2),
           ('seg', 'XI', (74.95, 18.35, 74.9, 17.0, 0.10), 0.2),
           ('seg', 'XI', (74.9, 17.0, 74.9, 12.85, 0.10), 0.2)],
       0: [], 1: []}
gate(XIB, 'XI B channel', ('XI',))
add_items(XIB)
V1 = {l: [('via', 'XI', (74.9, 12.85, 0.25), 0.2)] for l in range(3)}
gate(V1, 'XI via1 (74.9,12.85)', ('XI',))
add_items(V1)
XI2 = {1: [('seg', 'XI', (74.9, 12.85, 75.35, 12.2, 0.10), 0.2),
           ('seg', 'XI', (75.35, 12.2, VX, VY, 0.10), 0.2)],
       0: [], 2: []}
gate(XI2, 'XI In2 span', ('XI',))
add_items(XI2)
V2 = {l: [('via', 'XI', (VX, VY, 0.25), 0.2)] for l in range(3)}
gate(V2, 'XI pocket via', ('XI',))
add_items(V2)
XIF = {0: [('seg', 'XI', (VX, VY, 76.15, 10.8, 0.10), 0.2),
           ('seg', 'XI', (76.15, 10.8, 76.25, 11.35, 0.10), 0.2)],
       1: [], 2: []}
gate(XIF, 'XI F legs', ('XI',))
add_items(XIF)
fr = fragments('XI', BOX)
print('XI frags final:', len(fr))
for f in fr:
    print('   terms:', sorted(f['terms'])[:6])
json.dump({'pocket_via': [VX, VY], 'pocket_margin': best[0]},
          open('scratch/work/ba/design_xi_pocket.json', 'w'))
print('=== done ===')

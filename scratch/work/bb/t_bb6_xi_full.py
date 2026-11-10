"""t_bb6: XI FULL joint design on exp254 (model). Moves A+B+C from
t_bb5, pocket via (75.80,10.28) d0.5, corridor via (75.20,12.85),
hand B legs from arc via, A* In2 ride corridor->pocket, F leg
pocket->U7.28 (76.25,11.40). Gates every stage; saves design JSON
to scratch/work/bb/design_xi_bb.json if complete."""
import sys, json
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

BOARD = 'hw/pdlvds_rx.exp254.kicad_pcb'
BOX = (58.0, 96.0, -30.0, 34.0)
LAYN = {0: 'F', 1: 'In2', 2: 'B'}
pool = load_board_pool(BOARD)

def gate_items(items_by_layer, label, skip_nets, thr=0.15):
    ps = []
    for l in range(3):
        for it in items_by_layer.get(l, []):
            for o in pool[l]:
                if o[1] in skip_nets:
                    continue
                oc, ic = C(o), C(it)
                if abs(oc[0] - ic[0]) > 3.5 or abs(oc[1] - ic[1]) > 3.5:
                    continue
                m = item_margin(l, it, [o])
                if m < thr:
                    ps.append((round(m, 3), LAYN[l], o))
    ps.sort(key=lambda t: t[0])
    print(f'{label}: worst 6 {[(p[0], p[1], p[2]) for p in ps[:6]]}')
    return ps

def gate_via(x, y, net, label, r=0.25):
    cand = ('via', net, (x, y, r), 0.2)
    ps = []
    for l in range(3):
        for o in pool[l]:
            if o[1] == net:
                continue
            oc = C(o)
            if abs(oc[0] - x) > 3.0 or abs(oc[1] - y) > 3.0:
                continue
            m = item_margin(l, cand, [o])
            if m < 0.15:
                ps.append((round(m, 3), LAYN[l], o))
    ps.sort(key=lambda t: t[0])
    print(f'{label}: worst 6 {[(p[0], p[1], p[2]) for p in ps[:6]]}')
    return ps

def add_via(net, x, y, clr=0.2, r=0.25):
    v = ('via', net, (x, y, r), clr)
    add_items({0: [v], 1: [v], 2: [v]})
    return v

# ---- Move A ----
ripA = [it for it in pool[2]
        if it[1] == 'ULPI_STP' and it[0] == 'seg'
        and 75.9 <= C(it)[0] <= 76.5 and 9.2 <= C(it)[1] <= 13.5]
rip_items(ripA)
newA = {2: [('seg', 'ULPI_STP', (76.44, 9.03, 76.45, 12.90, 0.1), 0.2),
            ('seg', 'ULPI_STP', (76.45, 12.90, 76.05, 13.45, 0.1), 0.2)]}
gate_items(newA, 'A gate', ('ULPI_STP',))
add_items(newA)

# ---- Move B ----
ripB = []
for it in pool[1]:
    if it[1] != 'ULPI_CK' or it[0] != 'seg':
        continue
    d = it[2]
    if abs(d[0] - 74.625) < 0.02 and abs(d[2] - 74.625) < 0.02 and \
       min(d[1], d[3]) <= 9.40 and max(d[1], d[3]) >= 11.00:
        ripB.append(it)
rip_items(ripB)
newB = {1: [('seg', 'ULPI_CK', (74.625, 6.375, 74.625, 9.40, 0.125), 0.2),
            ('seg', 'ULPI_CK', (74.625, 9.40, 74.32, 10.20, 0.125), 0.2),
            ('seg', 'ULPI_CK', (74.32, 10.20, 74.625, 11.00, 0.125), 0.2),
            ('seg', 'ULPI_CK', (74.625, 11.00, 74.625, 13.50, 0.125), 0.2)]}
gate_items(newB, 'B gate', ('ULPI_CK',))
add_items(newB)

# ---- Move C ----
ripC = []
for it in list(pool[0]):
    if it[1] == 'PHY_1V8A' and it[0] == 'seg':
        d = it[2]
        if abs(d[0] - 75.72) < 0.05 and abs(d[1] - 11.0) < 0.05 and \
           abs(d[2] - 75.45) < 0.05 and abs(d[3] - 10.6) < 0.05:
            ripC.append(it)
for it in list(pool[2]):
    if it[1] == 'PHY_1V8A' and it[0] == 'seg':
        d = it[2]
        if abs(d[0] - 75.45) < 0.05 and abs(d[1] - 10.6) < 0.05:
            ripC.append(it)
ripC.append(('via', 'PHY_1V8A', (75.45, 10.6, 0.25), 0.25))
rip_items(ripC)
NV = (74.99, 10.28)
newC = {0: [('seg', 'PHY_1V8A', (75.72, 11.00, NV[0], NV[1], 0.1), 0.25)],
        2: [('seg', 'PHY_1V8A', (NV[0], NV[1], 75.00, 11.50, 0.1), 0.25)]}
gate_items(newC, 'C gate', ('PHY_1V8A',))
add_items(newC)
add_via('PHY_1V8A', NV[0], NV[1], clr=0.25)
gate_via(NV[0], NV[1], 'PHY_1V8A', 'C via gate')

# ---- XI: pocket via + F leg ----
PV = (75.80, 10.28)
gate_via(PV[0], PV[1], 'XI', 'pocket via gate')
add_via('XI', PV[0], PV[1])
fleg = {0: [('seg', 'XI', (PV[0], PV[1], 76.25, 11.40, 0.1), 0.2)]}
gate_items(fleg, 'F leg gate', ('XI',))
add_items(fleg)

# ---- XI: corridor via + hand B legs ----
CV = (75.20, 12.85)
gate_via(CV[0], CV[1], 'XI', 'corridor via gate')
add_via('XI', CV[0], CV[1])
blegs = {2: [('seg', 'XI', (75.625, 18.625, 74.85, 17.95, 0.1), 0.2),
             ('seg', 'XI', (74.85, 17.95, 74.85, 12.90, 0.1), 0.2),
             ('seg', 'XI', (74.85, 12.90, CV[0], CV[1], 0.1), 0.2)]}
gate_items(blegs, 'B legs gate', ('XI',))
add_items(blegs)

# ---- XI: A* In2 ride corridor -> pocket ----
astar = make_astar((70.0, 80.0, 6.0, 22.0), 0.05)
rr = astar('XI', ((1,), CV[0], CV[1]), (1, PV[0], PV[1]), 0.10)
print('XI In2 ride:', 'FOUND vias=' + str(rr['vias']) if rr else 'NONE')
if rr:
    JI = journey_items_dense(rr, 'XI', hw=0.10)
    gate_items(JI, 'In2 ride gate', ('XI',))
    add_items(JI)
    json.dump({'moves': 'A/B/C as t_bb6', 'pocket_via': PV, 'corridor_via': CV,
               'ride': rr}, open('scratch/work/bb/design_xi_bb.json', 'w'), default=str)
    print('design saved')

for n in ('ULPI_STP', 'PHY_1V8A', 'ULPI_CK', 'XI', 'ULPI_DIR', '+3V3A', 'XO'):
    print(f'frags {n}: {len(fragments(n, BOX))}')

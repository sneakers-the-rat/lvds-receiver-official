"""t_bb5: XI joint design v3 on exp254 (model only).
Fixes vs t_bb4: old notch via ripped with its exact 4-tuple;
notch v3 via moved to (74.99,10.28). Moves A (STP descent east) and
B (CK In2 jog west) as before. Then pocket grid, then XI arrival:
hand B legs arc->corridor via (75.20,12.85); A* In2 ride corridor->
pocket via; F leg pocket via->U7.28 pad point (76.25,11.40).
All gates printed; frag sigs incl. terminals for every touched net."""
import sys, json
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

BOARD = 'hw/pdlvds_rx.exp254.kicad_pcb'
BOX = (58.0, 96.0, -30.0, 34.0)
LAYN = {0: 'F', 1: 'In2', 2: 'B'}
pool = load_board_pool(BOARD)

def fragsig(net):
    fr = fragments(net, BOX)
    sig = []
    for f in fr:
        if isinstance(f, dict):
            terms = tuple(sorted(str(t) for t in f.get('terminals', [])))
            sig.append((f.get('n', len(f)), terms))
        else:
            sig.append((len(f), ()))
    return sorted(sig, key=str)

NETS = ('ULPI_STP', 'PHY_1V8A', 'ULPI_CK', 'XI', '+3V3A', 'XO', 'ULPI_DIR')
base = {n: fragsig(n) for n in NETS}
for n, s in base.items():
    print(f'base frags {n}: {len(s)} :: {s}')

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

# ---- Move A: STP descent east ----
ripA = [it for it in pool[2]
        if it[1] == 'ULPI_STP' and it[0] == 'seg'
        and 75.9 <= C(it)[0] <= 76.5 and 9.2 <= C(it)[1] <= 13.5]
rip_items(ripA)
newA = {2: [('seg', 'ULPI_STP', (76.44, 9.03, 76.45, 12.90, 0.1), 0.2),
            ('seg', 'ULPI_STP', (76.45, 12.90, 76.05, 13.45, 0.1), 0.2)]}
gate_items(newA, 'Move A gate', ('ULPI_STP',))
add_items(newA)
print(f'Move A: ripped {len(ripA)}, STP frags {len(fragments("ULPI_STP", BOX))} (base {len(base["ULPI_STP"])})')

# ---- Move B: CK In2 jog west ----
ripB = []
for it in pool[1]:
    if it[1] != 'ULPI_CK' or it[0] != 'seg':
        continue
    d = it[2]
    if abs(d[0] - 74.625) < 0.02 and abs(d[2] - 74.625) < 0.02 and \
       min(d[1], d[3]) <= 9.40 and max(d[1], d[3]) >= 11.00:
        ripB.append(it)
print(f'Move B rip: {len(ripB)} {[it[2] for it in ripB]}')
rip_items(ripB)
newB = {1: [('seg', 'ULPI_CK', (74.625, 6.375, 74.625, 9.40, 0.125), 0.2),
            ('seg', 'ULPI_CK', (74.625, 9.40, 74.32, 10.20, 0.125), 0.2),
            ('seg', 'ULPI_CK', (74.32, 10.20, 74.625, 11.00, 0.125), 0.2),
            ('seg', 'ULPI_CK', (74.625, 11.00, 74.625, 13.50, 0.125), 0.2)]}
gate_items(newB, 'Move B gate', ('ULPI_CK',))
add_items(newB)
print('CK frags:', len(fragments('ULPI_CK', BOX)), 'base', len(base['ULPI_CK']))

# ---- Move C: 1V8A notch v3 at (74.99,10.28) ----
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
old_via = ('via', 'PHY_1V8A', (75.45, 10.6, 0.25), 0.25)
assert old_via in pool[0], 'old notch via tuple not found'
ripC.append(old_via)
print(f'Move C rip: {len(ripC)} items')
rip_items(ripC)
NV = (74.99, 10.28)
newC = {0: [('seg', 'PHY_1V8A', (75.72, 11.00, NV[0], NV[1], 0.1), 0.25)],
        2: [('seg', 'PHY_1V8A', (NV[0], NV[1], 75.00, 11.50, 0.1), 0.25)]}
gate_items(newC, 'Move C segs gate', ('PHY_1V8A',))
add_items(newC)
_v = ('via', 'PHY_1V8A', (NV[0], NV[1], 0.25), 0.25)
add_items({0: [_v], 1: [_v], 2: [_v]})
gate_via(NV[0], NV[1], 'PHY_1V8A', 'Move C via gate')
print('1V8A frags:', len(fragments('PHY_1V8A', BOX)), 'base', len(base['PHY_1V8A']),
      'sig_equal:', fragsig('PHY_1V8A') == base['PHY_1V8A'])

# ---- pocket grid v4 ----
print('--- pocket grid v4 ---')
best = []
y = 9.90
while y <= 10.901:
    x = 75.55
    while x <= 76.201:
        cand = ('via', 'XI', (x, y, 0.25), 0.2)
        worst = (9.9, None, None)
        for l in range(3):
            for o in pool[l]:
                if o[1] == 'XI':
                    continue
                oc = C(o)
                if abs(oc[0] - x) > 3.0 or abs(oc[1] - y) > 3.0:
                    continue
                m = item_margin(l, cand, [o])
                if m < worst[0]:
                    worst = (m, LAYN[l], o)
        best.append((round(worst[0], 3), round(x, 3), round(y, 3), worst[1], worst[2]))
        x += 0.025
    y += 0.025
best.sort(key=lambda t: -t[0])
for row in best[:8]:
    print('  ', row)
json.dump({'best': best[:8]}, open('scratch/work/bb/xi_grid_v4.json', 'w'), default=str)

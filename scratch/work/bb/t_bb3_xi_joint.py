"""t_bb3: XI joint design on exp254 (model only).
Moves:
 A. STP B descent re-lay east: rip densified staircase x[75.9,76.5]
    y[9.2,13.5]; lay B (76.44,9.03)->(76.45,12.90)->(76.05,13.45).
 B. CK In2 vertical jog west: rip span x74.62 y[9.4,11.0]; lay
    (74.62,9.40)->(74.32,10.20)->(74.62,11.00).
 C. 1V8A notch v3: rip via (75.45,10.6) + F stub + first B head seg;
    via (74.95,10.20); F stub (75.72,11.00)->(74.95,10.20);
    B head (74.95,10.20)->(75.00,11.50).
Then re-grid the XI pocket via; gate everything; check fragments
(incl. terminals) for ULPI_STP / PHY_1V8A / ULPI_CK / XI.
Extra censuses first: In2 west of CK vertical; B east column;
PHY_1V8 items in box."""
import sys, json
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

BOARD = 'hw/pdlvds_rx.exp254.kicad_pcb'
BOX = (58.0, 96.0, -30.0, 34.0)
LAYN = {0: 'F', 1: 'In2', 2: 'B'}
pool = load_board_pool(BOARD)

print('--- In2 census x[72.6,74.62] y[8.0,13.0] (all nets) ---')
for it in pool[1]:
    cc = C(it)
    if 72.6 <= cc[0] <= 74.62 and 8.0 <= cc[1] <= 13.0:
        d = it[2]
        if it[0] == 'seg':
            print(f'  {it[1]:9} seg ({d[0]:.2f},{d[1]:.2f})->({d[2]:.2f},{d[3]:.2f})')
        elif it[0] == 'via':
            print(f'  {it[1]:9} via ({d[0]:.2f},{d[1]:.2f}) r{d[2]:.2f}')
print('--- B census x[76.3,77.3] y[8.8,14.2] (all nets) ---')
for it in pool[2]:
    cc = C(it)
    if 76.3 <= cc[0] <= 77.3 and 8.8 <= cc[1] <= 14.2:
        d = it[2]
        if it[0] == 'seg':
            print(f'  {it[1]:9} seg ({d[0]:.2f},{d[1]:.2f})->({d[2]:.2f},{d[3]:.2f})')
        elif it[0] == 'via':
            print(f'  {it[1]:9} via ({d[0]:.2f},{d[1]:.2f}) r{d[2]:.2f}')
        else:
            print(f'  {it[1]:9} {it[0]} ({d[0]:.2f},{d[1]:.2f})')
print('--- F census x[76.3,77.3] y[8.8,14.2] (all nets) ---')
for it in pool[0]:
    cc = C(it)
    if 76.3 <= cc[0] <= 77.3 and 8.8 <= cc[1] <= 14.2:
        d = it[2]
        if it[0] == 'seg':
            print(f'  {it[1]:9} seg ({d[0]:.2f},{d[1]:.2f})->({d[2]:.2f},{d[3]:.2f})')
        elif it[0] == 'via':
            print(f'  {it[1]:9} via ({d[0]:.2f},{d[1]:.2f}) r{d[2]:.2f}')
        else:
            print(f'  {it[1]:9} {it[0]} ({d[0]:.2f},{d[1]:.2f})')

def fragsig(net):
    fr = fragments(net, BOX)
    sig = []
    for f in fr:
        terms = tuple(sorted(str(t) for t in f.get('terminals', []))) if isinstance(f, dict) else ()
        sig.append((len(f), terms))
    return sorted(sig)

base = {n: fragsig(n) for n in ('ULPI_STP', 'PHY_1V8A', 'ULPI_CK', 'XI')}
for n, s in base.items():
    print(f'base frags {n}: {len(s)}')

def gate_new(items_by_layer, label, skip_nets):
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
                if m < 0.15:
                    ps.append((round(m, 3), LAYN[l], o[1],
                               (round(ic[0], 2), round(ic[1], 2)),
                               (round(oc[0], 2), round(oc[1], 2))))
    ps.sort(key=lambda t: t[0])
    print(f'{label}: worst 5 {ps[:5]}')
    return ps

def seg(l, net, a, b, w=0.1):
    return (l, ('seg', net, (a[0], a[1], b[0], b[1], w)))

def via(net, x, y, r=0.25):
    return ('via', net, (x, y, r))

# ---- Move A: STP descent east ----
ripA = []
for it in pool[2]:
    if it[1] != 'ULPI_STP' or it[0] != 'seg':
        continue
    cc = C(it)
    if 75.9 <= cc[0] <= 76.5 and 9.2 <= cc[1] <= 13.5:
        ripA.append(it)
print(f'Move A rip: {len(ripA)} STP B segs')
rip_items(ripA)
newA = {2: [('seg', 'ULPI_STP', (76.44, 9.03, 76.45, 12.90, 0.1)),
            ('seg', 'ULPI_STP', (76.45, 12.90, 76.05, 13.45, 0.1))]}
gate_new(newA, 'Move A gate', ('ULPI_STP',))
add_items(newA)
print('STP frags after A:', len(fragments('ULPI_STP', BOX)), 'base', len(base['ULPI_STP']))

# ---- Move B: CK In2 jog west ----
ripB = []
for it in pool[1]:
    if it[1] != 'ULPI_CK' or it[0] != 'seg':
        continue
    d = it[2]
    if abs(d[0] - 74.62) < 0.01 and abs(d[2] - 74.62) < 0.01 and \
       max(d[1], d[3]) <= 11.01 and min(d[1], d[3]) >= 9.39:
        ripB.append(it)
print(f'Move B rip: {len(ripB)} CK In2 segs')
for it in ripB:
    print('   ', it[2])
rip_items(ripB)
newB = {1: [('seg', 'ULPI_CK', (74.62, 9.40, 74.32, 10.20, 0.125)),
            ('seg', 'ULPI_CK', (74.32, 10.20, 74.62, 11.00, 0.125))]}
gate_new(newB, 'Move B gate', ('ULPI_CK',))
add_items(newB)
print('CK frags after B:', len(fragments('ULPI_CK', BOX)), 'base', len(base['ULPI_CK']))

# ---- Move C: 1V8A notch v3 ----
ripC = []
for l in range(3):
    for it in pool[l]:
        if it[1] != 'PHY_1V8A':
            continue
        cc = C(it)
        if abs(cc[0] - 75.45) < 0.3 and abs(cc[1] - 10.6) < 0.3:
            ripC.append((l, it))
for it in pool[0]:
    if it[1] == 'PHY_1V8A' and it[0] == 'seg':
        d = it[2]
        if (abs(d[0] - 75.72) < 0.05 and abs(d[1] - 11.0) < 0.05) or \
           (abs(d[2] - 75.72) < 0.05 and abs(d[3] - 11.0) < 0.05):
            ripC.append((0, it))
for it in pool[2]:
    if it[1] == 'PHY_1V8A' and it[0] == 'seg':
        d = it[2]
        if abs(d[0] - 75.45) < 0.05 and abs(d[1] - 10.6) < 0.05:
            ripC.append((2, it))
print(f'Move C rip: {len(ripC)} items')
rip_items([it for _, it in ripC])
newC = {0: [('seg', 'PHY_1V8A', (75.72, 11.00, 74.95, 10.20, 0.1))],
        2: [('seg', 'PHY_1V8A', (74.95, 10.20, 75.00, 11.50, 0.1))]}
_v = ('via', 'PHY_1V8A', (74.95, 10.20, 0.25))
add_items({0: [_v], 1: [_v], 2: [_v]})
gate_new(newC, 'Move C segs gate', ('PHY_1V8A',))
add_items(newC)
cand = ('via', 'PHY_1V8A', (74.95, 10.20, 0.25))
ps = []
for l in range(3):
    for o in pool[l]:
        if o[1] == 'PHY_1V8A':
            continue
        oc = C(o)
        if abs(oc[0] - 74.95) > 3.0 or abs(oc[1] - 10.20) > 3.0:
            continue
        m = item_margin(l, cand, [o])
        if m < 0.15:
            ps.append((round(m, 3), LAYN[l], o[1], (round(oc[0], 2), round(oc[1], 2))))
ps.sort(key=lambda t: t[0])
print('Move C via gate worst 5:', ps[:5])
print('1V8A frags after C:', len(fragments('PHY_1V8A', BOX)), 'base', len(base['PHY_1V8A']))

# ---- Re-grid XI pocket via on the moved fences ----
print('--- pocket grid v2 (via d0.5) ---')
best = []
y = 9.90
while y <= 10.901:
    x = 75.55
    while x <= 76.201:
        cand = ('via', 'XI', (x, y, 0.25))
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
        best.append((round(worst[0], 3), round(x, 3), round(y, 3), worst[1],
                     worst[2][1] if worst[2] else None,
                     (round(C(worst[2])[0], 2), round(C(worst[2])[1], 2)) if worst[2] else None))
        x += 0.025
    y += 0.025
best.sort(reverse=True)
for row in best[:10]:
    print('  ', row)

for n in ('ULPI_STP', 'PHY_1V8A', 'ULPI_CK'):
    now = fragsig(n)
    print(f'frag check {n}: base {len(base[n])} now {len(now)} sig_equal={now == base[n]}')

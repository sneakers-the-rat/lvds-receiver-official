"""t_bb15: XI design v8 (model, from exp254).
1) Verify 1V8A west tail (B segs x[70.0,73.35] y[11.8,12.9]) is a
   tail: frags + terminal set before/after rip.
2) Moves A2 (STP descent jogged), B (CK jog), C (notch v3),
   XO final re-lay, PV (75.86,10.34) + F leg via (76.2,10.95),
   west ride (all B). DIR untouched."""
import sys
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

BOARD = 'hw/pdlvds_rx.exp254.kicad_pcb'
BOX = (58.0, 96.0, -30.0, 34.0)
LAYN = {0: 'F', 1: 'In2', 2: 'B'}
pool = load_board_pool(BOARD)

def gate_items(items_by_layer, label, skip_nets, thr=0.12):
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
                    ps.append((round(m, 3), LAYN[l], o[1]))
    ps.sort(key=lambda t: t[0])
    print(f'{label}: worst 8 {ps[:8]}')
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
            if m < 0.12:
                ps.append((round(m, 3), LAYN[l], o))
    ps.sort(key=lambda t: t[0])
    print(f'{label}: worst 6 {[(p[0], p[1], p[2]) for p in ps[:6]]}')
    return ps

def add_via(net, x, y, clr=0.2, r=0.25):
    v = ('via', net, (x, y, r), clr)
    add_items({0: [v], 1: [v], 2: [v]})
    return v

def terms(n):
    fr = fragments(n, BOX)
    tt = sorted(t for f in fr for t in f['terms'])
    return len(fr), tt

# ---- 1) tail verification ----
f0, t0 = terms('PHY_1V8A')
tail = [it for it in pool[2]
        if it[1] == 'PHY_1V8A' and it[0] == 'seg'
        and 70.0 <= C(it)[0] <= 73.35 and 11.8 <= C(it)[1] <= 12.9]
print(f'tail candidates: {len(tail)}')
rip_items(tail)
f1, t1 = terms('PHY_1V8A')
print(f'1V8A frags {f0}->{f1}; terms equal: {t0 == t1}')
if t0 != t1:
    print('  terms before:', t0)
    print('  terms after :', t1)
# keep the tail RIPPED in the working pool for the design
# (pool state now = tail removed)

# ---- Move A2: STP B descent east, jogged west past GND via ----
ripA = [it for it in pool[2]
        if it[1] == 'ULPI_STP' and it[0] == 'seg'
        and 75.9 <= C(it)[0] <= 76.5 and 9.2 <= C(it)[1] <= 13.5]
rip_items(ripA)
newA = {2: [('seg', 'ULPI_STP', (76.44, 9.03, 76.40, 9.90, 0.1), 0.2),
            ('seg', 'ULPI_STP', (76.40, 9.90, 76.30, 11.20, 0.1), 0.2),
            ('seg', 'ULPI_STP', (76.30, 11.20, 76.30, 12.90, 0.1), 0.2),
            ('seg', 'ULPI_STP', (76.30, 12.90, 76.05, 13.45, 0.1), 0.2)]}
gate_items(newA, 'A2 gate', ('ULPI_STP',))
add_items(newA)
print('STP frags:', len(fragments('ULPI_STP', BOX)), '(base 2)')

# ---- Move B: CK In2 jog west ----
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
add_items(newB)
print('CK frags:', len(fragments('ULPI_CK', BOX)), '(base 1)')

# ---- Move C: 1V8A notch v3 ----
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
add_items(newC)
add_via('PHY_1V8A', NV[0], NV[1], clr=0.25)
fC, tC = terms('PHY_1V8A')
print(f'1V8A after notch: frags {fC}, terms == post-tail terms: {tC == t1}')

# ---- XO final re-lay ----
ripX = []
for it in pool[0]:
    if it[1] != 'XO' or it[0] != 'seg':
        continue
    d = it[2]
    pts = ((d[0], d[1]), (d[2], d[3]))
    if any(abs(p[0] - 76.55) < 0.03 and p[1] >= 10.44 for p in pts) or \
       (abs(d[0] - 76.5) < 0.03 and abs(d[1] - 10.75) < 0.03) or \
       (abs(d[2] - 76.5) < 0.03 and abs(d[3] - 10.75) < 0.03):
        ripX.append(it)
print(f'XO rip: {len(ripX)} (expect 7)')
for it in ripX:
    print('   ', it)
rip_items(ripX)
newX = {0: [('seg', 'XO', (76.55, 10.45, 76.82, 10.72, 0.1), 0.2),
            ('seg', 'XO', (76.82, 10.72, 76.80, 11.05, 0.1), 0.2),
            ('seg', 'XO', (76.80, 11.05, 76.75, 11.125, 0.1), 0.2)]}
gate_items(newX, 'XO gate', ('XO',))
add_items(newX)
print('XO frags:', len(fragments('XO', BOX)))

# ---- XI: PV + F leg ----
PV = (75.86, 10.34)
gate_via(PV[0], PV[1], 'XI', 'PV gate')
add_via('XI', PV[0], PV[1])
fleg = {0: [('seg', 'XI', (PV[0], PV[1], 76.20, 10.95, 0.1), 0.2),
            ('seg', 'XI', (76.20, 10.95, 76.25, 11.5625, 0.1), 0.2)]}
gate_items(fleg, 'F leg gate', ('XI',))
add_items(fleg)

# ---- XI: west ride ----
RIDE = [(75.625, 18.625), (74.75, 20.02), (72.05, 20.05), (70.35, 19.35),
        (70.35, 18.15), (69.90, 18.30), (69.70, 17.30), (70.05, 16.85),
        (70.40, 16.40), (70.15, 15.55), (70.15, 9.90), (75.70, 9.90),
        (75.70, 11.20), PV]
ride = {2: [('seg', 'XI', (a[0], a[1], b[0], b[1], 0.125), 0.2)
            for a, b in zip(RIDE, RIDE[1:])]}
gate_items(ride, 'ride gate', ('XI',))
add_items(ride)

for n in ('ULPI_STP', 'PHY_1V8A', 'ULPI_CK', 'ULPI_DIR', 'XO', 'XI'):
    fr, tt = terms(n)
    print(f'frags {n}: {fr}')
fr = fragments('XI', BOX)
for i, f in enumerate(fr):
    print(f'  XI frag{i} terms: {f["terms"]}')

"""t_ba56: XI five-net mega-relay, model gate on exp253.
Moves: (1) STP northern -> In2 underpass: rip B legs column
+ cap chain + descent + transition via + In2 diagonal;
lay In2 west/south/east to dive (76.9,5.85) joining the
tail via (77.15,5.9) zone. (2) DIR via west: rip DIR via
(75.5,17.52) + F stub; lay F escape west + via (74.7,17.3)
+ B leg to DIR's B track. (3) 1V8A notch v2: rip stub+via
+head; via (75.45,10.6), direct F stub, north-bowed B head.
(4) XO foot jog (as t_ba55). (5) XI drop in the freed band.
Gate every net's frags + margins."""
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
                if abs(cc[0] - ci[0]) > 4.5 or abs(cc[1] - ci[1]) > 4.5:
                    continue
                m = item_margin(l, it, [o])
                if m < thr:
                    ps.append((round(m, 3), LAYN[l], o[1],
                               (round(ci[0], 2), round(ci[1], 2)),
                               (round(cc[0], 2), round(cc[1], 2))))
    ps.sort(key=lambda t: t[0])
    print(f'{label}: neg {sum(1 for p in ps if p[0] < 0)}, '
          f'worst 5: {ps[:5]}')
    return ps


def rip_where(net, layer, fn):
    r = [it for it in pool[layer] if it[1] == net and fn(it)]
    rip_items(r)
    return len(r)


# ---------- (1) STP northern -> In2 underpass ----------
n = 0
# legs column + cap + descent on B: STP B segs centres
# x[75.9,76.6] y[9.0,18.3]
n += rip_where('ULPI_STP', 2, lambda it: it[0] == 'seg'
               and 75.9 <= C(it)[0] <= 76.6
               and 9.0 <= C(it)[1] <= 18.3)
# excursion (as before)
n += rip_where('ULPI_STP', 2, lambda it: it[0] == 'seg'
               and 74.3 <= C(it)[0] <= 76.0
               and 13.4 <= C(it)[1] <= 17.2)
# transition via (76.445,9.03) all layers
for l in range(3):
    n += rip_where('ULPI_STP', l, lambda it: it[0] == 'via'
                   and abs(it[2][0] - 76.445) < 0.03
                   and abs(it[2][1] - 9.03) < 0.03)
# In2 diagonal (76.445,9.03)->(77.2,5.9): In2 segs centres
# x[76.3,77.3] y[5.7,9.2]
n += rip_where('ULPI_STP', 1, lambda it: it[0] == 'seg'
               and 76.3 <= C(it)[0] <= 77.3
               and 5.7 <= C(it)[1] <= 9.2)
print(f'STP north rip: {n} items; frags mid:',
      len(fragments('ULPI_STP', BOX)))
STP2 = {1: [('seg', 'ULPI_STP', (76.065, 17.96, 74.3, 17.7, 0.10), 0.2),
            ('seg', 'ULPI_STP', (74.3, 17.7, 74.15, 12.0, 0.10), 0.2),
            ('seg', 'ULPI_STP', (74.15, 12.0, 74.15, 5.5, 0.10), 0.2),
            ('seg', 'ULPI_STP', (74.15, 5.5, 76.9, 5.85, 0.10), 0.2)],
        0: [], 2: []}
gate(STP2, 'STP In2 underpass', ('ULPI_STP',))
add_items(STP2)
VSTP = {l: [('via', 'ULPI_STP', (76.9, 5.85, 0.25), 0.2)]
        for l in range(3)}
gate(VSTP, 'STP dive (76.9,5.85)', ('ULPI_STP',))
add_items(VSTP)
print('STP frags after underpass:', len(fragments('ULPI_STP', BOX)))

# ---------- (2) DIR via west ----------
n = 0
for l in range(3):
    n += rip_where('ULPI_DIR', l, lambda it: it[0] == 'via'
                   and abs(it[2][0] - 75.5) < 0.03
                   and abs(it[2][1] - 17.52) < 0.05)
n += rip_where('ULPI_DIR', 0, lambda it: it[0] == 'seg'
               and 75.4 <= C(it)[0] <= 75.9
               and 16.3 <= C(it)[1] <= 17.6)
print(f'DIR rip: {n} items; frags mid:', len(fragments('ULPI_DIR', BOX)))
DIR2 = {0: [('seg', 'ULPI_DIR', (75.75, 16.4375, 74.9, 16.9, 0.10), 0.2),
            ('seg', 'ULPI_DIR', (74.9, 16.9, 74.7, 17.3, 0.10), 0.2)],
        1: [], 2: [('seg', 'ULPI_DIR', (74.7, 17.3, 74.2, 18.0, 0.10), 0.2),
                   ('seg', 'ULPI_DIR', (74.2, 18.0, 73.44, 18.32, 0.10), 0.2)]}
gate(DIR2, 'DIR relay', ('ULPI_DIR',))
add_items(DIR2)
VDIR = {l: [('via', 'ULPI_DIR', (74.7, 17.3, 0.25), 0.2)]
        for l in range(3)}
gate(VDIR, 'DIR via (74.7,17.3)', ('ULPI_DIR',))
add_items(VDIR)
print('DIR frags after:', len(fragments('ULPI_DIR', BOX)))

# ---------- (3) 1V8A notch v2 ----------
def find_seg(pool_l, net, a, b):
    out = []
    for it in pool_l:
        if it[1] != net or it[0] != 'seg':
            continue
        d = it[2]
        if (abs(d[0] - a[0]) < 0.02 and abs(d[1] - a[1]) < 0.02
                and abs(d[2] - b[0]) < 0.02 and abs(d[3] - b[1]) < 0.02) or \
           (abs(d[0] - b[0]) < 0.02 and abs(d[1] - b[1]) < 0.02
                and abs(d[2] - a[0]) < 0.02 and abs(d[3] - a[1]) < 0.02):
            out.append(it)
    return out

rip2 = []
rip2 += find_seg(pool[0], 'PHY_1V8A', (75.72, 11.0), (75.49, 10.69))
rip2 += find_seg(pool[0], 'PHY_1V8A', (75.49, 10.69), (75.27, 10.33))
rip2 += find_seg(pool[2], 'PHY_1V8A', (75.27, 10.33), (75.05, 10.95))
rip2 += find_seg(pool[2], 'PHY_1V8A', (75.05, 10.95), (74.90, 11.75))
rip2 += find_seg(pool[2], 'PHY_1V8A', (74.90, 11.75), (74.20, 12.25))
rip2 += find_seg(pool[2], 'PHY_1V8A', (74.20, 12.25), (73.50, 12.55))
for l in range(3):
    for it in pool[l]:
        if it[1] == 'PHY_1V8A' and it[0] == 'via' \
                and abs(it[2][0] - 75.27) < 0.02 \
                and abs(it[2][1] - 10.33) < 0.02:
            rip2.append(it)
rip_items(rip2)
print(f'1V8A notch rip: {len(rip2)} items')
NV = {0: [('seg', 'PHY_1V8A', (75.72, 11.0, 75.45, 10.6, 0.10), 0.2)],
      1: [],
      2: [('seg', 'PHY_1V8A', (75.45, 10.6, 75.0, 11.5, 0.10), 0.2),
          ('seg', 'PHY_1V8A', (75.0, 11.5, 74.45, 12.1, 0.10), 0.2),
          ('seg', 'PHY_1V8A', (74.45, 12.1, 73.50, 12.55, 0.10), 0.2)]}
gate(NV, '1V8A notch v2 segs', ('PHY_1V8A',))
add_items(NV)
VNV = {l: [('via', 'PHY_1V8A', (75.45, 10.6, 0.25), 0.2)]
       for l in range(3)}
gate(VNV, '1V8A via (75.45,10.6)', ('PHY_1V8A',))
add_items(VNV)
print('1V8A frags after v2:', len(fragments('PHY_1V8A', BOX)))

# ---------- (4) XO foot jog ----------
ripx = [it for it in pool[0]
        if it[1] == 'XO' and it[0] == 'seg'
        and 75.85 <= C(it)[0] <= 76.52 and 9.6 <= C(it)[1] <= 10.28]
rip_items(ripx)
JOG = {0: [('seg', 'XO', (75.90, 9.70, 76.28, 10.0, 0.10), 0.2),
           ('seg', 'XO', (76.28, 10.0, 76.52, 10.22, 0.10), 0.2)],
       1: [], 2: []}
add_items(JOG)
print('XO frags after jog:', len(fragments('XO', BOX)))

# ---------- (5) XI drop ----------
XIB = {2: [('seg', 'XI', (75.625, 18.625, 75.8, 17.6, 0.10), 0.2),
           ('seg', 'XI', (75.8, 17.6, 75.85, 13.0, 0.10), 0.2),
           ('seg', 'XI', (75.85, 13.0, 75.88, 10.38, 0.10), 0.2)],
       0: [], 1: []}
gate(XIB, 'XI B drop', ('XI',))
add_items(XIB)
VXI = {l: [('via', 'XI', (75.88, 10.38, 0.25), 0.2)] for l in range(3)}
gate(VXI, 'XI pocket via (75.88,10.38)', ('XI',))
add_items(VXI)
XIF = {0: [('seg', 'XI', (75.88, 10.38, 76.15, 10.8, 0.10), 0.2),
           ('seg', 'XI', (76.15, 10.8, 76.25, 11.35, 0.10), 0.2)],
       1: [], 2: []}
gate(XIF, 'XI F legs', ('XI',))
add_items(XIF)
fr = fragments('XI', BOX)
print('XI frags final:', len(fr))
for f in fr:
    print('   terms:', sorted(f['terms'])[:6])
print('=== done ===')

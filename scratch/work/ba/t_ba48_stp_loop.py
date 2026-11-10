"""t_ba48: is STP's western B excursion a removable loop?
On exp253's pool: fragments(ULPI_STP) before; rip STP B
items with centres in x[74.3,75.95] y[13.4,17.2] (west of
the legs column, the y13.7 chain + x74.55 column + NE fan);
fragments after. Also list the ripped set's boundary
endpoints (where it joins the kept web)."""
import sys
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa

pool = load_board_pool('hw/pdlvds_rx.exp253.kicad_pcb')
BOX = (58.0, 96.0, -30.0, 34.0)
fr = fragments('ULPI_STP', BOX)
print('STP frags before:', len(fr))
for f in fr:
    print('   terms:', sorted(f['terms'])[:6], 'items', len(f['items']))

rip = []
for it in pool[2]:
    if it[1] != 'ULPI_STP' or it[0] != 'seg':
        continue
    cc = C(it)
    if 74.3 <= cc[0] <= 75.95 and 13.4 <= cc[1] <= 17.2:
        rip.append(it)
print('excursion candidates:', len(rip))
# boundary: ripped endpoints that coincide with kept items
rip_pts = set()
for it in rip:
    d = it[2]
    rip_pts.add((round(d[0], 2), round(d[1], 2)))
    rip_pts.add((round(d[2], 2), round(d[3], 2)))
kept_pts = set()
for l in range(3):
    for it in pool[l]:
        if it[1] != 'ULPI_STP' or it in rip:
            continue
        if it[0] == 'seg':
            d = it[2]
            kept_pts.add((round(d[0], 2), round(d[1], 2)))
            kept_pts.add((round(d[2], 2), round(d[3], 2)))
        elif it[0] == 'via':
            kept_pts.add((round(it[2][0], 2), round(it[2][1], 2)))
print('boundary join points:', sorted(rip_pts & kept_pts))
rip_items(rip)
fr2 = fragments('ULPI_STP', BOX)
print('STP frags after excursion rip:', len(fr2))
for f in fr2:
    print('   terms:', sorted(f['terms'])[:6], 'items', len(f['items']))
print('=== done ===')

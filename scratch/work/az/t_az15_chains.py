"""t_az15: exact chain joints for the re-lay attachment points."""
import sys
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

pool = load_board_pool('hw/pdlvds_rx.exp251.kicad_pcb')


def joints(net, l, a, b, label):
    try:
        ch = chain_segs(pool, net, l, a, b)
    except SystemExit as e:
        print(label, 'FAILED', e)
        return
    pts = []
    for it in ch:
        d = it[2]
        pts.append((round(d[0], 3), round(d[1], 3)))
    pts.append((round(ch[-1][2][2], 3), round(ch[-1][2][3], 3)))
    print(f'{label}: {len(ch)} segs, joints:')
    print('   ', pts)


# STP B: from the dive-adjacent joint (76.35,18.1) south to via (77,9.6)
joints('ULPI_STP', 2, (76.35, 18.1), (77.0, 9.6), 'STP B chain')
# STP B north stub: dive via (76.065,17.96) to (76.35,18.1)
for it in pool[2]:
    if it[1] == 'ULPI_STP' and it[0] == 'seg':
        d = it[2]
        if (abs(d[0] - 76.065) < 0.01 and abs(d[1] - 17.96) < 0.01) or \
           (abs(d[2] - 76.065) < 0.01 and abs(d[3] - 17.96) < 0.01):
            print('STP B seg at dive via:', L.fmt_it(it))
# XO F: pad (76.75,11.562) west/south to (72.3,9.6)
joints('XO', 0, (76.75, 11.562), (72.3, 9.6), 'XO F chain (pad->west run)')
# PHY_1V8A F stub + B head
for l in (0, 2):
    for it in pool[l]:
        if it[1] == 'PHY_1V8A' and it[0] == 'seg':
            d = it[2]
            if max(d[0], d[2]) > 75.2 and min(d[1], d[3]) < 12.0:
                print(f'1V8A L{l}:', L.fmt_it(it))
# PHY_1V8 B loop joints
joints('PHY_1V8', 2, (77.25, 10.75), (77.8, 16.2), 'PHY B chain (pad dive->joint)')
print('=== done ===')

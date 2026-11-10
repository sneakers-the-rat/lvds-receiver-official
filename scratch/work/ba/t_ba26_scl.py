"""t_ba26: I2C_SCL items in x[74,81] y[5,13] (all layers) --
the fence at B (77.25,9.0). Plus: gate the GND via
(77.55,9.55) with SCL's B items in that box shifted +0.18
in x and -0.10 in y (local re-lay simulation)."""
import sys
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L

pool = load_board_pool('hw/pdlvds_rx.exp252.kicad_pcb')
LAYN = {0: 'F', 1: 'In2', 2: 'B'}
print('--- I2C_SCL items x[74,81] y[5,13] ---')
for l in range(3):
    for it in pool[l]:
        if it[1] != 'I2C_SCL':
            continue
        cc = C(it)
        if 74 <= cc[0] <= 81 and 5 <= cc[1] <= 13:
            d = it[2]
            if it[0] == 'seg':
                print(f'  {LAYN[l]} seg ({d[0]:.2f},{d[1]:.2f})->'
                      f'({d[2]:.2f},{d[3]:.2f}) hw{d[4]}')
            elif it[0] == 'via':
                print(f'  {LAYN[l]} via ({d[0]:.2f},{d[1]:.2f}) r{d[2]}')
            else:
                print(f'  {LAYN[l]} pad ({d[0]:.2f},{d[1]:.2f})')


def gate_via(x, y, net='GND'):
    it = ('via', net, (x, y, 0.25), 0.2)
    w, wo = 9.9, None
    for l in range(3):
        for o in pool[l]:
            if o[1] == net:
                continue
            cc = C(o)
            if abs(cc[0] - x) > 3 or abs(cc[1] - y) > 3:
                continue
            m = item_margin(l, it, [o])
            if m < w:
                w, wo = m, (LAYN[l], o[1],
                            (round(cc[0], 2), round(cc[1], 2)))
    return w, wo


print('GND via (77.55,9.55) as-is:', gate_via(77.55, 9.55))
# shift SCL B segs in the box SE: +0.18 x, -0.10 y
moved = []
for it in list(pool[2]):
    if it[1] != 'I2C_SCL' or it[0] != 'seg':
        continue
    cc = C(it)
    if 75.5 <= cc[0] <= 79.5 and 7.5 <= cc[1] <= 10.5:
        d = it[2]
        moved.append((it, ('seg', 'I2C_SCL',
                           (d[0] + 0.18, d[1] - 0.10, d[2] + 0.18,
                            d[3] - 0.10, d[4]), it[3])))
print(f'shifting {len(moved)} SCL B segs')
rip_items([m[0] for m in moved])
add_items({0: [], 1: [], 2: [m[1] for m in moved]})
print('GND via (77.55,9.55) after SCL shift:', gate_via(77.55, 9.55))
print('SCL frags:', len(fragments('I2C_SCL', (58.0, 96.0, -30.0, 34.0))))
print('=== done ===')

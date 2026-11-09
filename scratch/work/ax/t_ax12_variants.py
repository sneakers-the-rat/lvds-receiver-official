"""t_ax12: M1 feasibility variants.
V1: W5=(67.5,5.8), plain M1 A*.
V2: W4=(67.5,5.65) + M5 (THR_DAC via (66.625,4.875)->(66.35,4.6),
In2 corner + B corner re-lays), then M1 A*."""
import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa


def place_W(pool, W):
    via = ('via', 'I2C_SCL', (W[0], W[1], 0.25), 0.2)
    seg = ('seg', 'I2C_SCL', (66.875, 6.75, W[0], W[1], 0.10), 0.2)
    add_items({0: [via], 2: [via]})
    pool[1].append(via)
    pool[1].append(seg)
    return via, seg


def m1(pool):
    rip = chain_segs(pool, 'GND', 1, (66.375, 6.125), (67.375, 4.125))
    n = rip_items(rip)
    assert n == len(rip)
    astar = make_astar((65.4, 68.2, 3.4, 7.0), 0.025)
    return astar('GND', ((1,), 66.375, 6.125), (1, 67.375, 4.125),
                 hw=0.125)


# V1
pool = load_board_pool()
place_W(pool, (67.5, 5.8))
J = m1(pool)
print('V1 W5=(67.5,5.8) M1:', 'FOUND' if J else 'NONE', flush=True)
if J:
    its = journey_items_dense(J, 'GND', hw=0.125)
    worst = 9.9
    wb = None
    for l in range(3):
        for it in its[l]:
            for o in pool[l]:
                if o[1] == 'GND':
                    continue
                m = item_margin(l, it, [o])
                if m < worst:
                    worst, wb = m, o
    print(f'  V1 M1 gate worst {worst:+.3f} vs {L.fmt_it(wb)}',
          flush=True)

# V2
pool = load_board_pool()
place_W(pool, (67.5, 5.65))
# M5: rip THR_DAC via + In2 steps from (66.375,5.125) to the via +
# B segs from the via to (67.125,4.375)
oldvia = ('via', 'THR_DAC', (66.625, 4.875, 0.3), 0.2)
rip = [oldvia]
rip += chain_segs(pool, 'THR_DAC', 1, (66.375, 5.125), (66.625, 4.875))
rip += chain_segs(pool, 'THR_DAC', 2, (66.625, 4.875), (67.125, 4.375))
n = rip_items(rip)
print(f'V2 M5 rip {n} of {len(rip)}', flush=True)
assert n == len(rip)
NV = (66.35, 4.6)
newvia = ('via', 'THR_DAC', (NV[0], NV[1], 0.3), 0.2)
add_items({0: [newvia], 2: [newvia]})
pool[1].append(newvia)
for l in range(3):
    mm = min(item_margin(l, newvia, [o]) for o in pool[l]
             if o[1] != 'THR_DAC')
    print(f'  V2 THR via margin L{l}: {mm:+.3f}', flush=True)
astar = make_astar((64.8, 68.0, 3.6, 6.2), 0.025)
J = astar('THR_DAC', ((1,), 66.375, 5.125), (1, NV[0], NV[1]), hw=0.10,
          layer_lock=[0, 1, 0])
print('V2 THR In2 corner:', 'FOUND' if J else 'NONE', flush=True)
if J:
    its = journey_items_dense(J, 'THR_DAC', hw=0.10)
    add_items(its)
astar = make_astar((65.4, 68.2, 3.2, 5.8), 0.025)
J = astar('THR_DAC', ((2,), NV[0], NV[1]), (2, 67.125, 4.375), hw=0.10,
          layer_lock=[0, 0, 1])
print('V2 THR B corner:', 'FOUND' if J else 'NONE', flush=True)
if J:
    its = journey_items_dense(J, 'THR_DAC', hw=0.10)
    add_items(its)
    J = m1(pool)
    print('V2 M1 after M5:', 'FOUND' if J else 'NONE', flush=True)
    if J:
        its = journey_items_dense(J, 'GND', hw=0.125)
        worst = 9.9
        wb = None
        for l in range(3):
            for it in its[l]:
                for o in pool[l]:
                    if o[1] == 'GND':
                        continue
                    m = item_margin(l, it, [o])
                    if m < worst:
                        worst, wb = m, o
        print(f'  V2 M1 gate worst {worst:+.3f} vs {L.fmt_it(wb)}',
              flush=True)

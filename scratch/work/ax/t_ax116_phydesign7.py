import sys, json
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp249.kicad_pcb')

def gate(its, net, pool, label):
    worst = (9.9, None, None)
    for l in range(3):
        for it in its[l]:
            for o in pool[l]:
                if o[1] == net:
                    continue
                m = item_margin(l, it, [o])
                if m < worst[0]:
                    worst = (m, it, o)
    print(f'{label} gate worst {worst[0]:+.3f} {L.fmt_it(worst[1])} vs '
          f'{L.fmt_it(worst[2])}', flush=True)
    return worst[0]

# 1. C16 -> (70.25,13.0) rot 180
c16_old = [it for it in pool[0] if it[0] == 'pad'
           and abs(it[2][1] - 9.75) < 0.01
           and it[2][0] in (75.225, 76.775)]
feed = [it for it in pool[0] if it[1] == '+3V3D' and it[0] == 'seg'
        and ((abs(it[2][0] - 75.225) < 0.01 and abs(it[2][1] - 9.75) < 0.01)
             or (abs(it[2][0] - 75.225) < 0.01
                 and abs(it[2][1] - 9.5) < 0.01))]
print('C16 rip:', rip_items(c16_old + feed), flush=True)
add_items({0: [('pad', '+3V3D', (71.025, 13.0, 0.450, 0.475, 0.0), 0.2),
               ('pad', 'GND', (69.475, 13.0, 0.450, 0.475, 0.0), 0.2)]})
# 2. C23 rot 180 + rip GND stitch via
c23 = [it for it in pool[0] if it[0] == 'pad'
       and abs(it[2][1] - 14.75) < 0.01 and it[2][0] in (69.975, 71.525)]
gndvia = [it for it in pool[0] if it[0] == 'via' and it[1] == 'GND'
          and abs(it[2][0] - 71.8) < 0.01 and abs(it[2][1] - 14.9) < 0.01]
print('C23 rip:', rip_items(c23 + gndvia), flush=True)
add_items({0: [('pad', 'GND', (69.975, 14.75, 0.450, 0.475, 0.0), 0.2),
               ('pad', 'PHY_1V8A', (71.525, 14.75, 0.450, 0.475, 0.0), 0.2)]})
# 3. +3V3D via shrink + joiner
v3d_via = [it for it in pool[0] if it[0] == 'via' and it[1] == '+3V3D'
           and abs(it[2][0] - 70.875) < 0.01
           and abs(it[2][1] - 12.625) < 0.01]
rip_items(v3d_via)
add_items({l: [('via', '+3V3D', (70.875, 12.625, 0.25), 0.25)]
           for l in range(3)})
joiner = {0: [('seg', '+3V3D', (71.025, 13.0, 70.875, 12.625, 0.10), 0.25)],
          1: [], 2: []}
v3d_via2 = [it for it in pool[0] if it[0] == 'via' and it[1] == '+3V3D'
            and abs(it[2][0] - 70.875) < 0.01
            and abs(it[2][1] - 15.875) < 0.01]
print('via2 rip:', rip_items(v3d_via2), flush=True)
add_items({l: [('via', '+3V3D', (70.875, 15.875, 0.25), 0.25)]
           for l in range(3)})
gate(joiner, '+3V3D', pool, 'joiner')
add_items(joiner)
# 3b. +3V3D B vertical width normalize hw0.3 -> hw0.1
bvert = [it for it in pool[2] if it[1] == '+3V3D' and it[0] == 'seg'
         and abs(it[2][0] - 70.875) < 0.01 and abs(it[2][2] - 70.875) < 0.01
         and 12.0 < it[2][1] < 16.0]
print('B vertical segs:', len(bvert), flush=True)
print('B vert rip:', rip_items(bvert), flush=True)
add_items({2: [('seg', '+3V3D', (70.875, 12.625, 70.875, 15.875, 0.10),
                0.25)], 0: [], 1: []})
# 4. XO tail rip
xo_via = [it for it in pool[0] if it[0] == 'via' and it[1] == 'XO'
          and abs(it[2][0] - 76.0) < 0.01 and abs(it[2][1] - 10.625) < 0.01]
xo_b = [it for it in pool[2] if it[1] == 'XO' and it[0] == 'seg'
        and it[2][0] in (76.0, 74.125) and it[2][1] in (10.625, 12.25)]
xo_f = [it for it in pool[0] if it[1] == 'XO' and it[0] == 'seg'
        and abs(it[2][0] - 76.5) < 0.01 and abs(it[2][1] - 10.75) < 0.01]
print('XO rip:', rip_items(xo_via + xo_b + xo_f), flush=True)
# 5a. PHY stub + notch via
stub = {0: [('seg', 'PHY_1V8A', (75.75, 11.5625, 75.72, 11.0, 0.10), 0.2),
            ('seg', 'PHY_1V8A', (75.72, 11.0, 75.7375, 10.75, 0.10), 0.2)],
        1: [], 2: []}
for l in range(3):
    stub[l].append(('via', 'PHY_1V8A', (75.7375, 10.75, 0.25), 0.2))
gate(stub, 'PHY_1V8A', pool, 'PHY stub')
add_items(stub)
# 5b. PHY B journey aj7 to door-1
Bpts = [(75.7375, 10.75), (75.3, 11.35), (74.9, 11.75), (74.2, 12.25),
        (73.5, 12.55), (73.3, 12.2), (73.22, 11.94), (72.92, 11.62),
        (72.35, 11.65), (71.9, 11.95), (71.3, 12.1), (70.7, 11.85),
        (70.3, 12.15), (70.2, 12.5), (70.18, 12.75)]
bj = {0: [], 1: [], 2: []}
for a, bpt in zip(Bpts, Bpts[1:]):
    bj[2].append(('seg', 'PHY_1V8A', (a[0], a[1], bpt[0], bpt[1], 0.10),
                  0.2))
gate(bj, 'PHY_1V8A', pool, 'PHY B journey')
add_items(bj)
# 5c. goal via (71.5,15.46) + F stub south into the pad
goal = {0: [('seg', 'PHY_1V8A', (71.5, 15.46, 71.5, 15.15, 0.10), 0.2)],
        1: [], 2: []}
for l in range(3):
    goal[l].append(('via', 'PHY_1V8A', (71.5, 15.46, 0.25), 0.2))
gate(goal, 'PHY_1V8A', pool, 'PHY goal via+stub')
add_items(goal)
# 6. XO rejoin
astar = make_astar((70.0, 78.0, 7.5, 14.0), 0.05)
Jx = astar('XO', ((0,), 76.5, 10.75), (0, 72.625, 10.375), hw=0.10)
print('XO rejoin:', 'FOUND' if Jx else 'NONE', flush=True)
if Jx:
    itsx = journey_items_dense(Jx, 'XO', hw=0.10)
    gate(itsx, 'XO', pool, 'XO rejoin')
    add_items(itsx)
# 7. C16 GND A*
astar = make_astar((67.0, 74.0, 9.0, 15.0), 0.05)
Jg = astar('GND', ((0,), 69.475, 13.0), (0, 71.775, 11.0), hw=0.10)
print('C16 GND:', 'FOUND' if Jg else 'NONE', flush=True)
if Jg:
    print('  vias:', Jg['vias'], flush=True)
    itsg = journey_items_dense(Jg, 'GND', hw=0.10)
    gate(itsg, 'GND', pool, 'C16 GND')
    add_items(itsg)
# 8. PHY tail A* (B) door-1 -> goal via (71.5,15.46)
astar = make_astar((69.0, 74.5, 11.0, 16.5), 0.05)
Jt = astar('PHY_1V8A', ((2,), 70.18, 12.75), (2, 71.5, 15.46), hw=0.10)
print('PHY tail (B):', 'FOUND' if Jt else 'NONE', flush=True)
if Jt:
    print('  vias:', Jt['vias'], flush=True)
    itst = journey_items_dense(Jt, 'PHY_1V8A', hw=0.10)
    gate(itst, 'PHY_1V8A', pool, 'PHY tail')
if Jx and Jg and Jt:
    json.dump({'xo': Jx, 'gnd': Jg, 'tail': Jt},
              open('scratch/work/ax/phy_design_ax116.json', 'w'))
    print('saved phy_design_ax116.json', flush=True)

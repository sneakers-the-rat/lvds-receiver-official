import sys, json
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp249.kicad_pcb')

def gate(its, net, pool):
    worst = (9.9, None, None)
    for l in range(3):
        for it in its[l]:
            for o in pool[l]:
                if o[1] == net:
                    continue
                m = item_margin(l, it, [o])
                if m < worst[0]:
                    worst = (m, it, o)
    return worst

# staged GND diagnosis first (on the pristine pool)
for label, start, goal, box in (
    ('GND (69.475,13)->(69.6,12.3)F', ((0,), 69.475, 13.0),
     (0, 69.6, 12.3), (67.0, 73.0, 10.5, 16.5)),
    ('GND dive->(69.6,14.55)In2', ((0, 1, 2), 69.6, 12.3),
     (1, 69.6, 14.55), (67.0, 73.0, 10.5, 16.5)),
    ('GND dive->C23.2', ((0, 1, 2), 69.6, 12.3),
     (0, 71.525, 14.75), (67.0, 73.0, 10.5, 16.5)),
):
    astar = make_astar(box, 0.05)
    J = astar('GND', start, goal, hw=0.10)
    print(f'{label}:', 'FOUND' if J else 'NONE', flush=True)

# --- apply the model edits (same as t_ax104) ---
c16_old = [it for it in pool[0] if it[0] == 'pad'
           and abs(it[2][1] - 9.75) < 0.01
           and it[2][0] in (75.225, 76.775)]
feed = [it for it in pool[0] if it[1] == '+3V3D' and it[0] == 'seg'
        and ((abs(it[2][0] - 75.225) < 0.01 and abs(it[2][1] - 9.75) < 0.01)
             or (abs(it[2][0] - 75.225) < 0.01
                 and abs(it[2][1] - 9.5) < 0.01))]
rip_items(c16_old + feed)
add_items({0: [('pad', '+3V3D', (71.025, 13.0, 0.450, 0.475, 0.0), 0.2),
               ('pad', 'GND', (69.475, 13.0, 0.450, 0.475, 0.0), 0.2)]})
xo_via = [it for it in pool[0] if it[0] == 'via' and it[1] == 'XO'
          and abs(it[2][0] - 76.0) < 0.01 and abs(it[2][1] - 10.625) < 0.01]
xo_b = [it for it in pool[2] if it[1] == 'XO' and it[0] == 'seg'
        and it[2][0] in (76.0, 74.125) and it[2][1] in (10.625, 12.25)]
xo_f = [it for it in pool[0] if it[1] == 'XO' and it[0] == 'seg'
        and abs(it[2][0] - 76.5) < 0.01 and abs(it[2][1] - 10.75) < 0.01]
rip_items(xo_via + xo_b + xo_f)
v3d_via = [it for it in pool[0] if it[0] == 'via' and it[1] == '+3V3D'
           and abs(it[2][0] - 70.875) < 0.01
           and abs(it[2][1] - 12.625) < 0.01]
rip_items(v3d_via)
add_items({l: [('via', '+3V3D', (70.875, 12.625, 0.25), 0.25)]
           for l in range(3)})
add_items({0: [('seg', '+3V3D', (71.025, 13.0, 70.875, 12.625, 0.10),
                0.25)], 1: [], 2: []})

# PHY v2: goal via (69.35,14.35), B tail adjusted, F stub to C23.1
Bpts = [(75.7375, 10.75), (75.3, 11.35), (74.9, 11.75), (74.2, 12.25),
        (73.5, 12.55), (73.3, 12.2), (73.22, 11.94), (72.92, 11.62),
        (72.35, 11.65), (71.9, 11.95), (71.3, 12.1), (70.7, 11.85),
        (70.3, 12.15), (70.2, 12.5), (70.18, 12.75), (70.1, 13.3),
        (69.8, 14.0), (69.35, 14.35)]
phy = {0: [('seg', 'PHY_1V8A', (75.75, 11.5625, 75.72, 11.0, 0.10), 0.2),
           ('seg', 'PHY_1V8A', (75.72, 11.0, 75.7375, 10.75, 0.10), 0.2),
           ('seg', 'PHY_1V8A', (69.35, 14.35, 69.8, 14.65, 0.10), 0.2)],
       1: [], 2: []}
for a, bpt in zip(Bpts, Bpts[1:]):
    phy[2].append(('seg', 'PHY_1V8A', (a[0], a[1], bpt[0], bpt[1], 0.10),
                   0.2))
for l in range(3):
    phy[l].append(('via', 'PHY_1V8A', (75.7375, 10.75, 0.25), 0.2))
    phy[l].append(('via', 'PHY_1V8A', (69.35, 14.35, 0.25), 0.2))
w = gate(phy, 'PHY_1V8A', pool)
print(f'PHY v2 gate worst {w[0]:+.3f} {L.fmt_it(w[1])} vs {L.fmt_it(w[2])}',
      flush=True)
add_items(phy)

# XO rejoin with the south-loop box, goal = XO F term (72.625,10.375)
astar = make_astar((70.0, 78.0, 7.5, 14.0), 0.05)
Jx = astar('XO', ((0,), 76.5, 10.75), (0, 72.625, 10.375), hw=0.10)
print('XO rejoin v2:', 'FOUND' if Jx else 'NONE', flush=True)
if Jx:
    print('  vias:', Jx['vias'], flush=True)
    itsx = journey_items_dense(Jx, 'XO', hw=0.10)
    w = gate(itsx, 'XO', pool)
    print(f'  gate worst {w[0]:+.3f} {L.fmt_it(w[1])} vs {L.fmt_it(w[2])}',
          flush=True)
    add_items(itsx)

# GND full: pad2 -> C23.2 with the dive path now informed
astar = make_astar((67.0, 73.0, 10.5, 16.5), 0.05)
Jg = astar('GND', ((0,), 69.475, 13.0), (0, 71.525, 14.75), hw=0.10)
print('C16 GND re-lay v2:', 'FOUND' if Jg else 'NONE', flush=True)
if Jg:
    print('  vias:', Jg['vias'], flush=True)
    itsg = journey_items_dense(Jg, 'GND', hw=0.10)
    w = gate(itsg, 'GND', pool)
    print(f'  gate worst {w[0]:+.3f} {L.fmt_it(w[1])} vs {L.fmt_it(w[2])}',
          flush=True)
if Jx and Jg:
    json.dump({'xo': Jx, 'gnd': Jg},
              open('scratch/work/ax/phy_design_ax106.json', 'w'))
    print('saved phy_design_ax106.json', flush=True)

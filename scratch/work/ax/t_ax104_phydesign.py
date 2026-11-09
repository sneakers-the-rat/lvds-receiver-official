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

# 1. C16 move: rip old pads + its +3V3D feed stub (2 segs)
c16_old = [it for it in pool[0] if it[0] == 'pad'
           and abs(it[2][1] - 9.75) < 0.01
           and it[2][0] in (75.225, 76.775)]
feed = [it for it in pool[0] if it[1] == '+3V3D' and it[0] == 'seg'
        and ((abs(it[2][0] - 75.225) < 0.01 and abs(it[2][1] - 9.75) < 0.01)
             or (abs(it[2][0] - 75.225) < 0.01
                 and abs(it[2][1] - 9.5) < 0.01))]
print('C16 pads:', len(c16_old), 'feed segs:', len(feed), flush=True)
n = rip_items(c16_old + feed)
print('ripped:', n, flush=True)
add_items({0: [('pad', '+3V3D', (71.025, 13.0, 0.450, 0.475, 0.0), 0.2),
               ('pad', 'GND', (69.475, 13.0, 0.450, 0.475, 0.0), 0.2)]})

# 2. XO tail rip: notch via + B chain + F end seg
xo_via = [it for it in pool[0] if it[0] == 'via' and it[1] == 'XO'
          and abs(it[2][0] - 76.0) < 0.01 and abs(it[2][1] - 10.625) < 0.01]
xo_b = [it for it in pool[2] if it[1] == 'XO' and it[0] == 'seg'
        and it[2][0] in (76.0, 74.125) and it[2][1] in (10.625, 12.25)]
xo_f = [it for it in pool[0] if it[1] == 'XO' and it[0] == 'seg'
        and abs(it[2][0] - 76.5) < 0.01 and abs(it[2][1] - 10.75) < 0.01]
print('XO via:', len(xo_via), 'B chain:', len(xo_b), 'F end:', len(xo_f),
      flush=True)
n = rip_items(xo_via + xo_b + xo_f)
print('ripped (via counts 3):', n, flush=True)

# 3. +3V3D via shrink d0.8 -> d0.5 at (70.875,12.625)
v3d_via = [it for it in pool[0] if it[0] == 'via' and it[1] == '+3V3D'
           and abs(it[2][0] - 70.875) < 0.01
           and abs(it[2][1] - 12.625) < 0.01]
print('+3V3D via items:', len(v3d_via), flush=True)
n = rip_items(v3d_via)
add_items({l: [('via', '+3V3D', (70.875, 12.625, 0.25), 0.25)]
           for l in range(3)})
print('shrunk; ripped:', n, flush=True)
# C16.1 joiner seg pad -> via (same net)
joiner = {0: [('seg', '+3V3D', (71.025, 13.0, 70.875, 12.625, 0.10), 0.25)],
          1: [], 2: []}
w = gate(joiner, '+3V3D', pool)
print(f'joiner gate {w[0]:+.3f} {L.fmt_it(w[1])} vs {L.fmt_it(w[2])}',
      flush=True)
add_items(joiner)

# 4. PHY aj7 journey verbatim
Bpts = [(75.7375, 10.75), (75.3, 11.35), (74.9, 11.75), (74.2, 12.25),
        (73.5, 12.55), (73.3, 12.2), (73.22, 11.94), (72.92, 11.62),
        (72.35, 11.65), (71.9, 11.95), (71.3, 12.1), (70.7, 11.85),
        (70.3, 12.15), (70.2, 12.5), (70.18, 12.75), (70.1, 13.3),
        (70.0, 14.3), (69.9375, 15.375)]
phy = {0: [('seg', 'PHY_1V8A', (75.75, 11.5625, 75.72, 11.0, 0.10), 0.2),
           ('seg', 'PHY_1V8A', (75.72, 11.0, 75.7375, 10.75, 0.10), 0.2)],
       1: [], 2: []}
for a, bpt in zip(Bpts, Bpts[1:]):
    phy[2].append(('seg', 'PHY_1V8A', (a[0], a[1], bpt[0], bpt[1], 0.10),
                   0.2))
for l in range(3):
    phy[l].append(('via', 'PHY_1V8A', (75.7375, 10.75, 0.25), 0.2))
    phy[l].append(('via', 'PHY_1V8A', (69.9375, 15.375, 0.25), 0.2))
w = gate(phy, 'PHY_1V8A', pool)
print(f'PHY gate worst {w[0]:+.3f} {L.fmt_it(w[1])} vs {L.fmt_it(w[2])}',
      flush=True)
add_items(phy)

# 5. XO rejoin A*: (76.5,10.75) F -> via (72.625,12.25)
astar = make_astar((71.0, 78.0, 9.0, 14.0), 0.05)
Jx = astar('XO', ((0,), 76.5, 10.75), (0, 72.625, 12.25), hw=0.10)
print('XO rejoin:', 'FOUND' if Jx else 'NONE', flush=True)
if Jx:
    print('  vias:', Jx['vias'], flush=True)
    itsx = journey_items_dense(Jx, 'XO', hw=0.10)
    w = gate(itsx, 'XO', pool)
    print(f'  gate worst {w[0]:+.3f} {L.fmt_it(w[1])} vs {L.fmt_it(w[2])}',
          flush=True)
    add_items(itsx)

# 6. C16 GND re-lay A*: pad2 (69.475,13.0) -> C23.2 (71.525,14.75)
astar = make_astar((67.0, 73.0, 10.5, 16.5), 0.05)
Jg = astar('GND', ((0,), 69.475, 13.0), (0, 71.525, 14.75), hw=0.10)
print('C16 GND re-lay:', 'FOUND' if Jg else 'NONE', flush=True)
if Jg:
    print('  vias:', Jg['vias'], flush=True)
    itsg = journey_items_dense(Jg, 'GND', hw=0.10)
    w = gate(itsg, 'GND', pool)
    print(f'  gate worst {w[0]:+.3f} {L.fmt_it(w[1])} vs {L.fmt_it(w[2])}',
          flush=True)

if Jx and Jg:
    json.dump({'xo': Jx, 'gnd': Jg},
              open('scratch/work/ax/phy_design_ax104.json', 'w'))
    print('saved phy_design_ax104.json', flush=True)

"""t_aj7: PHY_1V8A design proof on exp221 (NOT a bankable build).
XO's tail is ripped and XO is deliberately NOT re-laid: this board
exists only to prove that PHY_1V8A's complete journey gates green
in the exact item model once the notch is free. The bankable pass
is blocked solely by XO's rejoin (see DISTRICT-STATUS-3.md).

Design: F stub U7.29 -> via Vp2 (75.7375,10.75) d0.5; B journey
south of +3V3A's via, north arc around RBIAS's via (73.875,11.625),
through the RBIAS/XO via gate (73.22,11.94), west north of +5V's
via (72.2,13.1), door-1 gate between I2C_SCL's via moved to
(69.5,12.75) and +3V3D's via (70.875,12.625) shrunk to d0.5,
channel x~70.1 south to goal via (69.9375,15.375) d0.5 (disc
overlaps C23.1's pad on F). +3V3A feed untouched in this proof."""
import sys
sys.path.insert(0, 'hw')
sys.path.insert(0, 'scratch/work/ai')
import wx
_app = wx.App(False)
import pcbnew
from t_ai_lib import (load_items, pt_margin, seg_margin,
                      in_box_pool, apply_rip, fmt_it)

SRC = 'hw/pdlvds_rx.exp221.kicad_pcb'
OUT = 'scratch/work/aj/exp222_PHYPROOF.kicad_pcb'
LAY = {'F': pcbnew.F_Cu, 'In2': pcbnew.In2_Cu, 'B': pcbnew.B_Cu}
LI = {'F': 0, 'In2': 1, 'B': 2}

RIP_SPECS = [
    ('seg', 'XO', 76.75, 11.125), ('seg', 'XO', 76.5, 10.75),
    ('via', 'XO', 76.0, 10.625), ('seg', 'XO', 74.125, 12.25),
    ('via', '+3V3D', 70.875, 12.625),
    ('via', 'I2C_SCL', 69.625, 12.625), ('seg', 'I2C_SCL', 69.625, 12.625),
]
items = load_items(pcbnew.LoadBoard(SRC))
statics, n_rip = apply_rip(items, RIP_SPECS)
print(f'ripped {n_rip} model entries')

VP2 = (75.7375, 10.75)
GOALV = (69.9375, 15.375)
ADDS = []
def seg(net, layer, a, b, hw=0.1):
    ADDS.append((net, 'seg', layer, (a, b), hw))
def via(net, pt, rad=0.25):
    ADDS.append((net, 'via', None, pt, rad))

seg('PHY_1V8A', 'F', (75.75, 11.562), (75.72, 11.0))
seg('PHY_1V8A', 'F', (75.72, 11.0), VP2)
via('PHY_1V8A', VP2)
BPTS = [VP2, (75.3, 11.35), (74.9, 11.75), (74.2, 12.25),
        (73.5, 12.55), (73.3, 12.2), (73.22, 11.94),
        (72.92, 11.62), (72.35, 11.65), (71.9, 11.95), (71.3, 12.1),
        (70.7, 11.85), (70.3, 12.15), (70.2, 12.5),
        (70.18, 12.75), (70.1, 13.3), (70.0, 14.3), GOALV]
for a, b in zip(BPTS, BPTS[1:]):
    seg('PHY_1V8A', 'B', a, b)
via('PHY_1V8A', GOALV)
via('+3V3D', (70.875, 12.625))
via('I2C_SCL', (69.5, 12.75), 0.3)
seg('I2C_SCL', 'F', (69.675, 12.75), (69.5, 12.75))
seg('I2C_SCL', 'In2', (69.5, 12.75), (67.0, 12.7))
seg('I2C_SCL', 'In2', (67.0, 12.7), (65.0, 12.5))

BOX = (63.5, 79.5, 7.5, 17.0)
pools = in_box_pool(statics, BOX, pad=1.2)

def to_item(net, kind, data, hwr):
    if kind == 'via':
        return ('via', net, (data[0], data[1], hwr))
    (a, b) = data
    return ('seg', net, (a[0], a[1], b[0], b[1], hwr))

add_items = {0: [], 1: [], 2: []}
for (net, kind, layer, data, hwr) in ADDS:
    if kind == 'via':
        for li in range(3):
            add_items[li].append(to_item(net, kind, data, hwr))
    else:
        add_items[LI[layer]].append(to_item(net, kind, data, hwr))

fails = []
worst = []
for (net, kind, layer, data, hwr) in ADDS:
    if kind == 'via':
        for li in range(3):
            m, w = pt_margin(li, data[0], data[1], net, hwr,
                             pools[li] + add_items[li])
            worst.append((m, net, kind, data, li))
            if m < 0:
                fails.append((net, kind, data, li, m, w))
    else:
        li = LI[layer]
        m, w = seg_margin(li, data[0], data[1], net, hwr,
                          pools[li] + add_items[li])
        worst.append((m, net, kind, data, li))
        if m < 0:
            fails.append((net, kind, data, li, m, w))
worst.sort()
print('worst 8 gates:')
for m, net, kind, data, li in worst[:8]:
    print(f'   {m:+.3f} {net} {kind} {data} L{li}')
if fails:
    print('GATE FAILURES:')
    for net, kind, data, li, m, w in fails:
        print(f'   {net} {kind} {data} L{li}: {m:+.3f} vs '
              f'{fmt_it(w) if w else "-"}')
    sys.exit(1)
print('all in-model gates pass -- PHY journey proven modulo XO rejoin')

"""t_aj6: pass-222 candidate build on exp221.
Joint PHY_1V8A connect + XO tail re-lay:
 - XO tail ripped (F stub x2, via (76.0,10.625), B chain x2);
   XO rejoins on F westward at y~10.1-10.34 under the re-laid
   +3V3A feed, into its own seg point (72.375,10.0).
 - +3V3A U7.30/31 feed re-laid: old via (73.625,10.625) d0.8 and
   its F chain + B legs ripped; new via (74.7,10.75) d0.5, F seg
   from the (75.125,11.125) joint, B seg north to the w0.6
   horizontal at (74.2,8.625).
 - PHY_1V8A: F stub from U7.29 to via (75.7375,10.75) d0.5
   (the notch's single feasible dive, +0.022 in-model), B journey
   south of +3V3A/RBIAS/XO vias, gate between I2C_SCL's moved
   via (69.5,12.75) and +3V3D's shrunk via (70.875,12.625) d0.5,
   north-south channel x~70.1 to goal via (69.9375,15.375) d0.5
   whose disc overlaps C23.1's pad on F.
 - I2C_SCL via (69.625,12.625) d0.6 moved to (69.5,12.75) (fully
   inside R20.1's pad rect); F stub + In2 horizontal re-laid.
 - +3V3D via (70.875,12.625) shrunk d0.8/drill0.4 -> d0.5/0.3.
Every add gated in-model vs statics (post-rip) and vs other-net
adds. If any gate fails, NOTHING is emitted."""
import sys
sys.path.insert(0, 'hw')
sys.path.insert(0, 'scratch/work/ai')
import wx
_app = wx.App(False)
import pcbnew
from t_ai_lib import (load_items, pt_margin, seg_margin,
                      in_box_pool, apply_rip, fmt_it)

SRC = 'hw/pdlvds_rx.exp221.kicad_pcb'
OUT = 'scratch/work/aj/exp222cand.kicad_pcb'
LAY = {'F': pcbnew.F_Cu, 'In2': pcbnew.In2_Cu, 'B': pcbnew.B_Cu}
LI = {'F': 0, 'In2': 1, 'B': 2}

RIP_SPECS = [
    ('seg', 'XO', 76.75, 11.125), ('seg', 'XO', 76.5, 10.75),
    ('via', 'XO', 76.0, 10.625), ('seg', 'XO', 74.125, 12.25),
    ('seg', '+3V3A', 74.25, 10.625), ('seg', '+3V3A', 73.625, 10.625),
    ('via', '+3V3A', 73.625, 10.625),
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

# PHY_1V8A: F stub + dive
seg('PHY_1V8A', 'F', (75.75, 11.562), (75.72, 11.0))
seg('PHY_1V8A', 'F', (75.72, 11.0), VP2)
via('PHY_1V8A', VP2)
# PHY_1V8A: B journey
BPTS = [VP2, (75.3, 11.3), (74.9, 11.75), (74.2, 12.25),
        (73.5, 12.55), (72.75, 12.85), (71.8, 12.55),
        (71.3, 12.1), (70.7, 11.85), (70.3, 12.15),
        (70.2, 12.5), (70.18, 12.75), (70.1, 13.3),
        (70.0, 14.3), GOALV]
for a, b in zip(BPTS, BPTS[1:]):
    seg('PHY_1V8A', 'B', a, b)
via('PHY_1V8A', GOALV)
# XO: F rejoin
XPTS = [(76.75, 11.125), (76.45, 10.62), (76.05, 10.22),
        (75.5, 10.14), (74.8, 10.1), (74.15, 10.28),
        (73.4, 10.34), (72.6, 10.34), (72.375, 10.0)]
for a, b in zip(XPTS, XPTS[1:]):
    seg('XO', 'F', a, b)
# +3V3A feed re-lay
via('+3V3A', (74.7, 10.75))
seg('+3V3A', 'F', (75.125, 11.125), (74.7, 10.75))
seg('+3V3A', 'B', (74.7, 10.75), (74.2, 8.625))
# +3V3D via shrink
via('+3V3D', (70.875, 12.625))
# I2C_SCL via move
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
print('all in-model gates pass')

board = pcbnew.LoadBoard(SRC)
codes = {n: board.GetNetcodeFromNetname(n)
         for n in ('XO', 'PHY_1V8A', '+3V3A', '+3V3D', 'I2C_SCL')}

def hit(t, spec):
    kind, net, x, y = spec
    if t.GetNetname() != net:
        return False
    if kind == 'via':
        if not isinstance(t, pcbnew.PCB_VIA):
            return False
        p = pcbnew.ToMM(t.GetPosition())
        return abs(p[0] - x) < 0.01 and abs(p[1] - y) < 0.01
    if isinstance(t, pcbnew.PCB_VIA):
        return False
    a = pcbnew.ToMM(t.GetStart())
    b = pcbnew.ToMM(t.GetEnd())
    return (abs(a[0] - x) < 0.01 and abs(a[1] - y) < 0.01) or \
           (abs(b[0] - x) < 0.01 and abs(b[1] - y) < 0.01)

victims = [t for t in board.GetTracks()
           if any(hit(t, s) for s in RIP_SPECS)]
print(f'ripping {len(victims)} board objects (expect 14)')
for t in victims:
    board.Remove(t)

def add_track(net, a, b, layer, w=0.2):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(a[0]), pcbnew.FromMM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(b[0]), pcbnew.FromMM(b[1])))
    t.SetWidth(pcbnew.FromMM(w))
    t.SetLayer(LAY[layer])
    t.SetNetCode(codes[net])
    board.Add(t)

def add_via(net, pt, dia, drill):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(pt[0]),
                                  pcbnew.FromMM(pt[1])))
    v.SetWidth(pcbnew.FromMM(dia))
    v.SetDrill(pcbnew.FromMM(drill))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNetCode(codes[net])
    board.Add(v)

for (net, kind, layer, data, hwr) in ADDS:
    if kind == 'via':
        dia = 0.6 if net == 'I2C_SCL' else 0.5
        add_via(net, data, dia, 0.3)
    else:
        add_track(net, data[0], data[1], layer, 0.2)

filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(OUT)
print('saved', OUT)

# reload census: per-net item counts vs expectation
b2 = pcbnew.LoadBoard(OUT)
from collections import Counter
c = Counter(t.GetNetname() for t in b2.GetTracks())
for n in ('XO', 'PHY_1V8A', '+3V3A', '+3V3D', 'I2C_SCL', 'PHY_1V8'):
    print(f'reload {n}: {c[n]} items')

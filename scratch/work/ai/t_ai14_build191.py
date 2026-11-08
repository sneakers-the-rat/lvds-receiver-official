"""t_ai14: pass-191 candidate build on exp220.
Joint U7.25 + PHY_1V8 re-lay (optimizer t_ai12 winner, onward legs
flood-verified t_ai13):
 rip PHY south fanout (3 F segs, via (77.875,10.375), 2 B segs);
 PHY: F stub (77.25,11.562)->(77.25,10.75)->P(77.8688,10.0563) w0.2,
      via P d0.5; B w0.6 P->(76.8,10.9875)->(76.8,14.9875)->(77.8,16.2)
 +3V3A: F stub (77.75,11.562)->Q(77.8625,10.9187) w0.2, via Q d0.5;
      In2 w0.6 Q->(76.6,12.15)->(77.375,13.125)
Every add gated in-model vs statics and vs other-net adds."""
import math, sys
sys.path.insert(0, 'hw')
sys.path.insert(0, 'scratch/work/ai')
import wx
_app = wx.App(False)
import pcbnew
from t_ai_lib import (load_items, pair_clr, pt_margin, seg_margin,
                      in_box_pool, apply_rip, fmt_it)

SRC = 'hw/pdlvds_rx.exp220.kicad_pcb'
OUT = 'scratch/work/ai/exp221cand5.kicad_pcb'
LAY = {'F': pcbnew.F_Cu, 'In2': pcbnew.In2_Cu, 'B': pcbnew.B_Cu}
LI = {'F': 0, 'In2': 1, 'B': 2}

items = load_items(pcbnew.LoadBoard(SRC))
RIP_SPECS = [('seg', 'PHY_1V8', 77.25, 11.562),
             ('seg', 'PHY_1V8', 77.25, 10.812),
             ('seg', 'PHY_1V8', 77.625, 10.625),
             ('via', 'PHY_1V8', 77.875, 10.375),
             ('seg', 'PHY_1V8', 77.875, 10.375),
             ('seg', 'PHY_1V8', 77.875, 12.875)]
statics, n_rip = apply_rip(items, RIP_SPECS)
print(f'ripped {n_rip} model entries')

P = (77.8688, 10.0563)
Q = (77.8625, 10.975)
ADDS = []
# (net, kind, layer, data, hw/rad)
ADDS.append(('PHY_1V8', 'seg', 'F', ((77.25, 11.562), (77.25, 10.75)), 0.1))
ADDS.append(('PHY_1V8', 'seg', 'F', ((77.25, 10.75), P), 0.1))
ADDS.append(('PHY_1V8', 'via', None, P, 0.25))
ADDS.append(('PHY_1V8', 'seg', 'B', (P, (77.35, 10.0)), 0.3))
ADDS.append(('PHY_1V8', 'seg', 'B', ((77.35, 10.0), (76.8, 10.9875)), 0.3))
ADDS.append(('PHY_1V8', 'seg', 'B', ((76.8, 10.9875), (76.8, 14.9875)), 0.3))
ADDS.append(('PHY_1V8', 'seg', 'B', ((76.8, 14.9875), (77.8, 16.2)), 0.3))
ADDS.append(('+3V3A', 'seg', 'F', ((77.75, 11.562), Q), 0.1))
ADDS.append(('+3V3A', 'via', None, Q, 0.25))
ADDS.append(('+3V3A', 'seg', 'In2', (Q, (76.6, 12.15)), 0.3))
ADDS.append(('+3V3A', 'seg', 'In2', ((76.6, 12.15), (77.375, 13.125)), 0.3))

BOX = (74.5, 80.5, 8.0, 17.5)
pools = in_box_pool(statics, BOX, pad=1.2)


def to_item(net, kind, layer, data, hwr):
    if kind == 'via':
        return ('via', net, (data[0], data[1], hwr))
    (a, b) = data
    return ('seg', net, (a[0], a[1], b[0], b[1], hwr))


add_items = {0: [], 1: [], 2: []}
for (net, kind, layer, data, hwr) in ADDS:
    if kind == 'via':
        for li in range(3):
            add_items[li].append(to_item(net, kind, layer, data, hwr))
    else:
        add_items[LI[layer]].append(to_item(net, kind, layer, data, hwr))

fails = []
for (net, kind, layer, data, hwr) in ADDS:
    if kind == 'via':
        for li in range(3):
            m, w = pt_margin(li, data[0], data[1], net, hwr,
                             pools[li] + add_items[li])
            print(f'  gate {net} via {data} L{li}: {m:+.3f}')
            if m < 0:
                fails.append((net, kind, data, li, m, w))
    else:
        li = LI[layer]
        m, w = seg_margin(li, data[0], data[1], net, hwr,
                          pools[li] + add_items[li])
        print(f'  gate {net} seg {data} {layer}: {m:+.3f}')
        if m < 0:
            fails.append((net, kind, data, li, m, w))
if fails:
    print('GATE FAILURES:')
    for f in fails:
        print('  ', f[0], f[1], f[2], 'L', f[3], f'{f[4]:+.3f}',
              'vs', fmt_it(f[5]) if f[5] else '-')
    sys.exit(1)
print('all in-model gates pass')

board = pcbnew.LoadBoard(SRC)
codes = {n: board.GetNetcodeFromNetname(n)
         for n in ('PHY_1V8', '+3V3A', 'GND')}


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
print(f'ripping {len(victims)} board objects (expect 6)')
for t in victims:
    board.Remove(t)


def add_track(net, a, b, layer, w):
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


add_track('PHY_1V8', (77.25, 11.562), (77.25, 10.75), 'F', 0.2)
add_track('PHY_1V8', (77.25, 10.75), P, 'F', 0.2)
add_via('PHY_1V8', P, 0.5, 0.3)
add_track('PHY_1V8', P, (77.35, 10.0), 'B', 0.6)
add_track('PHY_1V8', (77.35, 10.0), (76.8, 10.9875), 'B', 0.6)
add_track('PHY_1V8', (76.8, 10.9875), (76.8, 14.9875), 'B', 0.6)
add_track('PHY_1V8', (76.8, 14.9875), (77.8, 16.2), 'B', 0.6)
add_track('+3V3A', (77.75, 11.562), Q, 'F', 0.2)
add_via('+3V3A', Q, 0.5, 0.3)
add_track('+3V3A', Q, (76.6, 12.15), 'In2', 0.6)
add_track('+3V3A', (76.6, 12.15), (77.375, 13.125), 'In2', 0.6)

filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(OUT)
print('saved', OUT)

"""t_ai8: pass-190 candidate build v2 (+ GND island heals).
 +3V3A U7.6 CONNECTED via groute's all-F path found on ripA
 (t_ab2_groute on the board with the fence ripped).
 Fence re-lay in the same pass:
  - +5V fanout: seg2 + via ripped; via moves to (72.2,13.1) d0.8,
    F seg (72.812,13.75)->(72.2,13.1), In2 joiner up to the trunk.
  - GND stitch via (72.0,14.65) ripped and NOT replaced: refill +
    check_pcb on ripA2 proved C23.2's group stays whole without it
    (redundant via; the F fill island is tied elsewhere).
All adds gated in the exact item model vs statics (exp219 minus
rip set) and vs other-net adds before any copper moves."""
import sys
sys.path.insert(0, 'hw')
sys.path.insert(0, 'scratch/work/ai')
import wx
_app = wx.App(False)
import pcbnew
import t_ai_lib as L

SRC = sys.argv[1] if len(sys.argv) > 1 else 'hw/pdlvds_rx.exp219.kicad_pcb'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'scratch/work/ai/exp220cand3.kicad_pcb'
MM = pcbnew.FromMM
LAY = {'F': pcbnew.F_Cu, 'In2': pcbnew.In2_Cu, 'B': pcbnew.B_Cu}
LAYIDX = {'F': 0, 'In2': 1, 'B': 2}

board = pcbnew.LoadBoard(SRC)
items = L.load_items(board)

RIP_SPECS = [('via', '+5V', 72.125, 13.625),
             ('via', 'GND', 72.0, 14.65)]
statics, nrip = L.apply_rip(items, RIP_SPECS)
# seg2 (72.812,13.75)->(72.125,13.625) ripped by exact endpoint pair;
# seg1 (73.562,13.75)->(72.812,13.75) is KEPT.
def is_seg2(it):
    if it[0] != 'seg' or it[1] != '+5V':
        return False
    d = it[2]
    return (abs(d[0] - 72.812) < 0.01 and abs(d[1] - 13.75) < 0.01 and
            abs(d[2] - 72.125) < 0.01 and abs(d[3] - 13.625) < 0.01) or \
        (abs(d[2] - 72.812) < 0.01 and abs(d[3] - 13.75) < 0.01 and
         abs(d[0] - 72.125) < 0.01 and abs(d[1] - 13.625) < 0.01)
statics2 = {li: [it for it in statics[li] if not is_seg2(it)]
            for li in range(3)}
nseg2 = sum(len(statics[li]) for li in range(3)) - \
    sum(len(statics2[li]) for li in range(3))
print(f'ripped {nrip} via entries + {nseg2} seg2 entries '
      f'(expect 6 + 1)')
found = [it for li in range(3) for it in statics2[li]
         if it[0] == 'seg' and it[1] == '+5V' and
         abs(it[2][0] - 73.562) < 0.01 and abs(it[2][1] - 13.75) < 0.01]
print('kept +5V seg1 entries:', len(found))
RIP_SPECS.append(('seg', '+5V', 72.812, 13.75))

A76 = [((73.125, 14.75), (72.625, 14.625)),
       ((72.625, 14.625), (72.25, 13.875)),
       ((72.25, 13.875), (69.25, 13.875)),
       ((69.25, 13.875), (69.125, 14.375)),
       ((69.125, 14.375), (69.125, 15.5)),
       ((69.125, 15.5), (68.625, 15.875)),
       ((68.625, 15.875), (68.375, 17.5))]
ADDS = []  # (net, kind, layer, geom, rad/hw)
for a, b in A76:
    ADDS.append(('+3V3A', 'seg', 'F', (a, b), 0.1))
ADDS.append(('+5V', 'seg', 'F', ((72.812, 13.75), (72.2, 13.1)), 0.1))
ADDS.append(('+5V', 'via', None, (72.2, 13.1), 0.4))
ADDS.append(('+5V', 'seg', 'In2', ((72.2, 13.1), (72.2, 13.625)), 0.3))
ADDS.append(('+5V', 'seg', 'In2', ((72.125, 13.625), (72.2, 13.625)), 0.3))
# GND fill-island heals (polygon diff pathonly vs exp219refill):
# island13 (C23.2) loses the ripped stitch via -> replacement via
# inside the island; island11 (C27.2 alone) severed by the western
# +3V3A run -> new stitch via. Both d0.6 like the original stitch.
ADDS.append(('GND', 'via', None, (71.8, 14.9), 0.3))
ADDS.append(('GND', 'via', None, (67.3, 16.9), 0.3))

# ---- gate every add vs statics and vs other-net adds ----
def add_as_items(add):
    net, kind, lay, geom, r = add
    if kind == 'via':
        return [(li, ('via', net, (geom[0], geom[1], r),
                      L.netclass(net)[1])) for li in range(3)]
    a, b = geom
    return [(LAYIDX[lay], ('seg', net, (a[0], a[1], b[0], b[1], r),
                            L.netclass(net)[1]))]

fails = []
for idx, add in enumerate(ADDS):
    net, kind, lay, geom, r = add
    others = []
    for jdx, o in enumerate(ADDS):
        if jdx != idx and o[0] != net:
            others.extend(add_as_items(o))
    if kind == 'via':
        for li in range(3):
            pool = statics2[li] + [it for (l2, it) in others if l2 == li]
            m, w = L.pt_margin(li, geom[0], geom[1], net, r, pool)
            if m < 0:
                fails.append(f'{net} via {geom} L{li}: {m:+.3f} vs '
                             f'{L.fmt_it(w)}')
            else:
                print(f'  gate {net} via {geom} L{li}: {m:+.3f}')
    else:
        li = LAYIDX[lay]
        pool = statics2[li] + [it for (l2, it) in others if l2 == li]
        a, b = geom
        m, w = L.seg_margin(li, a, b, net, r, pool)
        if m < 0:
            fails.append(f'{net} seg {a}->{b} {lay}: {m:+.3f} vs '
                         f'{L.fmt_it(w)}')
        else:
            print(f'  gate {net} seg {a}->{b} {lay}: {m:+.3f}')
if fails:
    print('GATE FAILURES:')
    for f in fails:
        print('  ', f)
    sys.exit(1)
print('all in-model gates pass')

# ---- execute on the board (netcodes BEFORE any Remove) ----
codes = {n: board.GetNetcodeFromNetname(n)
         for n in ('+3V3A', '+5V', 'GND')}

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
    p1 = (abs(a[0] - x) < 0.01 and abs(a[1] - y) < 0.01 and
          abs(b[0] - 72.125) < 0.01 and abs(b[1] - 13.625) < 0.01)
    p2 = (abs(b[0] - x) < 0.01 and abs(b[1] - y) < 0.01 and
          abs(a[0] - 72.125) < 0.01 and abs(a[1] - 13.625) < 0.01)
    return p1 or p2

victims = [t for t in board.GetTracks()
           if any(hit(t, s) for s in RIP_SPECS)]
print(f'ripping {len(victims)} board objects (expect 3)')
for t in victims:
    board.Remove(t)

def add_track(net, a, b, layname, w):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(MM(b[0]), MM(b[1])))
    t.SetWidth(MM(w))
    t.SetLayer(LAY[layname])
    t.SetNetCode(codes[net])
    board.Add(t)

def add_via(net, V, dia, drill):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(MM(V[0]), MM(V[1])))
    v.SetWidth(MM(dia))
    v.SetDrill(MM(drill))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNetCode(codes[net])
    board.Add(v)

for a, b in A76:
    add_track('+3V3A', a, b, 'F', 0.2)
add_track('+5V', (72.812, 13.75), (72.2, 13.1), 'F', 0.2)
add_via('+5V', (72.2, 13.1), 0.8, 0.4)
add_track('+5V', (72.2, 13.1), (72.2, 13.625), 'In2', 0.6)
add_track('+5V', (72.125, 13.625), (72.2, 13.625), 'In2', 0.6)
add_via('GND', (71.8, 14.9), 0.6, 0.3)
add_via('GND', (67.3, 16.9), 0.6, 0.3)

filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(OUT)
print('saved', OUT)

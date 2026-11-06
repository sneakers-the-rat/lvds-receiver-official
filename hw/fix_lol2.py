#!/usr/bin/env python3
"""Connect CDR_LOL's lone pad U6.36 (queue item 6b), attempt 2.

Attempt 1 record: four dive sites on the y=2.75 latitude all
fenced; the cleanest, (70.20,2.75), had exactly ONE blocker --
ULPI_NXT's B diagonal (70.05,0.12)->(70.30,5.30). F weaves south
and west are fenced by CAP_CLK's escape run + staircase.

Mechanism: relay NXT's B diagonal west (victim repaid in-pass,
groups asserted unchanged), then LOL dives at (70.20,2.75) and
runs In2 west onto the main group's trunk at x=56.62.

Run: xvfb-run -a python3 hw/fix_lol2.py IN OUT
"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import check_pcb, repair6, repair
from hand_stub import build_items

check_pcb.SURFACE = {pcbnew.F_Cu, pcbnew.B_Cu}
need_for = check_pcb.need_for
MM = pcbnew.FromMM
F, B = pcbnew.F_Cu, pcbnew.B_Cu
IN2 = pcbnew.In2_Cu
SAFETY = 0.005
W = 0.20
VD = 0.60

SRC, OUT = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(SRC)
items = build_items(board)
print(f"items: {len(items)}")


def seg_shape(a, b, w):
    return pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])),
                                pcbnew.VECTOR2I(MM(b[0]), MM(b[1])),
                                MM(w))


def blockers(net, layers, shape, skip_net=None):
    out = []
    for kind, n2, l2, s2, desc in items:
        if n2 == net or kind == 'zone':
            continue
        shared = layers & l2
        if not shared:
            continue
        need = need_for(net, n2, shared)
        if s2.Collide(shape, MM(need - 0.001 + SAFETY)):
            out.append((n2, desc, need))
    return out


def ngroups(board, net):
    return len(repair.compute_groups(board)[net])


def add_track(a, b, layer, net):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(MM(b[0]), MM(b[1])))
    t.SetWidth(MM(W))
    t.SetLayer(layer)
    t.SetNet(board.FindNet(net))
    board.Add(t)
    return t


assert ngroups(board, 'CDR_LOL') == 2
nxt0 = ngroups(board, 'ULPI_NXT')
print('NXT groups before:', nxt0)

# --- 1. NXT B relay candidates (west bow), exact-tested on B
RELAYS = [
    [((70.05, 0.12), (69.80, 1.40)), ((69.80, 1.40), (69.80, 4.00)),
     ((69.80, 4.00), (70.30, 5.30))],
    [((70.05, 0.12), (69.65, 1.40)), ((69.65, 1.40), (69.65, 4.00)),
     ((69.65, 4.00), (70.30, 5.30))],
    [((70.05, 0.12), (69.80, 2.70)), ((69.80, 2.70), (70.30, 5.30))],
]
relay = None
for cand in RELAYS:
    ok = True
    for a, b in cand:
        bl = blockers('ULPI_NXT', {B}, seg_shape(a, b, W))
        if bl:
            print('NXT relay', a, '->', b, 'blockers:', bl[:4])
            ok = False
            break
    if ok:
        relay = cand
        break
if relay is None:
    print('ABORT: no NXT relay clean')
    sys.exit(1)
print('NXT relay chosen:', relay[0][0], '...', relay[-1][1])

# --- 2. LOL dive + In2 run, tested against the CURRENT board except
#        the NXT B diagonal being relayed (exclude that one segment
#        by testing LOL pieces with NXT's old diagonal removed from
#        the item list is complex; instead test the via now -- it
#        must be clean vs everything except that diagonal).
VIA = (70.20, 2.75)
c = pcbnew.SHAPE_CIRCLE(pcbnew.VECTOR2I(MM(VIA[0]), MM(VIA[1])), MM(VD / 2))
bl = blockers('CDR_LOL', {F, pcbnew.In1_Cu, IN2, B}, c)
print('LOL via blockers (pre-relay):', bl[:5] if bl else 'none')
bl = [x for x in bl if x[0] != 'ULPI_NXT']
if bl:
    print('ABORT: LOL via blocked beyond the relayed diagonal:', bl[:4])
    sys.exit(1)
bl = blockers('CDR_LOL', {F}, seg_shape((70.50, 2.75), VIA, W))
print('LOL stub ext blockers:', bl[:4] if bl else 'none')
if bl:
    print('ABORT: stub extension blocked')
    sys.exit(1)

RUNS = [
    [(VIA, (56.62, 2.75))],
    [(VIA, (63.00, 2.75)), ((63.00, 2.75), (63.00, 2.25)),
     ((63.00, 2.25), (56.62, 2.25))],
    [(VIA, (63.00, 2.75)), ((63.00, 2.75), (63.00, 3.25)),
     ((63.00, 3.25), (56.62, 3.25))],
]
run = None
for cand in RUNS:
    ok = True
    for a, b in cand:
        bl = blockers('CDR_LOL', {IN2}, seg_shape(a, b, W))
        if bl:
            print('In2 run', a, '->', b, 'blockers:', bl[:4])
            ok = False
            break
    if ok:
        run = cand
        break
if run is None:
    print('ABORT: no In2 run clean')
    sys.exit(1)

# --- 3. apply: rip NXT's B diagonal, lay relay, lay LOL
ripped = 0
for t in list(board.GetTracks()):
    if isinstance(t, pcbnew.PCB_VIA):
        continue
    if t.GetNetname() != 'ULPI_NXT' or t.GetLayer() != B:
        continue
    a = (pcbnew.ToMM(t.GetStart().x), pcbnew.ToMM(t.GetStart().y))
    b = (pcbnew.ToMM(t.GetEnd().x), pcbnew.ToMM(t.GetEnd().y))
    if {a, b} == {(70.05, 0.12), (70.30, 5.30)}:
        board.Remove(t)
        ripped += 1
print('NXT B diagonal ripped:', ripped)
assert ripped == 1
for a, b in relay:
    add_track(a, b, B, 'ULPI_NXT')
assert ngroups(board, 'ULPI_NXT') == nxt0, 'NXT partition changed!'

add_track((70.50, 2.75), VIA, F, 'CDR_LOL')
v = pcbnew.PCB_VIA(board)
v.SetPosition(pcbnew.VECTOR2I(MM(VIA[0]), MM(VIA[1])))
v.SetDrill(MM(0.30))
v.SetWidth(MM(VD))
v.SetViaType(pcbnew.VIATYPE_THROUGH)
v.SetLayerPair(F, B)
v.SetNet(board.FindNet('CDR_LOL'))
board.Add(v)
for a, b in run:
    add_track(a, b, IN2, 'CDR_LOL')

g1 = ngroups(board, 'CDR_LOL')
print('LOL groups after:', g1)
assert g1 == 1, 'join failed'
repair6.save_checkpoint(board, OUT)
print('saved', OUT)

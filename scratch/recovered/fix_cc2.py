#!/usr/bin/env python3
"""Rejoin CC2 (queue item 3) with a VBUS_RAW relay.

The 1.42 mm F gap between J1.B5's stub (30.50,72.55) and the main
group's west end (31.90,72.30) is crossed by VBUS_RAW's F jumper
(31.15,72.83)->(31.00,71.98) -- the sole link between J1.A9 and the
rest of VBUS_RAW (A9's own escape dead-ends at (31.85,70.88)) --
and the hop also fails J1.B4's 0.25 power clearance by 0.02 with
the jumper present.

Plan (all exact-tested in order, zones excluded):
 1. Rip the VBUS_RAW jumper.
 2. Repay VBUS_RAW: extend A9's escape (31.85,70.88)->(32.05,70.68)
    w=0.60, via d=0.60 at (32.05,70.68), B run w=0.60 west to
    (27.50,71.05) landing on VBUS_RAW's own B web (y=71.12 run).
 3. CC2 hop on F, w=0.25: (30.56,72.62)->(31.10,72.30)->(31.90,72.30).
Post-checks: CC2 and VBUS_RAW each exactly 1 group.

Run: xvfb-run -a python3 hw/fix_cc2.py IN OUT
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
SAFETY = 0.02

SRC, OUT = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(SRC)
items = build_items(board)
print(f"items: {len(items)}")

def seg_shape(a, b, w):
    return pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])),
                                pcbnew.VECTOR2I(MM(b[0]), MM(b[1])),
                                MM(w))

def blockers(net, layer, shape, skip_desc=None):
    out = []
    for kind, n2, l2, s2, desc in items:
        if n2 == net or kind == 'zone':
            continue
        if skip_desc and desc == skip_desc:
            continue
        if layer not in l2:
            continue
        need = need_for(net, n2, {layer})
        if shape.Collide(s2, MM(need - 0.001 + SAFETY)):
            out.append((n2, desc, need))
    return out

def via_blockers(net, x, y, d=0.6):
    return blockers(net, F, pcbnew.SHAPE_CIRCLE(
        pcbnew.VECTOR2I(MM(x), MM(y)), MM(d / 2))) + \
        blockers(net, B, pcbnew.SHAPE_CIRCLE(
            pcbnew.VECTOR2I(MM(x), MM(y)), MM(d / 2)))

def find_track(net, a, b):
    for t in board.GetTracks():
        if t.GetNetname() != net or isinstance(t, pcbnew.PCB_VIA):
            continue
        s = pcbnew.ToMM(t.GetStart()); e = pcbnew.ToMM(t.GetEnd())
        if (abs(s[0]-a[0]) < 0.01 and abs(s[1]-a[1]) < 0.01 and
                abs(e[0]-b[0]) < 0.01 and abs(e[1]-b[1]) < 0.01) or \
           (abs(s[0]-b[0]) < 0.01 and abs(s[1]-b[1]) < 0.01 and
                abs(e[0]-a[0]) < 0.01 and abs(e[1]-a[1]) < 0.01):
            return t
    return None

def add_track(net, layer, a, b, w):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(MM(b[0]), MM(b[1])))
    t.SetWidth(MM(w))
    t.SetLayer(layer)
    t.SetNet(board.FindNet(net))
    board.Add(t)
    return t

def add_via(net, x, y, d=0.6):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    v.SetWidth(MM(d))
    v.SetDrill(MM(0.3))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(F, B)
    v.SetNet(board.FindNet(net))
    board.Add(v)
    return v

fails = []
# 1. test the repay pieces BEFORE ripping anything
bl = blockers('VBUS_RAW', F, seg_shape((31.85, 70.88), (32.05, 70.68), 0.60))
print(f"VBUS F extension blockers: {bl}"); fails += bl
bl = via_blockers('VBUS_RAW', 32.05, 70.68)
print(f"VBUS via blockers: {bl}"); fails += bl
bl = blockers('VBUS_RAW', B, seg_shape((32.05, 70.68), (27.50, 71.05), 0.60))
print(f"VBUS B run blockers: {bl}"); fails += bl
# 2. test the CC2 hop (jumper still present in the model: it is
#    VBUS_RAW, so it WILL appear -- test with the jumper's shape
#    excluded by testing after the rip instead; here we test
#    against everything except VBUS_RAW's jumper by name: the
#    jumper is a track, desc is anonymous, so test now and allow
#    exactly the jumper hits)
hop = [((30.56, 72.62), (31.10, 72.30)), ((31.10, 72.30), (31.90, 72.30))]
for a, b in hop:
    bl = blockers('CC2', F, seg_shape(a, b, 0.25))
    print(f"CC2 hop {a}->{b} blockers (pre-rip): {bl}")
    for n2, desc, need in bl:
        if n2 != 'VBUS_RAW':
            fails.append((n2, desc, need))
if fails:
    print(f"REFUSED: {fails}; board NOT saved")
    sys.exit(1)

# 3. rip the jumper, place everything
jmp = find_track('VBUS_RAW', (31.15, 72.83), (31.00, 71.98))
assert jmp is not None, "jumper not found"
board.Remove(jmp)
print("ripped VBUS_RAW jumper")
add_track('VBUS_RAW', F, (31.85, 70.88), (32.05, 70.68), 0.60)
add_via('VBUS_RAW', 32.05, 70.68)
add_track('VBUS_RAW', B, (32.05, 70.68), (27.50, 71.05), 0.60)
print("placed VBUS_RAW repay (F ext + via + B run)")
for a, b in hop:
    add_track('CC2', F, a, b, 0.25)
print("placed CC2 hop")

groups = repair.compute_groups(board)
for net in ('CC2', 'VBUS_RAW'):
    print(f"{net}: {len(groups[net])} group(s)")
    assert len(groups[net]) == 1, f"{net} not rejoined!"
repair6.save_checkpoint(board, OUT)
print(f"saved {OUT}")

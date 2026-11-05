#!/usr/bin/env python3
"""U10 locality surgery (Class A): reposition the +5V trunk that
fences U10's east via window, then place U10.7's via escape.

Evidence chain (results/probe-u10-*.txt): U10.7's only via window
is due east; its disc at dv>=1.15 is blocked by exactly one item —
the +5V trunk segment (18.050,-20.500)->(18.375,0.375) w=0.60 on
F_Cu. At dv=1.05..1.12 the disc clears everything (window between
the pad row's reach and the trunk). This script:
  1. replaces the trunk segment with a collision-tested polyline
     jogged east around the U10 latitude band (same net, same
     width, same endpoints — +5V stays whole);
  2. places U10.7's escape: F neck pad->(17.20,-14.50), via
     0.6/0.3, In2 tail east — every placed shape collision-tested
     against the post-jog field before it is added.
Usage: python3 hw/surgery_u10_jog.py <src> <out>
"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import check_pcb
import repair6
from hand_stub import build_items
check_pcb.SURFACE = {pcbnew.F_Cu, pcbnew.B_Cu}
need_for = check_pcb.need_for
MM, TM = pcbnew.FromMM, pcbnew.ToMM

SRC, OUT = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(SRC)

# --- find and remove the trunk segment -------------------------
A = (18.050, -20.500)
B = (18.375, 0.375)
trunk = None
for t in board.GetTracks():
    if t.GetNetname() != '+5V' or t.Type() == pcbnew.PCB_VIA_T:
        continue
    s, e = t.GetStart(), t.GetEnd()
    pts = {(round(TM(s.x), 3), round(TM(s.y), 3)),
           (round(TM(e.x), 3), round(TM(e.y), 3))}
    if pts == {A, B}:
        trunk = t
        break
assert trunk is not None, 'trunk segment not found'
board.Remove(trunk)
print('trunk removed')

items = build_items(board)

def seg_ok(net, x1, y1, x2, y2, w, layer):
    s = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(x1), MM(y1)),
                             pcbnew.VECTOR2I(MM(x2), MM(y2)), MM(w))
    for kind, n2, l2, s2, desc in items:
        if n2 == net or kind == 'zone':
            continue
        if layer not in l2:
            continue
        need = need_for(net, n2, {layer})
        if s.Collide(s2, MM(need - 0.001)):
            return (n2, desc)
    return None

def on_line(y):
    t = (y - A[1]) / (B[1] - A[1])
    return (A[0] + t * (B[0] - A[0]), y)

# --- jogged replacement polyline -------------------------------
placed = False
for jx in (19.30, 19.70, 20.10, 18.95):
    p0 = A
    p1 = on_line(-17.5)
    p2 = (jx, -16.6)
    p3 = (jx, -12.9)
    p4 = on_line(-11.5)
    p5 = B
    poly = [p0, p1, p2, p3, p4, p5]
    bad = None
    for i in range(len(poly) - 1):
        bad = seg_ok('+5V', *poly[i], *poly[i + 1], 0.60, pcbnew.F_Cu)
        if bad:
            break
    if bad:
        print(f'jog x={jx}: blocked by {bad}')
        continue
    netobj = board.FindNet('+5V')
    for i in range(len(poly) - 1):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(MM(poly[i][0]), MM(poly[i][1])))
        t.SetEnd(pcbnew.VECTOR2I(MM(poly[i + 1][0]), MM(poly[i + 1][1])))
        t.SetWidth(MM(0.60))
        t.SetLayer(pcbnew.F_Cu)
        t.SetNet(netobj)
        board.Add(t)
    print(f'jog placed at x={jx}: ' +
          ' -> '.join(f'({x:.2f},{y:.2f})' for x, y in poly))
    placed = True
    break
assert placed, 'no jog depth cleared'
items = build_items(board)

# --- U10.7 escape: neck + via + In2 tail ------------------------
ALL = {pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu}
def disc_ok(net, x, y):
    s = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(x), MM(y)),
                             pcbnew.VECTOR2I(MM(x), MM(y)), MM(0.6))
    for kind, n2, l2, s2, desc in items:
        if n2 == net or kind == 'zone':
            continue
        need = need_for(net, n2, l2)
        if s.Collide(s2, MM(need - 0.001)):
            return (n2, desc)
    return None

VX, VY = 17.20, -14.50
bad = seg_ok('HV_GATE', 16.79, VY, VX, VY, 0.25, pcbnew.F_Cu)
assert not bad, f'neck blocked: {bad}'
bad = disc_ok('HV_GATE', VX, VY)
assert not bad, f'disc blocked: {bad}'
tail = None
for (tx, ty) in ((19.20, VY), (18.70, VY), (19.20, -13.00),
                 (19.20, -16.00), (18.70, -13.50), (18.70, -15.50)):
    if not seg_ok('HV_GATE', VX, VY, tx, ty, 0.25, pcbnew.In2_Cu):
        tail = (tx, ty)
        break
assert tail, 'no In2 tail cleared'
netobj = board.FindNet('HV_GATE')
t = pcbnew.PCB_TRACK(board)
t.SetStart(pcbnew.VECTOR2I(MM(16.79), MM(VY)))
t.SetEnd(pcbnew.VECTOR2I(MM(VX), MM(VY)))
t.SetWidth(MM(0.25))
t.SetLayer(pcbnew.F_Cu)
t.SetNet(netobj)
board.Add(t)
v = pcbnew.PCB_VIA(board)
v.SetPosition(pcbnew.VECTOR2I(MM(VX), MM(VY)))
v.SetWidth(MM(0.6))
v.SetDrill(MM(0.3))
v.SetNet(netobj)
board.Add(v)
t2 = pcbnew.PCB_TRACK(board)
t2.SetStart(pcbnew.VECTOR2I(MM(VX), MM(VY)))
t2.SetEnd(pcbnew.VECTOR2I(MM(tail[0]), MM(tail[1])))
t2.SetWidth(MM(0.25))
t2.SetLayer(pcbnew.In2_Cu)
t2.SetNet(netobj)
board.Add(t2)
print(f'U10.7 escape placed: neck (16.79,{VY})->({VX},{VY}), '
      f'via @({VX},{VY}), In2 tail ->({tail[0]},{tail[1]})')

repair6.save_checkpoint(board, OUT)
print('saved', OUT)

#!/usr/bin/env python3
"""U10 locality surgery (Class A): U10.7's via escape, no rip.

Evidence (results/probe-u10-fine-dv.txt): U10.7 (HV_GATE) has a
clean via window due east at dv 1.05..1.12 — neck and disc clear
of everything on the current field (hand_via's coarse dv grid,
1.00/1.15, straddles the window and misses it). The companion
plan to jog the +5V trunk east for a second window FAILED:
a MOS_G track fences every jog depth (results/surgery-u10-jog.txt)
— so this pass places only the one proven escape: F neck
(16.79,-14.50)->(17.20,-14.50), via 0.6/0.3 at (17.20,-14.50),
In2 tail east. Every shape is collision-tested before placement.
Usage: python3 hw/surgery_u10_escape.py <src> <out>
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
ALL = {pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu}

SRC, OUT = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(SRC)
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

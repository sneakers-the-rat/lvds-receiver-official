#!/usr/bin/env python3
"""U10 locality surgery (Class A): U10.9's via escape, no rip.

Evidence (results/probe-u10-dense-exp16.txt): the pass-78 "row
arithmetic" seal priced U10.9's escape at a 0.25 pair clearance the
tools never demanded (the U10 control nets are default class 0.20
in check_pcb/router alike). A dense 2D retest with the audit's own
need_for found exactly ONE clear via site for U10.9 on the current
board: (17.25,-15.45) — 0.05 mm north of the pin latitude, inside
the dv 1.05..1.12 east window family but offset in y, which the
radial probes (fixed compass angles, coarse dv grid) never sampled.
Neck width 0.25 tried first (netclass width); 0.20 (the probe-proven
width, router NECK_W) is the recorded fallback. Every shape is
collision-tested before placement.
Usage: python3 hw/surgery_u10_9_escape.py <src> <out>
"""
import sys, math
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import check_pcb
from hand_stub import build_items
check_pcb.SURFACE = {pcbnew.F_Cu, pcbnew.B_Cu}
need_for = check_pcb.need_for
MM, TM = pcbnew.FromMM, pcbnew.ToMM
ALL = {pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu}

SRC, OUT = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(SRC)
items = build_items(board)

NET = 'HV_SHDN'
VX, VY = 17.25, -15.45
pad = None
for fp in board.GetFootprints():
    if fp.GetReference() != 'U10':
        continue
    for p in fp.Pads():
        if p.GetNumber() == '9':
            pad = p
assert pad is not None and pad.GetNetname() == NET
px, py = TM(pad.GetPosition())
bb = pad.GetBoundingBox()
hx, hy = TM(bb.GetWidth()) / 2, TM(bb.GetHeight()) / 2
dx, dy = VX - px, VY - py
dist = math.hypot(dx, dy)
ca, sa = dx / dist, dy / dist
ext = min(hx / abs(ca) if ca else 1e9, hy / abs(sa) if sa else 1e9)
startd = max(ext - 0.08, 0.25 * ext)
SX, SY = px + startd * ca, py + startd * sa

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

bad = disc_ok(NET, VX, VY)
assert not bad, f'disc blocked: {bad}'
neck_w = None
for w in (0.25, 0.20):
    if not seg_ok(NET, SX, SY, VX, VY, w, pcbnew.F_Cu):
        neck_w = w
        break
assert neck_w, 'neck blocked at 0.25 and 0.20'
tail = None
for (tx, ty) in ((19.20, VY), (18.70, VY), (19.20, -14.45),
                 (19.20, -16.45), (18.70, -14.95), (18.70, -15.95)):
    if not seg_ok(NET, VX, VY, tx, ty, 0.25, pcbnew.In2_Cu):
        tail = (tx, ty)
        break
assert tail, 'no In2 tail cleared'
netobj = board.FindNet(NET)
t = pcbnew.PCB_TRACK(board)
t.SetStart(pcbnew.VECTOR2I(MM(SX), MM(SY)))
t.SetEnd(pcbnew.VECTOR2I(MM(VX), MM(VY)))
t.SetWidth(MM(neck_w))
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
board.Save(OUT)
print(f'U10.9 escape placed: neck ({SX:.2f},{SY:.2f})->({VX},{VY}) '
      f'w={neck_w}, via @({VX},{VY}), In2 tail ->({tail[0]},{tail[1]})')
print(f'saved {OUT}')

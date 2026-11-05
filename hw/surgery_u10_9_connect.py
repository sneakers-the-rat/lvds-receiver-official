#!/usr/bin/env python3
"""U10.9 HV_SHDN connection (Class A, pass 80 second half): extend
the pass-80 escape's In2 tail around the HV cluster to the divider
web and land on the main group.

Vehicle history on this pair (all recorded in results/):
heal_nets refused (STILL isolated, results/heal-hvshdn-exp18.txt);
thread.py pair gate 3 mm; thread_far refused (gap 6.28,
results/thread-hvshdn-exp19.txt). The direct westward In2 corridor
at the pin latitude is fenced by the HV_FBX/HV_GATE In2 webs
(hw/probe_path.py). The placed path detours south into the open
strip on In2 — every segment probe-verified CLEAR with
hw/probe_path.py at the audit's need_for before placement:
  (19.2,-15.45) -> (20.5,-15.45) -> (20.5,-21.0) -> (9.5,-21.0)
  -> (9.5,-18.9), then a via up and a short F neck into the main
group's track near (9.225,-18.975) (nearest main item per
results/groups-hvshdn-exp18.txt). Via site and neck targets are
candidate-scanned in-script with the same collision asserts as the
surgery scripts.
Usage: python3 hw/surgery_u10_9_connect.py <src> <out>
"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import check_pcb
from hand_stub import build_items
check_pcb.SURFACE = {pcbnew.F_Cu, pcbnew.B_Cu}
need_for = check_pcb.need_for
MM = pcbnew.FromMM
ALL = {pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu}

SRC, OUT = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(SRC)
items = build_items(board)
NET = 'HV_SHDN'

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

path = [(19.2, -15.45), (20.5, -15.45), (20.5, -21.0),
        (9.5, -21.0), (9.5, -18.9)]
for (x1, y1), (x2, y2) in zip(path, path[1:]):
    bad = seg_ok(NET, x1, y1, x2, y2, 0.25, pcbnew.In2_Cu)
    assert not bad, f'In2 seg ({x1},{y1})->({x2},{y2}) blocked: {bad}'

landing = None
for (vx, vy) in ((9.5, -18.9), (9.3, -18.9), (9.7, -18.9),
                 (9.5, -18.6), (9.5, -19.2)):
    if disc_ok(NET, vx, vy):
        continue
    for (tx, ty) in ((9.225, -18.975), (9.35, -18.95), (9.1, -19.0),
                     (8.875, -17.125)):
        if not seg_ok(NET, vx, vy, tx, ty, 0.25, pcbnew.F_Cu):
            landing = (vx, vy, tx, ty)
            break
    if landing:
        break
assert landing, 'no landing via+neck cleared'
vx, vy, tx, ty = landing

netobj = board.FindNet(NET)
def add_track(x1, y1, x2, y2, w, layer):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MM(x1), MM(y1)))
    t.SetEnd(pcbnew.VECTOR2I(MM(x2), MM(y2)))
    t.SetWidth(MM(w))
    t.SetLayer(layer)
    t.SetNet(netobj)
    board.Add(t)

for (x1, y1), (x2, y2) in zip(path, path[1:]):
    add_track(x1, y1, x2, y2, 0.25, pcbnew.In2_Cu)
v = pcbnew.PCB_VIA(board)
v.SetPosition(pcbnew.VECTOR2I(MM(vx), MM(vy)))
v.SetWidth(MM(0.6))
v.SetDrill(MM(0.3))
v.SetNet(netobj)
board.Add(v)
add_track(vx, vy, tx, ty, 0.25, pcbnew.F_Cu)
board.Save(OUT)
print(f'HV_SHDN connected: In2 detour {path}, via @({vx},{vy}), '
      f'F neck ->({tx},{ty})')
print(f'saved {OUT}')

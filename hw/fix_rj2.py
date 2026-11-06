#!/usr/bin/env python3
"""APD_K RJ2.2 leg, step 1: free the fanout ray (queue item 1,
leg 3 of 3).

RJ2.2's pocket is tiled at the 1.0 mm class (disc scan: the only
clear via sites in x[10.5,17.5] y[49,60] are the cluster at
(15.5-16.25,52.5-52.75), and every F neck to them is walled by
the +3V3D via (14.88,54.12), APD_A_ALT's via (15.57,55.03), SW2's
web, or APD_A's x=13.82 vertical). One tile is cheap to move:
APD_A_ALT's F bar (13.21,55.03)->(15.57,55.03). APD_A_ALT is an
LV net (not in HV_NETS), so it may dive at (13.21,55.03) -- its
own diagonal's end -- where the disc clears RJ1.2's pad at the
0.2 class, and run In1 (empty here) east onto its existing via
(15.57,55.03). Ripping the bar opens the NE diagonal corridor
for the heal that follows (step 2, separate run + audit).

Every placed shape is exact-tested (zones excluded) before
placement; any block aborts unsaved.

Run: xvfb-run -a python3 hw/fix_rj2.py IN OUT
"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import check_pcb, repair6
from hand_stub import build_items

check_pcb.SURFACE = {pcbnew.F_Cu, pcbnew.B_Cu}
need_for = check_pcb.need_for
MM = pcbnew.FromMM
F, B, IN1, IN2 = (pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In1_Cu,
                  pcbnew.In2_Cu)
ALL = {F, IN1, IN2, B}
SAFETY = 0.02
NET = 'APD_A_ALT'

SRC, OUT = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(SRC)
items = build_items(board)
print(f"items before rip: {len(items)}")

def seg_shape(a, b, w):
    return pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])),
                                pcbnew.VECTOR2I(MM(b[0]), MM(b[1])),
                                MM(w))

def disc_shape(p, d):
    return pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(p[0]), MM(p[1])),
                                pcbnew.VECTOR2I(MM(p[0]), MM(p[1])),
                                MM(d))

def blockers(net, shape, layers, items):
    out = []
    for kind, n2, l2, s2, desc in items:
        if n2 == net or kind == 'zone':
            continue
        shared = layers & l2
        if not shared:
            continue
        need = need_for(net, n2, shared)
        if shape.Collide(s2, MM(need - 0.001 + SAFETY)):
            out.append((n2, desc, need))
    return out

def test_or_die(net, label, shape, layers, items):
    bl = blockers(net, shape, layers, items)
    if bl:
        print(f"REFUSED {label}: {bl[:6]}")
        sys.exit(1)
    print(f"clean: {label}")

# via template: APD_A_ALT's own via at (15.57,55.03), d=0.6
tmpl = None
for t in board.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == NET:
        tmpl = t
        break
assert tmpl is not None, "APD_A_ALT via template not found"

# ---- rip the F bar -------------------------------------------------
ripped = 0
for t in list(board.GetTracks()):
    if t.GetNetname() != NET or isinstance(t, pcbnew.PCB_VIA):
        continue
    if t.GetLayer() != F:
        continue
    a = (pcbnew.ToMM(t.GetStart().x), pcbnew.ToMM(t.GetStart().y))
    b = (pcbnew.ToMM(t.GetEnd().x), pcbnew.ToMM(t.GetEnd().y))
    if (abs(a[0] - 13.21) < 0.05 and abs(a[1] - 55.03) < 0.05 and
            abs(b[0] - 15.57) < 0.05 and abs(b[1] - 55.03) < 0.05) or \
       (abs(b[0] - 13.21) < 0.05 and abs(b[1] - 55.03) < 0.05 and
            abs(a[0] - 15.57) < 0.05 and abs(a[1] - 55.03) < 0.05):
        board.Remove(t)
        ripped += 1
print(f"ripped {ripped} APD_A_ALT F bar track(s)")
assert ripped == 1

items = build_items(board)

# ---- repay: via at the diagonal's end + In1 run to its via --------
test_or_die(NET, 'APD_A_ALT via (13.21,55.03)',
            disc_shape((13.21, 55.03), 0.6), ALL, items)
test_or_die(NET, 'APD_A_ALT In1 run',
            seg_shape((13.21, 55.03), (15.57, 55.03), 0.25), {IN1},
            items)

v = pcbnew.PCB_VIA(board)
v.SetPosition(pcbnew.VECTOR2I(MM(13.21), MM(55.03)))
v.SetWidth(tmpl.GetWidth())
v.SetDrill(tmpl.GetDrill())
v.SetViaType(tmpl.GetViaType())
v.SetNet(board.FindNet(NET))
board.Add(v)
print("  placed APD_A_ALT via at (13.21,55.03) d=0.6")
t = pcbnew.PCB_TRACK(board)
t.SetStart(pcbnew.VECTOR2I(MM(13.21), MM(55.03)))
t.SetEnd(pcbnew.VECTOR2I(MM(15.57), MM(55.03)))
t.SetWidth(MM(0.25))
t.SetLayer(IN1)
t.SetNet(board.FindNet(NET))
board.Add(t)
print("  placed APD_A_ALT (13.21,55.03)->(15.57,55.03) w=0.25 "
      "layer=In1")

repair6.save_checkpoint(board, OUT)
print(f"saved {OUT}")

#!/usr/bin/env python3
"""Connect APD_K's R47.2 group (queue item 1, pass after 115).

Diagnosis (all measured on exp107 with the audit's own item model):
- R47.2 (49.33,-1.60) sits in a sewn pocket at the 1.0 mm HV class:
  R47.1 (HV_R29M) west, U9 south, +3V3A via/jog east, GND F track
  (y=0.12) north. hand_stub placed the east stub; hand_via 0/3,
  heal 1 s refusals, thread_far "no thread (gap 7.63)".
- The pocket's last wall is invisible from the F side: TMP_ALERT's
  B.Cu vertical track (49.12,-2.88)->(49.12,27.12) passes 0.21 mm
  west of the pad, and APD_K (HV) needs 1.0 mm from it on EVERY
  layer a via spans -- it blocks every via site on the stub
  (disc probes at (49.85,-1.6) and (50.25,-1.6): sole blocker).
- In1.Cu (layer id 1) is EMPTY in the whole box x[36,57] y[-10,5]
  (the busy buried layer here is In2, id 2: the APD_K staircase,
  the GND riser, HV_FBX). The main APD_K web's via at (41.12,0.62)
  spans every layer. need_for counts HV as 0.3 on buried-only
  pairs, 1.0 on surface pairs -- that is why the B.Cu TMP_ALERT
  track (surface) is the wall and its In2 re-lay is not.

Fix:
1. Repay TMP_ALERT: rip its B vertical south of y=1.20, re-lay
   (49.12,-3.38)->(49.12,1.20) on In2 from its own via, via back
   up at (49.12,1.20), B track (49.12,1.20)->(49.12,27.12).
2. Pour notch (fix_hvraw species): rule areas F+B over
   x[46.20,51.15] y[-3.10,-0.10] so the GND pours hold >=1.0 mm
   from the R47 pocket copper (also cures the standing lines
   'APD_K R47.2 vs GND zone', 'APD_K track@(49.325,-1.6) vs GND
   zone', 'HV_R29M R47.1 vs GND zone').
3. APD_K via (0.6) at (50.05,-1.60) (stub extended east to meet
   it; 49.85 refused by 0.005 mm against the re-laid TMP_ALERT
   In2 riser at the buried 0.3 class); In1 west run
   (50.05,-1.60)->(41.12,-1.60); In1 north (41.12,-1.60)->
   (41.12,0.62) onto the main web's existing via.
Every placed shape is tested against the audit's item model
(check_pcb.need_for, zones excluded -- pour re-carves at refill)
with 0.02 safety before placement; any block aborts unsaved.

Run: xvfb-run -a python3 hw/fix_r47.py IN OUT
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
        print(f"REFUSED {label}: {bl[:5]}")
        sys.exit(1)
    print(f"clean: {label}")

def add_track(net, a, b, w, layer):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(MM(b[0]), MM(b[1])))
    t.SetWidth(MM(w))
    t.SetLayer(layer)
    t.SetNet(board.FindNet(net))
    board.Add(t)
    print(f"  placed {net} {a}->{b} w={w} layer={layer}")

def add_via(net, p, template):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(MM(p[0]), MM(p[1])))
    v.SetWidth(template.GetWidth())
    v.SetDrill(template.GetDrill())
    v.SetViaType(template.GetViaType())
    v.SetNet(board.FindNet(net))
    board.Add(v)
    print(f"  placed {net} via at {p} d={pcbnew.ToMM(v.GetWidth())}")

# via template: TMP_ALERT's own via at (49.12,-3.38), d=0.6
tmpl = None
for t in board.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == 'TMP_ALERT':
        pos = t.GetPosition()
        if abs(pcbnew.ToMM(pos.x) - 49.12) < 0.01 and \
           abs(pcbnew.ToMM(pos.y) + 3.38) < 0.01:
            tmpl = t
            break
assert tmpl is not None, "TMP_ALERT via template not found"

# ---- 1. rip TMP_ALERT B vertical ----------------------------------
ripped = 0
for t in list(board.GetTracks()):
    if t.GetNetname() != 'TMP_ALERT' or isinstance(t, pcbnew.PCB_VIA):
        continue
    if t.GetLayer() != B:
        continue
    a = (pcbnew.ToMM(t.GetStart().x), pcbnew.ToMM(t.GetStart().y))
    b = (pcbnew.ToMM(t.GetEnd().x), pcbnew.ToMM(t.GetEnd().y))
    if abs(a[0] - 49.12) < 0.05 and abs(b[0] - 49.12) < 0.05 and \
            min(a[1], b[1]) < -2.0 and max(a[1], b[1]) > 20.0:
        print(f"  ripping B track {a}->{b}")
        board.Remove(t)
        ripped += 1
print(f"ripped {ripped} TMP_ALERT B vertical track(s)")
assert ripped == 1

items = build_items(board)
print(f"items after rip: {len(items)}")

# ---- 2. pour notch over the R47 pocket ----------------------------
NOTCH = (46.20, -3.10, 51.45, -0.10)   # east edge: via east edge
# 50.35 + 1.0 class + margin (first cut at 51.15 left the via and
# the stub extension 0.8-0.9 mm from the fill: +3 zone lines,
# exp108 audit -- widened, not weakened: the rule never moved)
for layer in (F, B):
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    z.SetDoNotAllowCopperPour(True)
    z.SetLayer(layer)
    o = z.Outline()
    o.NewOutline()
    x0, y0, x1, y1 = NOTCH
    for (x, y) in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        o.Append(pcbnew.VECTOR2I(MM(x), MM(y)))
    board.Add(z)
print(f"notch {NOTCH} added on F+B")

# ---- 3. TMP_ALERT repay -------------------------------------------
test_or_die('TMP_ALERT', 'TMP_ALERT In2 riser',
            seg_shape((49.12, -3.38), (49.12, 1.20), 0.25), {IN2}, items)
test_or_die('TMP_ALERT', 'TMP_ALERT via (49.12,1.20)',
            disc_shape((49.12, 1.20), 0.6), ALL, items)
test_or_die('TMP_ALERT', 'TMP_ALERT B north',
            seg_shape((49.12, 1.20), (49.12, 27.12), 0.25), {B}, items)
add_track('TMP_ALERT', (49.12, -3.38), (49.12, 1.20), 0.25, IN2)
add_via('TMP_ALERT', (49.12, 1.20), tmpl)
add_track('TMP_ALERT', (49.12, 1.20), (49.12, 27.12), 0.25, B)

items = build_items(board)

# ---- 4. APD_K via + In1 haul --------------------------------------
test_or_die('APD_K', 'APD_K F stub extension',
            seg_shape((49.90, -1.60), (50.05, -1.60), 0.40), {F},
            items)
test_or_die('APD_K', 'APD_K via (50.05,-1.60)',
            disc_shape((50.05, -1.60), 0.6), ALL, items)
test_or_die('APD_K', 'APD_K In1 west run',
            seg_shape((50.05, -1.60), (41.12, -1.60), 0.40), {IN1},
            items)
test_or_die('APD_K', 'APD_K In1 north leg',
            seg_shape((41.12, -1.60), (41.12, 0.62), 0.40), {IN1},
            items)
add_track('APD_K', (49.90, -1.60), (50.05, -1.60), 0.40, F)
add_via('APD_K', (50.05, -1.60), tmpl)
add_track('APD_K', (50.05, -1.60), (41.12, -1.60), 0.40, IN1)
add_track('APD_K', (41.12, -1.60), (41.12, 0.62), 0.40, IN1)

repair6.save_checkpoint(board, OUT)
print(f"saved {OUT}")

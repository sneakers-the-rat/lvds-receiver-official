#!/usr/bin/env python3
"""Connect APD_K's D1.5 leg (queue item 1, leg 2 of 3).

Geometry (measured on exp108): D1.5 (8.85,40.00) is ringed by
its own footprint's APD_A pads at 0.40-0.50 mm gaps (D1.4 north,
D1.6 south, D1.2 west). Any surface copper touching D1.5 starts
inside 1.0 mm of an APD_A pad -- the same geometry that produces
the 2 standing APD_K-vs-APD_A lines (docs/07-gated family). The
neck below is ONE diagonal segment, so it can add at most the
two sibling-pad pairs; the script asserts every neck blocker is
APD_A and aborts on anything else. A 0.25-grid disc scan found
the first clear via sites south-east; (11.00,38.50) is the
nearest. From there In1.Cu (empty in this whole region -- the
board's buried routing lives on In2) runs south at x=11.00 and
east at y=30.62 onto the main web's via (13.62,30.62).

Run: xvfb-run -a python3 hw/fix_d15.py IN OUT
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
NET = 'APD_K'

SRC, OUT = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(SRC)
items = build_items(board)
print(f"items: {len(items)}")

def seg_shape(a, b, w):
    return pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])),
                                pcbnew.VECTOR2I(MM(b[0]), MM(b[1])),
                                MM(w))

def disc_shape(p, d):
    return pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(p[0]), MM(p[1])),
                                pcbnew.VECTOR2I(MM(p[0]), MM(p[1])),
                                MM(d))

def blockers(net, shape, layers):
    out = []
    for kind, n2, l2, s2, desc in items:
        if n2 == net or kind == 'zone':
            continue
        shared = layers & l2
        if not shared:
            continue
        need = need_for(net, n2, shared)
        if shape.Collide(s2, MM(need - 0.001 + SAFETY)):
            out.append((kind, n2, desc, need))
    return out

def test_or_die(label, shape, layers):
    bl = blockers(NET, shape, layers)
    if bl:
        print(f"REFUSED {label}: {bl[:6]}")
        sys.exit(1)
    print(f"clean: {label}")

def add_track(a, b, w, layer):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(MM(b[0]), MM(b[1])))
    t.SetWidth(MM(w))
    t.SetLayer(layer)
    t.SetNet(board.FindNet(NET))
    board.Add(t)
    print(f"  placed {a}->{b} w={w} layer={layer}")

# via template: any 0.6 via (APD_A's at (9.90,41.90))
tmpl = None
for t in board.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA) and \
            abs(pcbnew.ToMM(t.GetWidth()) - 0.6) < 0.01:
        tmpl = t
        break
assert tmpl is not None

# ---- neck: the one standing-species exception ---------------------
neck = seg_shape((9.20, 40.00), (11.00, 38.50), 0.40)
bl = blockers(NET, neck, {F})
print(f"neck blockers: {bl}")
foreign = [b for b in bl if b[1] != 'APD_A']
if foreign:
    print(f"REFUSED: neck blocked by non-APD_A items: {foreign}")
    sys.exit(1)
print(f"neck accepted: {len(bl)} blocker(s), all APD_A "
      f"(standing D1-footprint species)")

# ---- via + buried haul: strict ------------------------------------
test_or_die('via (11.00,38.50)', disc_shape((11.00, 38.50), 0.6),
            ALL)
test_or_die('In1 south run',
            seg_shape((11.00, 38.50), (11.00, 30.62), 0.40), {IN1})
test_or_die('In1 east run',
            seg_shape((11.00, 30.62), (13.62, 30.62), 0.40), {IN1})

add_track((9.20, 40.00), (11.00, 38.50), 0.40, F)
v = pcbnew.PCB_VIA(board)
v.SetPosition(pcbnew.VECTOR2I(MM(11.00), MM(38.50)))
v.SetWidth(tmpl.GetWidth())
v.SetDrill(tmpl.GetDrill())
v.SetViaType(tmpl.GetViaType())
v.SetNet(board.FindNet(NET))
board.Add(v)
print("  placed via at (11.00,38.50) d=0.6")
add_track((11.00, 38.50), (11.00, 30.62), 0.40, IN1)
add_track((11.00, 30.62), (13.62, 30.62), 0.40, IN1)

repair6.save_checkpoint(board, OUT)
print(f"saved {OUT}")

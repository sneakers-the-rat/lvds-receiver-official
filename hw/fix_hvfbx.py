#!/usr/bin/env python3
"""Repay HV_FBX (owed from pass 114's APD_K bridge rips).

Geometry (probe_hvfbx.py on exp106): group 1 (R50.2 side) reaches
north-west with an F.Cu spur that ends at (31.275, 0.25), 1.33 mm
from group 0's In2 run at y=0.625 -- different layers, and the only
via site is inside R31.1's (APD_K, 1.0 mm class) exclusion disc:
that is why pass 114's bridge repay refused. The spur's west descent
(12 tracks, x 31.0..33.0, y -4.5..0.25) also carries all 8 of the
APD_K-vs-HV_FBX violation lines.

Fix: rip the spur west of the (33.25,-4.5) track (the spur is a
dead-end branch; R50.2 keeps its path via (33.875,-5.375) and the
In2 east run), and bridge group 0 -> group 1 on F.Cu along the
south corridor y=-4.8: out of R32.1's pad south edge, east under
R32.2 (0.375 mm to the GND pad, LV class 0.2) and under R31.1
(1.725 mm, HV class 1.0), then north into the (33.25,-4.5) track.
Every placed segment is tested against the audit's own item model
(check_pcb.need_for, zones excluded per bridge.py practice -- the
pour re-carves at refill) with 0.02 safety before placement.

Run: xvfb-run -a python3 hw/fix_hvfbx.py IN OUT
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
NET = 'HV_FBX'
W = 0.30
SAFETY = 0.02

SRC, OUT = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(SRC)
items = build_items(board)   # prime SWIG wrappers before any Remove
print(f"items before rip: {len(items)}")

# ---- rip the spur (select by bbox centre, cf. probe dump) ---------
ripped = []
for t in list(board.GetTracks()):
    if t.GetNetname() != NET or isinstance(t, pcbnew.PCB_VIA):
        continue
    if t.GetLayer() != pcbnew.F_Cu:
        continue
    bb = t.GetBoundingBox()
    cx = pcbnew.ToMM(bb.GetX()) + pcbnew.ToMM(bb.GetWidth()) / 2
    cy = pcbnew.ToMM(bb.GetY()) + pcbnew.ToMM(bb.GetHeight()) / 2
    if 30.8 <= cx <= 33.05 and -5.0 <= cy <= 0.4:
        ripped.append((round(cx, 3), round(cy, 3)))
        board.Remove(t)
print(f"ripped {len(ripped)} spur tracks: {ripped}")

# ---- candidate bridges (first clean variant wins) -------------------
VARIANTS = [
    ("F y=-4.80", pcbnew.F_Cu,
     [((29.675, -3.90), (29.675, -4.80)),
      ((29.675, -4.80), (33.25, -4.80)),
      ((33.25, -4.80), (33.25, -4.45))]),
    ("F y=-5.05", pcbnew.F_Cu,
     [((29.675, -3.90), (29.675, -5.05)),
      ((29.675, -5.05), (33.25, -5.05)),
      ((33.25, -5.05), (33.25, -4.45))]),
    ("In2 via-to-via", pcbnew.In2_Cu,
     [((26.125, -4.625), (30.00, -5.00)),
      ((30.00, -5.00), (33.875, -5.375))]),
    ("F y=-5.50 (south of the GND tail)", pcbnew.F_Cu,
     [((29.675, -3.90), (29.675, -5.50)),
      ((29.675, -5.50), (33.25, -5.50)),
      ((33.25, -5.50), (33.25, -4.45))]),
    ("B via-to-via", pcbnew.B_Cu,
     [((26.125, -4.625), (30.00, -5.00)),
      ((30.00, -5.00), (33.875, -5.375))]),
]

items = build_items(board)   # rebuild after the rip
print(f"items after rip: {len(items)}")

def seg_shape(a, b, w):
    return pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])),
                                pcbnew.VECTOR2I(MM(b[0]), MM(b[1])),
                                MM(w))

def blockers_of(segs, layer):
    out = []
    for a, b in segs:
        s = seg_shape(a, b, W)
        for kind, n2, l2, s2, desc in items:
            if n2 == NET or kind == 'zone':
                continue
            shared = {layer} & l2
            if not shared:
                continue
            need = need_for(NET, n2, shared)
            if s.Collide(s2, MM(need - 0.001 + SAFETY)):
                bb = s2.BBox()
                out.append((a, b, n2, desc,
                            round(pcbnew.ToMM(bb.Centre().x), 2),
                            round(pcbnew.ToMM(bb.Centre().y), 2), need,
                            round(pcbnew.ToMM(bb.GetWidth()), 2),
                            round(pcbnew.ToMM(bb.GetHeight()), 2)))
    return out

chosen = None
for name, layer, segs in VARIANTS:
    bl = blockers_of(segs, layer)
    if bl:
        print(f"variant {name}: {len(bl)} blocker(s)")
        for a, b, n2, desc, cx, cy, need, bw, bh in bl[:6]:
            print(f"    {a}->{b} blocked by {n2} {desc} @({cx},{cy}) "
                  f"bbox {bw}x{bh} need {need}")
    else:
        print(f"variant {name}: CLEAN")
        chosen = (name, layer, segs)
        break
if chosen is None:
    print("all bridge variants refused by exact test; board NOT saved")
    sys.exit(1)

name, layer, segs = chosen
netobj = board.FindNet(NET)
for a, b in segs:
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(MM(b[0]), MM(b[1])))
    t.SetWidth(MM(W))
    t.SetLayer(layer)
    t.SetNet(netobj)
    board.Add(t)
    print(f"  placed {a}->{b} w={W} layer={layer} ({name})")
repair6.save_checkpoint(board, OUT)
print(f"saved {OUT}")

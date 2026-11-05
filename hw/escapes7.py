#!/usr/bin/env python3
"""Escape + join surgery batch 7 -- routes from batch 6's named
blockers and the via census:
- U14.6 stub at x=60.45 (0.32 clear of the GND remnant, 0.295
  clear of ILIM_A's track end).
- +3V3A crosses the whole ULPI northbound F bank on In2.
- HV_FBX In2 detours south of the APD_K via (41.12,-4.38).
- HV_INTVCC via-up site hunted around the In2 end (14.6,-10.5)
  (batch 6 landed everything up to that via).
- HV_RAW crosses the corridor mouth on In2 under the APD_K via
  (41.12,-4.38) at the 0.3 internal need.
- CC2 loops south through its own pad column at neck width and
  east at y=74.3 into the target group's southern track.
- U4.12 SE diagonal through the wedge (batch 6 landed seg 1).
Usage: xvfb-run -a python3 hw/escapes7.py <src> <out>
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
MMf = pcbnew.FromMM
MMt = pcbnew.ToMM
SRC, OUT = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(SRC)
items = build_items(board)

def refresh():
    global items
    items = build_items(board)

def seg_blocked(net, x1, y1, x2, y2, w, layer):
    s = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MMf(x1), MMf(y1)),
                             pcbnew.VECTOR2I(MMf(x2), MMf(y2)),
                             MMf(w))
    for kind, n2, l2, s2, desc in items:
        if n2 == net or kind == 'zone':
            continue
        if layer not in l2:
            continue
        need = need_for(net, n2, {layer})
        if s.Collide(s2, MMf(need - 0.001)):
            return f'{n2} {desc}'
    return None

def disc_blocked(net, x, y):
    s = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MMf(x), MMf(y)),
                             pcbnew.VECTOR2I(MMf(x), MMf(y)), MMf(0.6))
    for kind, n2, l2, s2, desc in items:
        if n2 == net or kind == 'zone':
            continue
        need = need_for(net, n2, l2)
        if s.Collide(s2, MMf(need - 0.001)):
            return f'{n2} {desc}'
    return None

def add_track(net, x1, y1, x2, y2, w=0.25, layer=pcbnew.F_Cu):
    bad = seg_blocked(net, x1, y1, x2, y2, w, layer)
    assert not bad, f'{net} seg ({x1},{y1})->({x2},{y2}): {bad}'
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MMf(x1), MMf(y1)))
    t.SetEnd(pcbnew.VECTOR2I(MMf(x2), MMf(y2)))
    t.SetWidth(MMf(w))
    t.SetLayer(layer)
    t.SetNet(board.FindNet(net))
    board.Add(t)
    print(f'  {net}: ({x1:.2f},{y1:.2f})->({x2:.2f},{y2:.2f}) L{layer}')

def add_via(net, x, y):
    bad = disc_blocked(net, x, y)
    assert not bad, f'{net} via ({x},{y}): {bad}'
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(MMf(x), MMf(y)))
    v.SetWidth(MMf(0.6))
    v.SetDrill(MMf(0.3))
    v.SetNet(board.FindNet(net))
    board.Add(v)
    print(f'  {net}: via ({x:.2f},{y:.2f})')

def section(name, fn):
    print(f'--- {name} ---')
    try:
        fn()
        refresh()
        print(f'  [{name} OK]')
    except AssertionError as exc:
        refresh()
        print(f'  [{name} REFUSED: {exc}]')

# 1. +5V U14.6 at x=60.45.
def sec_u14():
    add_track('+5V', 60.5, 63.15, 60.45, 64.8, w=0.3)
    add_via('+5V', 60.45, 64.8)
    add_track('+5V', 60.45, 64.8, 57.8, 61.6, layer=pcbnew.In2_Cu)
    refresh()
    add_via('+5V', 57.8, 61.6)
    add_track('+5V', 57.8, 61.6, 57.45, 61.3, w=0.3)
section('1 +5V U14.6 x=60.45', sec_u14)

# 2. +3V3A: F east to (84.0,-17.1), via down, In2 east under
# the ULPI bank, via up, south into the target track.
def sec_33a():
    add_track('+3V3A', 82.6, -17.1, 84.0, -17.1, w=0.25)
    add_via('+3V3A', 84.0, -17.1)
    add_track('+3V3A', 84.0, -17.1, 87.9, -17.1,
              layer=pcbnew.In2_Cu)
    refresh()
    add_via('+3V3A', 87.9, -17.1)
    add_track('+3V3A', 87.9, -17.1, 87.9, -18.56, w=0.25)
section('2 +3V3A In2 under ULPI bank', sec_33a)

# 3. HV_FBX In2 v5: south to y=-5.6, west under the APD_K via,
# north at x=34.5, via up, stub into the web.
def sec_fbx():
    add_track('HV_FBX', 42.9, 0.1, 42.9, -5.6,
              layer=pcbnew.In2_Cu)
    add_track('HV_FBX', 42.9, -5.6, 34.5, -5.6,
              layer=pcbnew.In2_Cu)
    add_track('HV_FBX', 34.5, -5.6, 34.5, -4.6,
              layer=pcbnew.In2_Cu)
    refresh()
    add_via('HV_FBX', 34.5, -4.6)
    add_track('HV_FBX', 34.5, -4.6, 33.46, -5.25)
section('3 HV_FBX In2 v5', sec_fbx)

# 4. HV_INTVCC via-up hunt: batch 6 left In2 ending (14.6,-10.5)
# whose via was GND-fenced. Try candidate sites; a candidate
# wins if its disc is clear, its In2 link from (14.6,-10.5) is
# clear, and its F stub to C31.1's track end (13.62,-9.11) is
# clear. All checks dry-run before anything is placed.
def sec_intvcc():
    cands = [(14.2, -10.2), (15.0, -10.9), (14.6, -9.8),
             (13.9, -10.9), (15.2, -10.2), (14.0, -9.6)]
    for x, y in cands:
        if disc_blocked('HV_INTVCC', x, y):
            continue
        if seg_blocked('HV_INTVCC', 14.6, -10.5, x, y, 0.25,
                       pcbnew.In2_Cu):
            continue
        if seg_blocked('HV_INTVCC', x, y, 13.62, -9.11, 0.25,
                       pcbnew.F_Cu):
            continue
        print(f'  via-up site ({x},{y})')
        add_track('HV_INTVCC', 14.6, -10.5, x, y,
                  layer=pcbnew.In2_Cu)
        refresh()
        add_via('HV_INTVCC', x, y)
        add_track('HV_INTVCC', x, y, 13.62, -9.11)
        return
    raise AssertionError('no via-up site in the candidate list')
section('4 HV_INTVCC via-up hunt', sec_intvcc)

# 5. HV_RAW v5: F legs to (42.9,-4.7), via down, In2 west under
# the APD_K via at the 0.3 internal need, via up at (39.9,-5.6),
# F jog west then south into the island track (39.53,-9.8).
def sec_raw():
    add_track('HV_RAW', 43.3, -3.6, 42.9, -4.7, w=0.4)
    add_via('HV_RAW', 42.9, -4.7)
    add_track('HV_RAW', 42.9, -4.7, 39.9, -5.6, w=0.4,
              layer=pcbnew.In2_Cu)
    refresh()
    add_via('HV_RAW', 39.9, -5.6)
    add_track('HV_RAW', 39.9, -5.6, 39.3, -7.5, w=0.4)
    add_track('HV_RAW', 39.3, -7.5, 39.53, -9.8, w=0.4)
section('5 HV_RAW v5 In2 mouth crossing', sec_raw)

# 6. CC2 v4 south loop.
def sec_cc2():
    add_track('CC2', 30.5, 72.55, 30.44, 73.0, w=0.15)
    add_track('CC2', 30.44, 73.0, 30.44, 74.3, w=0.15)
    add_track('CC2', 30.44, 74.3, 33.71, 74.3)
section('6 CC2 v4 south loop', sec_cc2)

# 7. +3V3D_CDR U4.12: SE diagonal through the wedge from batch
# 6's placed seg-1 end (54.75,-15.45).
def sec_u412():
    add_track('+3V3D_CDR', 54.75, -15.45, 56.3, -14.6, w=0.2)
section('7 +3V3D_CDR U4.12 diagonal', sec_u412)

board.Save(OUT)
board = pcbnew.LoadBoard(OUT)
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(OUT)
print(f'saved {OUT}')

#!/usr/bin/env python3
"""Escape + join surgery batch 11 -- the HV pocket resolution.
Facts (probe_r50, real bboxes): the batch-9 R50 move left
R50.1's pad bbox overlapping R31.2's by 0.06mm in x -- R50
shifts +1.14mm east (net move from original: (-0.86,-0.8)),
putting R50.1's east edge 1.08 clear of R31.2. Then:
- HV_R31B re-join: R50.1 south at x=37.38, east into R49.2.
- HV_FBX: stub NE to via (41.3,-2.2), In2 west stepping south
  of the APD_K In2 staircase, via up at (33.2,-4.6), stub into
  the web track end (33.46,-5.25).
- HV_RAW: F lane west to (42.6,-1.3), via down, In2 SW under
  the corridor mouth, via up at (39.9,-5.6), F into the island
  track (39.53,-9.8).
Run AFTER the engine round, on its output board.
Usage: xvfb-run -a python3 hw/escapes11.py <src> <out>
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

def pad_pos(ref, pin):
    fp = board.FindFootprintByReference(ref)
    for p in fp.Pads():
        if p.GetNumber() == pin:
            return (MMt(p.GetPosition().x), MMt(p.GetPosition().y))
    raise AssertionError(f'{ref}.{pin} not found')

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

# 0. R50 shift +1.14 east.
def sec_shift():
    fp = board.FindFootprintByReference('R50')
    pos = fp.GetPosition()
    fp.SetPosition(pcbnew.VECTOR2I(pos.x + MMf(1.14), pos.y))
    print('  R50 shifted +1.14 east (net move (-0.86,-0.8))')
    refresh()
section('0 R50 shift east', sec_shift)

# 1. HV_R31B re-join.
def sec_r31b():
    p1 = pad_pos('R50', '1')
    r492 = pad_pos('R49', '2')
    add_track('HV_R31B', p1[0], p1[1], p1[0], -5.0)
    add_track('HV_R31B', p1[0], -5.0, r492[0], r492[1])
section('1 HV_R31B re-join', sec_r31b)

# 2. HV_FBX via route.
def sec_fbx():
    p2 = pad_pos('R50', '2')
    add_track('HV_FBX', p2[0], p2[1], 41.3, -2.2)
    add_via('HV_FBX', 41.3, -2.2)
    add_track('HV_FBX', 41.3, -2.2, 40.9, -3.9,
              layer=pcbnew.In2_Cu)
    add_track('HV_FBX', 40.9, -3.9, 36.5, -4.0,
              layer=pcbnew.In2_Cu)
    add_track('HV_FBX', 36.5, -4.0, 33.2, -4.6,
              layer=pcbnew.In2_Cu)
    refresh()
    add_via('HV_FBX', 33.2, -4.6)
    add_track('HV_FBX', 33.2, -4.6, 33.46, -5.25)
section('2 HV_FBX via route', sec_fbx)

# 3. HV_RAW lane + In2 mouth crossing.
def sec_raw():
    p = pad_pos('R29', '1')
    add_track('HV_RAW', p[0], p[1], 42.6, -1.3, w=0.4)
    add_via('HV_RAW', 42.6, -1.3)
    add_track('HV_RAW', 42.6, -1.3, 41.5, -4.2, w=0.4,
              layer=pcbnew.In2_Cu)
    add_track('HV_RAW', 41.5, -4.2, 39.9, -5.6, w=0.4,
              layer=pcbnew.In2_Cu)
    refresh()
    add_via('HV_RAW', 39.9, -5.6)
    add_track('HV_RAW', 39.9, -5.6, 39.3, -7.5, w=0.4)
    add_track('HV_RAW', 39.3, -7.5, 39.53, -9.8, w=0.4)
section('3 HV_RAW lane + In2', sec_raw)

# 4. HV_SS In2 hop (heal_big failed from both sides: 8s + 299s).
def sec_ss():
    add_track('HV_SS', 10.62, -15.0, 9.9, -15.9)
    add_via('HV_SS', 9.9, -15.9)
    add_track('HV_SS', 9.9, -15.9, 15.9, -11.6, layer=pcbnew.In2_Cu)
    refresh()
    add_via('HV_SS', 15.9, -11.6)
    add_track('HV_SS', 15.9, -11.6, 16.02, -11.01)
section('4 HV_SS In2 hop', sec_ss)

board.Save(OUT)
board = pcbnew.LoadBoard(OUT)
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(OUT)
print(f'saved {OUT}')

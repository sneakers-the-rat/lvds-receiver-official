#!/usr/bin/env python3
"""Escape + join surgery batch 10 -- batch 9's R50 move landed;
its re-joins redesigned from the named blockers:
- the orphaned HV_R31B hop is ripped (its north end sits inside
  the moved R50.2's 1.0 shadow) and R50.1 re-joins R49.2's pad
  directly from the south-west;
- R50.2 escapes north-east then west at y=0.3 (clear of R49.2's
  and R50.1's shadows) and south at x=33.4 into the FBX web;
- HV_RAW threads the via gap at y=-1.85 to x=40.92, then drops
  west of the APD_K via (41.12,-4.38) at 1.13 clearance;
- U14.6 B leg waypointed; CC2 jogged east before turning north.
Usage: xvfb-run -a python3 hw/escapes10.py <src> <out>
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

def rip_exact(net, layer, pts):
    n = 0
    for t in list(board.GetTracks()):
        if t.GetNetname() != net or t.Type() == pcbnew.PCB_VIA_T:
            continue
        if t.GetLayer() != layer:
            continue
        sx, sy = MMt(t.GetStart().x), MMt(t.GetStart().y)
        ex, ey = MMt(t.GetEnd().x), MMt(t.GetEnd().y)
        key = (round(sx, 2), round(sy, 2), round(ex, 2), round(ey, 2))
        if key in pts or (key[2], key[3], key[0], key[1]) in pts:
            board.Remove(t)
            n += 1
            print(f'  rip {net} L{layer} ({sx:.2f},{sy:.2f})'
                  f'->({ex:.2f},{ey:.2f})')
    refresh()
    return n

# 1. Rip the orphaned HV_R31B hop; re-join R50.1 -> R49.2.
def sec_r31b():
    rip_exact('HV_R31B', pcbnew.F_Cu, {(38.24, -1.6, 38.16, -5.0)})
    p1 = pad_pos('R50', '1')
    r492 = pad_pos('R49', '2')
    add_track('HV_R31B', p1[0], p1[1], 36.9, -4.6)
    add_track('HV_R31B', 36.9, -4.6, r492[0], r492[1])
section('1 HV_R31B re-join', sec_r31b)

# 2. R50.2 FBX escape v2.
def sec_fbx():
    p2 = pad_pos('R50', '2')
    add_track('HV_FBX', p2[0], p2[1], 38.75, -0.9)
    add_track('HV_FBX', 38.75, -0.9, 37.9, 0.3)
    add_track('HV_FBX', 37.9, 0.3, 33.4, 0.3)
    add_track('HV_FBX', 33.4, 0.3, 33.4, -5.0)
    add_track('HV_FBX', 33.4, -5.0, 33.46, -5.25)
section('2 HV_FBX R50.2 escape v2', sec_fbx)

# 3. HV_RAW v6 lane.
def sec_raw():
    p = pad_pos('R29', '1')
    add_track('HV_RAW', p[0], p[1], 40.92, -1.85, w=0.4)
    add_track('HV_RAW', 40.92, -1.85, 39.95, -2.6, w=0.4)
    add_track('HV_RAW', 39.95, -2.6, 39.4, -4.6, w=0.4)
    add_track('HV_RAW', 39.4, -4.6, 39.4, -7.5, w=0.4)
    add_track('HV_RAW', 39.4, -7.5, 39.53, -9.8, w=0.4)
section('3 HV_RAW v6', sec_raw)

# 4. +5V U14.6: B legs waypointed west of ILIM_A's B fanout.
def sec_u14():
    add_track('+5V', 58.8, 63.9, 58.3, 62.9, layer=pcbnew.B_Cu)
    add_track('+5V', 58.3, 62.9, 57.8, 61.6, layer=pcbnew.B_Cu)
    refresh()
    add_via('+5V', 57.8, 61.6)
    add_track('+5V', 57.8, 61.6, 57.45, 61.3, w=0.3)
section('4 +5V U14.6 B waypoint', sec_u14)

# 5. CC2 v2 + VBUS re-feed.
def sec_cc2():
    add_track('CC2', 30.5, 72.55, 30.75, 72.3)
    add_track('CC2', 30.75, 72.3, 31.9, 72.3)
    add_track('CC2', 31.9, 72.3, 32.81, 72.3)
    add_track('CC2', 32.81, 72.3, 32.81, 72.42)
    add_track('VBUS_RAW', 31.10, 71.83, 31.35, 71.35, w=0.3)
section('5 CC2 v2', sec_cc2)

board.Save(OUT)
board = pcbnew.LoadBoard(OUT)
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(OUT)
print(f'saved {OUT}')

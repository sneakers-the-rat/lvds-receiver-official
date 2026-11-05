#!/usr/bin/env python3
"""Escape + join surgery batch 12 -- PLACEMENT break of the HV
pocket seesaw. Diagnosis (audits 90-93 + probe_r50 real bboxes):
the string pocket (R49/R50/R29/R34 + APD_K vias + CMP_QN B
staircase) is over-dense at the 1.0mm class -- every escape
fences another net, so heal/thread trade nets 27->29->28 while
violations creep. Fix attempted here: move R49+R50 SW as a unit
by (-6,-5.5) into the open field south of the FBX web (landing
verified vs real bboxes: 1.52 clear of D5.1, ~1.5 clear of the
HV_RAW web; one GND stitch vertical ripped, GND re-stitches).
That frees R50.2's FBX escape (direct 3mm hop to the web),
frees HV_RAW's via site (39.9,-5.6) (R49.2's tall pad was its
fence), and removes the R50.1/R31.2 pad graze.
Also: HV_SS/HV_FBX are LV class (0.2) per check_pcb.need_for --
their U10 seal was my misread: FBX's dive via re-sites 0.5mm SW
and HV_SS threads the freed slot north to fan2's clear via site
(10.9,-12.8), then In2 to C30.1.
Board-agnostic: Usage: xvfb-run -a python3 hw/escapes12.py <src> <out>
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

def rip_seg(net, x1, y1, x2, y2):
    for t in list(board.GetTracks()):
        if t.Type() == pcbnew.PCB_VIA_T or t.GetNetname() != net:
            continue
        a = (MMt(t.GetStart().x), MMt(t.GetStart().y))
        b = (MMt(t.GetEnd().x), MMt(t.GetEnd().y))
        for (p, q) in ((a, b), (b, a)):
            if (abs(p[0] - x1) < 0.6 and abs(p[1] - y1) < 0.6
                    and abs(q[0] - x2) < 0.6 and abs(q[1] - y2) < 0.6):
                board.Remove(t)
                print(f'  rip {net} ({a[0]:.2f},{a[1]:.2f})->'
                      f'({b[0]:.2f},{b[1]:.2f})')
                return
    print(f'  rip {net} ({x1},{y1})->({x2},{y2}): NOT FOUND')

def rip_via(net, x, y):
    for t in list(board.GetTracks()):
        if t.Type() != pcbnew.PCB_VIA_T or t.GetNetname() != net:
            continue
        if (abs(MMt(t.GetPosition().x) - x) < 0.3
                and abs(MMt(t.GetPosition().y) - y) < 0.3):
            board.Remove(t)
            print(f'  rip via {net} @({x},{y})')
            return
    print(f'  rip via {net} @({x},{y}): NOT FOUND')

def rip_touching(x, y, r=0.6):
    for t in list(board.GetTracks()):
        if t.Type() == pcbnew.PCB_VIA_T:
            continue
        for e in (t.GetStart(), t.GetEnd()):
            if (abs(MMt(e.x) - x) < r and abs(MMt(e.y) - y) < r):
                print(f'  rip touching {t.GetNetname()} '
                      f'({MMt(t.GetStart().x):.2f},'
                      f'{MMt(t.GetStart().y):.2f})->'
                      f'({MMt(t.GetEnd().x):.2f},'
                      f'{MMt(t.GetEnd().y):.2f})')
                board.Remove(t)
                break

def move(ref, dx, dy):
    fp = board.FindFootprintByReference(ref)
    pos = fp.GetPosition()
    fp.SetPosition(pcbnew.VECTOR2I(pos.x + MMf(dx), pos.y + MMf(dy)))
    print(f'  {ref} moved ({dx},{dy})')

def section(name, fn):
    print(f'--- {name} ---')
    try:
        fn()
        refresh()
        print(f'  [{name} OK]')
    except AssertionError as exc:
        refresh()
        print(f'  [{name} REFUSED: {exc}]')

# 0. Rips: GND stitch vertical in the landing field; dead
# batch-11 copper; FBX dive via at U10; tracks touching the
# string pads' current positions (they orphan on the move).
def sec_rips():
    rip_seg('GND', 30.38, -4.88, 30.38, -12.62)
    rip_seg('HV_RAW', 43.675, -1.8, 42.6, -1.3)
    rip_seg('HV_RAW', 43.675, -1.8, 42.90, -2.6)
    rip_seg('HV_FBX', 40.30, -2.4, 41.3, -2.2)
    rip_via('HV_FBX', 10.12, -15.38)
    for (rx, ry) in ((35.24, -5.0), (38.16, -5.0),
                     (37.38, -2.4), (40.30, -2.4)):
        rip_touching(rx, ry)
section('0 rips', sec_rips)

# 1. The placement move: R49 + R50 SW as a unit.
def sec_move():
    move('R49', -6.0, -5.5)
    move('R50', -6.0, -5.5)
section('1 R49+R50 move SW', sec_move)

# 2. HV_R31B re-join between the moved pads.
def sec_r31b():
    p1 = pad_pos('R50', '1')
    p2 = pad_pos('R49', '2')
    add_track('HV_R31B', p1[0], p1[1], 31.7, -9.2)
    add_track('HV_R31B', 31.7, -9.2, p2[0], p2[1])
section('2 HV_R31B re-join', sec_r31b)

# 3. HV_FBX: R50.2 direct hop west into the web track end.
def sec_fbx():
    p2 = pad_pos('R50', '2')
    add_track('HV_FBX', p2[0], p2[1], 33.9, -6.2)
    add_track('HV_FBX', 33.9, -6.2, 33.46, -5.25)
section('3 HV_FBX hop to web', sec_fbx)

# 4. HV_RAW: fan stub -> via (44.35,-4.85) -> In2 west -> via
# up (39.9,-5.6) -> island track.
def sec_raw():
    add_track('HV_RAW', 43.45, -3.9, 44.35, -4.85, w=0.4)
    add_via('HV_RAW', 44.35, -4.85)
    add_track('HV_RAW', 44.35, -4.85, 41.5, -5.6, w=0.4,
              layer=pcbnew.In2_Cu)
    add_track('HV_RAW', 41.5, -5.6, 39.9, -5.6, w=0.4,
              layer=pcbnew.In2_Cu)
    refresh()
    add_via('HV_RAW', 39.9, -5.6)
    add_track('HV_RAW', 39.9, -5.6, 39.3, -7.5, w=0.4)
    add_track('HV_RAW', 39.3, -7.5, 39.53, -9.8, w=0.4)
section('4 HV_RAW via + In2', sec_raw)

# 5. HV_FBX re-dive at U10 (via re-sited SW, In2 run kept).
def sec_fbx_dive():
    add_track('HV_FBX', 10.12, -15.38, 9.62, -15.75, w=0.2)
    add_via('HV_FBX', 9.62, -15.75)
    add_track('HV_FBX', 9.62, -15.75, 10.38, -15.38, w=0.2,
              layer=pcbnew.In2_Cu)
section('5 HV_FBX re-dive', sec_fbx_dive)

# 6. HV_SS: west leg, north run through the freed slot, via at
# fan2's clear site (10.9,-12.8), In2 east, via up into the
# C30.1 group track.
def sec_ss():
    add_track('HV_SS', 10.62, -15.0, 9.9, -15.0)
    add_track('HV_SS', 9.9, -15.0, 9.9, -13.6)
    add_track('HV_SS', 9.9, -13.6, 10.9, -12.8)
    add_via('HV_SS', 10.9, -12.8)
    add_track('HV_SS', 10.9, -12.8, 15.9, -11.6,
              layer=pcbnew.In2_Cu)
    refresh()
    add_via('HV_SS', 15.9, -11.6)
    add_track('HV_SS', 15.9, -11.6, 16.02, -11.01)
section('6 HV_SS north dive', sec_ss)

board.Save(OUT)
board = pcbnew.LoadBoard(OUT)
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(OUT)
print(f'saved {OUT}')

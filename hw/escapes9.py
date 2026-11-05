#!/usr/bin/env python3
"""Escape + join surgery batch 9 -- the R50 PLACEMENT MOVE.
R50.2's pad (41.16,-1.6) sits in the only gap between the two
APD_K via shadows (41.12,0.62)/(41.12,-4.38) on HV_RAW's west
lane, and CMP_QN's B staircase + R29.2 fence every via site.
R50 moves (-2.0,-0.8): its R50.1 pad is re-joined to the
HV_R31B hop, R50.2 escapes SW on F to the FBX web, the orphaned
FBX stub/via at (42.9,0.1) is ripped, and HV_RAW runs the
opened lane west then SW into its island track.
Also: U14.6 crosses SET_A's In2 wall on B.Cu; CC2 rips the
VBUS picket at x=31.1 and runs north, VBUS re-fed to A9's track.
Usage: xvfb-run -a python3 hw/escapes9.py <src> <out>
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
        if t.GetNetname() != net:
            continue
        if t.Type() == pcbnew.PCB_VIA_T:
            if layer is None:
                px, py = MMt(t.GetPosition().x), MMt(t.GetPosition().y)
                if (round(px, 2), round(py, 2)) in pts:
                    board.Remove(t)
                    n += 1
                    print(f'  rip {net} via @({px:.2f},{py:.2f})')
            continue
        if layer is not None and t.GetLayer() != layer:
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

# 1. Rip the orphaned FBX stub + via + In2 stub (batch 3/7
# remnants anchored on R50.2's old pad / the west web).
def sec_rip():
    rip_exact('HV_FBX', pcbnew.F_Cu, {(41.16, -1.6, 42.9, 0.1)})
    rip_exact('HV_FBX', None, {(42.9, 0.1)})
    rip_exact('HV_FBX', pcbnew.In2_Cu, {(34.5, -5.6, 34.5, -4.6)})
section('1 rip FBX orphans', sec_rip)

# 2. Move R50 (-2.0,-0.8) and re-join R50.1 to the HV_R31B hop
# track end (38.237,-1.6).
def sec_move():
    fp = board.FindFootprintByReference('R50')
    pos = fp.GetPosition()
    fp.SetPosition(pcbnew.VECTOR2I(pos.x - MMf(2.0),
                                   pos.y - MMf(0.8)))
    print('  R50 moved (-2.0,-0.8)')
    refresh()
    p1 = pad_pos('R50', '1')
    add_track('HV_R31B', 38.237, -1.6, 37.0, -2.2)
    add_track('HV_R31B', 37.0, -2.2, p1[0], p1[1])
section('2 R50 move + R31B re-join', sec_move)

# 3. R50.2 (moved) FBX escape: SW around R49.1's south, into
# the FBX web track end (33.46,-5.25).
def sec_fbx():
    p2 = pad_pos('R50', '2')
    add_track('HV_FBX', p2[0], p2[1], 37.8, -3.9)
    add_track('HV_FBX', 37.8, -3.9, 36.8, -6.6)
    add_track('HV_FBX', 36.8, -6.6, 34.8, -6.9)
    add_track('HV_FBX', 34.8, -6.9, 33.46, -5.25)
section('3 HV_FBX R50.2 escape', sec_fbx)

# 4. HV_RAW west lane through the opened via gap, SW into the
# island track end (39.53,-9.8).
def sec_raw():
    p = pad_pos('R29', '1')
    add_track('HV_RAW', p[0], p[1], 40.0, -1.85, w=0.4)
    add_track('HV_RAW', 40.0, -1.85, 39.53, -9.8, w=0.4)
section('4 HV_RAW west lane', sec_raw)

# 5. +5V U14.6: batch 7 left F via at (60.45,64.8). In2 leg
# south of SET_A's wall, via down to B before the wall, B leg
# north, via up at the target (57.8,61.6).
def sec_u14():
    add_track('+5V', 60.45, 64.8, 58.8, 63.9,
              layer=pcbnew.In2_Cu)
    add_via('+5V', 58.8, 63.9)
    add_track('+5V', 58.8, 63.9, 57.8, 61.6,
              layer=pcbnew.B_Cu)
    refresh()
    add_via('+5V', 57.8, 61.6)
    add_track('+5V', 57.8, 61.6, 57.45, 61.3, w=0.3)
section('5 +5V U14.6 B crossing', sec_u14)

# 6. CC2: rip the VBUS picket, run north + east + SE into the
# target track end; re-feed VBUS B4's north stub to A9's track.
def sec_cc2():
    rip_exact('VBUS_RAW', pcbnew.F_Cu, {(31.15, 72.83, 31.10, 71.83)})
    add_track('CC2', 30.5, 72.55, 30.5, 71.9)
    add_track('CC2', 30.5, 71.9, 31.9, 71.9)
    add_track('CC2', 31.9, 71.9, 32.81, 72.42)
    add_track('VBUS_RAW', 31.10, 71.83, 31.35, 71.35, w=0.3)
section('6 CC2 north route', sec_cc2)

board.Save(OUT)
board = pcbnew.LoadBoard(OUT)
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(OUT)
print(f'saved {OUT}')

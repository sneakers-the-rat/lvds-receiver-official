#!/usr/bin/env python3
"""Escape + join surgery batch 6 -- every route redesigned from
batch 5's coordinate-exact blockers:
- U14.6 stub jogged west to x=60.3 (ILIM_A track end was 0.195
  from the x=60.55 line at the 0.25 class).
- +3V3A hops ULPI_CK's northbound F track on In2.
- HV_FBX In2 goes south first at x=42.9, then west (the APD_K
  via (41.125,0.625) r=0.4 shadows every diagonal at need 1.0).
- HV_INTVCC turns through the [15.114,15.151] window between
  U10.11's EP and U10.7's pad at neck width 0.15.
- HV_RAW: the APD_K dead-end strand hanging into the corridor
  is ripped, then the legs land.
- CC2 drops to y=72.25 before turning east.
- U4.12 exits its row at w=0.20 (the 0.5-pitch row admits no
  more at the 0.25 class), east under the REFCLKN diagonal.
Usage: xvfb-run -a python3 hw/escapes6.py <src> <out>
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

def rip(net, layer, xlo, xhi, ylo, yhi):
    n = 0
    for t in list(board.GetTracks()):
        if t.GetNetname() != net or t.Type() == pcbnew.PCB_VIA_T:
            continue
        if t.GetLayer() != layer:
            continue
        sx, sy = MMt(t.GetStart().x), MMt(t.GetStart().y)
        ex, ey = MMt(t.GetEnd().x), MMt(t.GetEnd().y)
        if (min(sx, ex) <= xhi and max(sx, ex) >= xlo
                and min(sy, ey) <= yhi and max(sy, ey) >= ylo):
            print(f'  rip {net} L{layer} ({sx:.2f},{sy:.2f})'
                  f'->({ex:.2f},{ey:.2f})')
            board.Remove(t)
            n += 1
    print(f'  ripped {n} {net} segments')
    refresh()
    return n

# 1. +5V U14.6: stub at x=60.3 (from the pad's south edge),
# via, In2 NW, via up, stub into U14.1's fanout.
def sec_u14():
    add_track('+5V', 60.35, 63.15, 60.3, 64.8, w=0.3)
    add_via('+5V', 60.3, 64.8)
    add_track('+5V', 60.3, 64.8, 57.8, 61.6, layer=pcbnew.In2_Cu)
    refresh()
    add_via('+5V', 57.8, 61.6)
    add_track('+5V', 57.8, 61.6, 57.45, 61.3, w=0.3)
section('1 +5V U14.6 x=60.3', sec_u14)

# 2. +3V3A: east at y=-17.1 to x=85.9, via down, In2 east under
# ULPI_CK's F track, via up at (87.9,-17.1), south into target.
def sec_33a():
    add_track('+3V3A', 82.6, -17.1, 85.9, -17.1, w=0.25)
    add_via('+3V3A', 85.9, -17.1)
    add_track('+3V3A', 85.9, -17.1, 87.9, -17.1,
              layer=pcbnew.In2_Cu)
    refresh()
    add_via('+3V3A', 87.9, -17.1)
    add_track('+3V3A', 87.9, -17.1, 87.9, -18.56, w=0.25)
section('2 +3V3A In2 hop over ULPI_CK', sec_33a)

# 3. HV_FBX In2 v4: south at x=42.9 first, then west.
def sec_fbx():
    add_track('HV_FBX', 42.9, 0.1, 42.9, -3.5,
              layer=pcbnew.In2_Cu)
    add_track('HV_FBX', 42.9, -3.5, 34.5, -4.6,
              layer=pcbnew.In2_Cu)
    refresh()
    add_via('HV_FBX', 34.5, -4.6)
    add_track('HV_FBX', 34.5, -4.6, 33.46, -5.25)
section('3 HV_FBX In2 v4', sec_fbx)

# 4. HV_INTVCC: neck-width turn through the EP/GATE window.
def sec_intvcc():
    add_track('HV_INTVCC', 16.15, -15.0, 15.13, -15.0, w=0.15)
    add_track('HV_INTVCC', 15.13, -15.0, 15.13, -13.3, w=0.15)
    add_via('HV_INTVCC', 15.13, -13.3)
    add_track('HV_INTVCC', 15.13, -13.3, 14.6, -13.3,
              layer=pcbnew.In2_Cu)
    add_track('HV_INTVCC', 14.6, -13.3, 14.6, -10.5,
              layer=pcbnew.In2_Cu)
    refresh()
    add_via('HV_INTVCC', 14.6, -10.5)
    add_track('HV_INTVCC', 14.6, -10.5, 13.62, -9.11)
section('4 HV_INTVCC neck turn', sec_intvcc)

# 5. HV_RAW: rip the APD_K dead-end strand in the corridor,
# then legs 2-4 from batch 4's placed leg 1.
def sec_raw():
    rip('APD_K', pcbnew.F_Cu, 41.2, 41.8, -5.8, -4.4)
    add_track('HV_RAW', 43.3, -3.6, 42.5, -4.5, w=0.4)
    add_track('HV_RAW', 42.5, -4.5, 40.2, -5.2, w=0.4)
    add_track('HV_RAW', 40.2, -5.2, 39.53, -9.8, w=0.4)
section('5 HV_RAW strand rip + legs', sec_raw)

# 6. CC2 v3: drop to y=72.25 east of B4's shadow, east, north.
def sec_cc2():
    add_track('CC2', 30.5, 72.55, 30.75, 72.25)
    add_track('CC2', 30.75, 72.25, 32.81, 72.25)
    add_track('CC2', 32.81, 72.25, 32.81, 72.42)
section('6 CC2 v3', sec_cc2)

# 7. +3V3D_CDR U4.12: south at w=0.20, east under the REFCLKN
# diagonal, SE into open field (stub for heal).
def sec_u412():
    add_track('+3V3D_CDR', 54.75, -16.06, 54.75, -15.45, w=0.2)
    add_track('+3V3D_CDR', 54.75, -15.45, 56.5, -15.45, w=0.2)
    add_track('+3V3D_CDR', 56.5, -15.45, 57.5, -13.5, w=0.25)
section('7 +3V3D_CDR U4.12 w=0.20 route', sec_u412)

board.Save(OUT)
board = pcbnew.LoadBoard(OUT)
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(OUT)
print(f'saved {OUT}')

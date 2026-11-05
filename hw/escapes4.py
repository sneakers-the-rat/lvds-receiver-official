#!/usr/bin/env python3
"""Escape + join surgery batch 4. Headline: the PLACEMENT move
the residue demanded -- R34 moves 1.5mm north, opening the
HV_RAW corridor between R50.2's and R34.1's 1.0mm shadows (they
overlapped by 0.06mm; no via or track at the HV class fit
between them). R34's two connected nets are re-joined in the
same section. Plus batch-3 retries with the exact blockers
designed around. Non-fatal per section.
Usage: xvfb-run -a python3 hw/escapes4.py <src> <out>
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

# 1. SET_P: north run at x=50.9 (west of the +5V fanout diagonal
# at (51.38,62.62)->(51.62,62.38) that refused batch 3).
def sec_setp():
    p = pad_pos('U13', '7')
    add_track('SET_P', p[0], p[1], 50.9, p[1], w=0.2)
    add_track('SET_P', 50.9, p[1], 50.9, 64.55)
    add_track('SET_P', 50.9, 64.55, 42.73, 64.55)
    add_track('SET_P', 42.73, 64.55, 42.73, 64.47)
section('1 SET_P x=50.9', sec_setp)

# 2. +5V U14.6 south route: rip the GND staircase tail hugging
# the pad's south-east, stub south, via at the fan-clear site,
# In2 NW, via up beside U14.1, stub into its fanout.
def sec_u14():
    rip('GND', pcbnew.F_Cu, 59.9, 60.8, 63.4, 64.1)
    p = pad_pos('U14', '6')
    add_track('+5V', p[0], 63.15, p[0], 64.8, w=0.3)
    add_via('+5V', p[0], 64.8)
    add_track('+5V', p[0], 64.8, 57.8, 61.6, layer=pcbnew.In2_Cu)
    refresh()
    add_via('+5V', 57.8, 61.6)
    add_track('+5V', 57.8, 61.6, 57.45, 61.3, w=0.3)
section('2 +5V U14.6 south', sec_u14)

# 3. +3V3A east run: rip U7.10's GND fanout where it crosses
# y=-17.6, then finish batch 3a's route into the +3V3A track.
def sec_33a():
    rip('GND', pcbnew.F_Cu, 84.3, 85.3, -18.4, -16.8)
    add_track('+3V3A', 82.6, -17.6, 87.9, -17.6, w=0.25)
    add_track('+3V3A', 87.9, -17.6, 87.9, -18.56, w=0.25)
section('3 +3V3A east run', sec_33a)

# 4. +3V3D_CDR U4.12: diagonal stub SE, passing south of the
# REFCLKN fanout tracks that refused the straight south run.
def sec_u412():
    add_track('+3V3D_CDR', 54.75, -16.06, 56.3, -14.2, w=0.3)
section('4 +3V3D_CDR U4.12 diag stub', sec_u412)

# 5. HV_FBX: batch 3 left the F run + via at (42.9,0.1). In2
# with a waypoint bending SW earlier than the refused straight
# line, via up at the web, stub in.
def sec_fbx():
    add_track('HV_FBX', 42.9, 0.1, 38.0, -2.2,
              layer=pcbnew.In2_Cu)
    add_track('HV_FBX', 38.0, -2.2, 34.5, -4.6,
              layer=pcbnew.In2_Cu)
    refresh()
    add_via('HV_FBX', 34.5, -4.6)
    add_track('HV_FBX', 34.5, -4.6, 33.46, -5.25)
section('5 HV_FBX In2 waypoint', sec_fbx)

# 6. HV_INTVCC U10.8: via on the pad's west end (15.55,-15.0),
# In2 west then north (the FBX L2 staircase's first step sits at
# x>=15.62 -- the In2 must leave westward first), via up, stub
# into C31.1's group track end.
def sec_intvcc():
    add_track('HV_INTVCC', 16.15, -15.0, 15.55, -15.0)
    add_via('HV_INTVCC', 15.55, -15.0)
    add_track('HV_INTVCC', 15.55, -15.0, 14.6, -15.0,
              layer=pcbnew.In2_Cu)
    add_track('HV_INTVCC', 14.6, -15.0, 14.6, -10.5,
              layer=pcbnew.In2_Cu)
    refresh()
    add_via('HV_INTVCC', 14.6, -10.5)
    add_track('HV_INTVCC', 14.6, -10.5, 13.62, -9.11)
section('6 HV_INTVCC via-in-pad', sec_intvcc)

# 7. HV_SS: extend the batch-2 west stub to x=10.1 (west of the
# HV_RT fanout's west end (10.62,-14.38) with 0.295 to spare),
# south, via, In2 east, via up, stub into C30.1's group.
def sec_ss():
    add_track('HV_SS', 10.7, -15.0, 10.1, -15.0)
    add_track('HV_SS', 10.1, -15.0, 10.1, -13.1)
    add_via('HV_SS', 10.1, -13.1)
    add_track('HV_SS', 10.1, -13.1, 15.4, -13.1,
              layer=pcbnew.In2_Cu)
    add_track('HV_SS', 15.4, -13.1, 15.4, -11.0,
              layer=pcbnew.In2_Cu)
    refresh()
    add_via('HV_SS', 15.4, -11.0)
    add_track('HV_SS', 15.4, -11.0, 16.02, -11.01)
section('7 HV_SS x=10.1', sec_ss)

# 8. THE MOVE: R34 north 1.5mm. Re-join APD_K (section-I track
# end to the moved pad) and TP_HV (stub end to the moved pad),
# join the R34 group to APD_K main (north run at x=41.5), then
# HV_RAW through the opened corridor.
def sec_move():
    fp = board.FindFootprintByReference('R34')
    pos = fp.GetPosition()
    fp.SetPosition(pcbnew.VECTOR2I(pos.x, pos.y - MMf(1.5)))
    print('  R34 moved (0,-1.5)')
    refresh()
    r341 = pad_pos('R34', '1')
    add_track('APD_K', 41.538, -6.0, r341[0], r341[1], w=0.4)
    r342 = pad_pos('R34', '2')
    add_track('TP_HV', 44.462, -6.0, r342[0], r342[1], w=0.4)
    add_track('APD_K', r341[0], r341[1], 41.5, -0.5, w=0.4)
    add_track('APD_K', 41.5, -0.5, 41.38, 0.38, w=0.4)
section('8a R34 move + rejoins', sec_move)

def sec_raw():
    p = pad_pos('R29', '1')
    add_track('HV_RAW', p[0], p[1], 43.3, -3.6, w=0.4)
    add_track('HV_RAW', 43.3, -3.6, 42.5, -4.5, w=0.4)
    add_track('HV_RAW', 42.5, -4.5, 40.2, -5.2, w=0.4)
    add_track('HV_RAW', 40.2, -5.2, 39.53, -9.8, w=0.4)
section('8b HV_RAW corridor', sec_raw)

# 9. CC2: from the existing stub end (30.50,72.55), SE diagonal
# under the B-row pads (0.255 clear of B4 at the 0.25 class),
# east into the group track end (32.81,72.42).
def sec_cc2():
    add_track('CC2', 30.5, 72.55, 31.3, 72.35)
    add_track('CC2', 31.3, 72.35, 32.81, 72.35)
    add_track('CC2', 32.81, 72.35, 32.81, 72.42)
section('9 CC2 diagonal', sec_cc2)

board.Save(OUT)
board = pcbnew.LoadBoard(OUT)
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(OUT)
print(f'saved {OUT}')

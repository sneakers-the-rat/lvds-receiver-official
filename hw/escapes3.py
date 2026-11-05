#!/usr/bin/env python3
"""Escape + join surgery batch 3, geometry from fan2 measurements
and the probed clearance classes (rails are 0.25 class, not 0.20
-- the 0.05 error refused several batch-2 segments by 0.024).

Sections: SET_P east exit at w=0.20 (the pad-corner shadow math);
U14.6 east run at w=0.20; the GND stitch fence west of U7 ripped
(one vertical stitch track fences U7.4/U7.6/U7.7) then all three
escape west; GND segment north of U4 ripped for U4.12; R50.2 SE
run (fan: 3.5mm free at 45deg) + via + In2 to the FBX web; U10.8
via at the end of its west ray; HV_SS south via from the batch-2
stub; HV_RAW via moved west of the CMP_QN F track; CC2 south
exit at w=0.15. Non-fatal per section; blockers explained with
coordinates scanned from the board objects.
Usage: xvfb-run -a python3 hw/escapes3.py <src> <out>
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

def explain(n2, x, y):
    """Coords of board objects of net n2 near (x, y)."""
    out = []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname() != n2:
                continue
            px, py = MMt(p.GetPosition().x), MMt(p.GetPosition().y)
            if abs(px - x) < 3.5 and abs(py - y) < 3.5:
                out.append(f'pad {fp.GetReference()}.{p.GetNumber()} '
                           f'@({px:.2f},{py:.2f})')
    for t in board.GetTracks():
        if t.GetNetname() != n2:
            continue
        if t.Type() == pcbnew.PCB_VIA_T:
            px, py = MMt(t.GetPosition().x), MMt(t.GetPosition().y)
            if abs(px - x) < 3.5 and abs(py - y) < 3.5:
                out.append(f'via @({px:.2f},{py:.2f})')
        else:
            sx, sy = MMt(t.GetStart().x), MMt(t.GetStart().y)
            ex, ey = MMt(t.GetEnd().x), MMt(t.GetEnd().y)
            mx, my = (sx + ex) / 2, (sy + ey) / 2
            if abs(mx - x) < 3.5 and abs(my - y) < 3.5:
                out.append(f'trk L{t.GetLayer()} ({sx:.2f},{sy:.2f})'
                           f'->({ex:.2f},{ey:.2f})')
    return '; '.join(out[:4])

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
            return f'{n2} {desc} [{explain(n2, (x1 + x2) / 2, (y1 + y2) / 2)}]'
    return None

def disc_blocked(net, x, y):
    s = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MMf(x), MMf(y)),
                             pcbnew.VECTOR2I(MMf(x), MMf(y)), MMf(0.6))
    for kind, n2, l2, s2, desc in items:
        if n2 == net or kind == 'zone':
            continue
        need = need_for(net, n2, l2)
        if s.Collide(s2, MMf(need - 0.001)):
            return f'{n2} {desc} [{explain(n2, x, y)}]'
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
        # rip if the segment's bbox intersects the box at all
        if (min(sx, ex) <= xhi and max(sx, ex) >= xlo
                and min(sy, ey) <= yhi and max(sy, ey) >= ylo):
            print(f'  rip {net} L{layer} ({sx:.2f},{sy:.2f})'
                  f'->({ex:.2f},{ey:.2f})')
            board.Remove(t)
            n += 1
    print(f'  ripped {n} {net} segments')
    refresh()
    return n

# 1. SET_P: east exit at w=0.20 (corner shadow clears at 0.25
# surface distance = need), north at x=51.3, west at y=64.55,
# up into the group track end (42.73,64.47).
def sec_setp():
    p = pad_pos('U13', '7')
    add_track('SET_P', p[0], p[1], 51.3, p[1], w=0.2)
    add_track('SET_P', 51.3, p[1], 51.3, 64.55)
    add_track('SET_P', 51.3, 64.55, 42.73, 64.55)
    add_track('SET_P', 42.73, 64.55, 42.73, 64.47)
section('1 SET_P east exit', sec_setp)

# 2. +5V U14.6: east at w=0.20 (SET_A shadow clears at exactly
# the 0.25 need), then B2's route at w=0.30.
def sec_u14():
    p = pad_pos('U14', '6')
    add_track('+5V', p[0], p[1], 61.6, p[1], w=0.2)
    add_track('+5V', 61.6, p[1], 61.6, 65.9, w=0.3)
    add_track('+5V', 61.6, 65.9, 57.45, 65.9, w=0.3)
    add_track('+5V', 57.45, 65.9, 57.45, 61.85, w=0.3)
section('2 +5V U14.6', sec_u14)

# 3. U7 west fence: rip the GND stitch track(s) hugging the
# package's west side, then escape U7.6 (join north-east to the
# +3V3A track), U7.4 and U7.7 (stubs west for heal/thread).
def sec_u7rip():
    rip('GND', pcbnew.F_Cu, 82.3, 83.15, -22.7, -18.5)
section('3 rip GND fence west of U7', sec_u7rip)

def sec_u76():
    add_track('+3V3A', 83.12, -20.25, 82.6, -20.25, w=0.25)
    add_track('+3V3A', 82.6, -20.25, 82.6, -17.6, w=0.25)
    add_track('+3V3A', 82.6, -17.6, 87.9, -17.6, w=0.25)
    add_track('+3V3A', 87.9, -17.6, 87.9, -18.56, w=0.25)
section('3a +3V3A U7.6', sec_u76)

def sec_u74():
    add_track('+5V', 83.12, -21.25, 80.6, -21.25, w=0.3)
section('3b +5V U7.4 stub', sec_u74)

def sec_u77():
    add_track('DP_PHY', 83.12, -19.75, 81.0, -19.75)
section('3c DP_PHY U7.7 stub', sec_u77)

# 4. U4.12: rip the GND track hugging U4's north edge across
# x=54.75, then the north stub into the fan-clear zone.
def sec_u412():
    rip('GND', pcbnew.F_Cu, 54.1, 55.4, -17.4, -16.2)
    add_track('+3V3D_CDR', 54.75, -16.5, 54.75, -13.2, w=0.3)
section('4 +3V3D_CDR U4.12', sec_u412)

# 5. HV_FBX R50.2: SE run along the fan's free 45deg ray, via at
# the fan-clear site (42.9,0.1), In2 SW, via up at the web.
def sec_fbx():
    p = pad_pos('R50', '2')
    add_track('HV_FBX', p[0], p[1], 42.9, 0.1)
    add_via('HV_FBX', 42.9, 0.1)
    add_track('HV_FBX', 42.9, 0.1, 34.5, -4.6,
              layer=pcbnew.In2_Cu)
    refresh()
    add_via('HV_FBX', 34.5, -4.6)
    add_track('HV_FBX', 34.5, -4.6, 33.46, -5.25)
section('5 HV_FBX R50.2 SE route', sec_fbx)

# 6. HV_INTVCC U10.8: stub west to the fan ray end, via at
# (15.05,-15.0), In2 north + west, via up, stub to C31.1 group.
def sec_intvcc():
    add_track('HV_INTVCC', 16.15, -15.0, 15.05, -15.0)
    add_via('HV_INTVCC', 15.05, -15.0)
    add_track('HV_INTVCC', 15.05, -15.0, 15.05, -10.5,
              layer=pcbnew.In2_Cu)
    add_track('HV_INTVCC', 15.05, -10.5, 14.2, -10.5,
              layer=pcbnew.In2_Cu)
    refresh()
    add_via('HV_INTVCC', 14.2, -10.5)
    add_track('HV_INTVCC', 14.2, -10.5, 13.62, -9.11)
section('6 HV_INTVCC U10.8', sec_intvcc)

# 7. HV_SS: batch 2 left a west stub ending (10.7,-15.0). South
# from its end, via at (10.7,-12.6) (fan-clear arc), In2 east,
# via up at (15.4,-11.0), stub into C30.1's group track.
def sec_ss():
    add_track('HV_SS', 10.7, -15.0, 10.7, -12.6)
    add_via('HV_SS', 10.7, -12.6)
    add_track('HV_SS', 10.7, -12.6, 15.4, -12.6,
              layer=pcbnew.In2_Cu)
    add_track('HV_SS', 15.4, -12.6, 15.4, -11.0,
              layer=pcbnew.In2_Cu)
    refresh()
    add_via('HV_SS', 15.4, -11.0)
    add_track('HV_SS', 15.4, -11.0, 16.02, -11.01)
section('7 HV_SS U10.3', sec_ss)

# 8. HV_RAW: batch 2 left a stub to (43.45,-2.0); the via there
# is fenced by a CMP_QN F track NE. New via west at (42.9,-2.6),
# stub from R29.1's pad, In2 SW, via up, stub to the island.
def sec_raw():
    p = pad_pos('R29', '1')
    add_track('HV_RAW', p[0], p[1], 42.9, -2.6)
    add_via('HV_RAW', 42.9, -2.6)
    add_track('HV_RAW', 42.9, -2.6, 40.5, -8.8,
              layer=pcbnew.In2_Cu)
    refresh()
    add_via('HV_RAW', 40.5, -8.8)
    add_track('HV_RAW', 40.5, -8.8, 39.53, -9.8)
section('8 HV_RAW R29.1 via west', sec_raw)

# 9. CC2: south exit at w=0.15 (B4/B6 shadows clear at 0.275),
# then east at y=72.42 into the R19.1 group track end.
def sec_cc2():
    add_track('CC2', 30.5, 73.18, 30.5, 72.42, w=0.15)
    add_track('CC2', 30.5, 72.42, 32.81, 72.42)
section('9 CC2 J1.B5', sec_cc2)

board.Save(OUT)
board = pcbnew.LoadBoard(OUT)
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(OUT)
print(f'saved {OUT}')

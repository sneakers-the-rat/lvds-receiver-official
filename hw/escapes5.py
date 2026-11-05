#!/usr/bin/env python3
"""Escape + join surgery batch 5: machine-measured retries.
New machinery: explain2 (blocker = nearest board objects of that
net to the SEGMENT, with layer/coords/width), via_scan (grid
search for a clear via site + a straight F stub to it).
Usage: xvfb-run -a python3 hw/escapes5.py <src> <out>
"""
import math
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

def pad_bbox(ref, pin):
    fp = board.FindFootprintByReference(ref)
    for p in fp.Pads():
        if p.GetNumber() == pin:
            bb = p.GetBoundingBox()
            return (MMt(bb.GetX()), MMt(bb.GetY()),
                    MMt(bb.GetRight()), MMt(bb.GetBottom()))
    raise AssertionError(f'{ref}.{pin} not found')

def objects_near(net, x1, y1, x2, y2, slack=1.6):
    out = []
    lo_x, hi_x = min(x1, x2) - slack, max(x1, x2) + slack
    lo_y, hi_y = min(y1, y2) - slack, max(y1, y2) + slack
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname() != net:
                continue
            px, py = MMt(p.GetPosition().x), MMt(p.GetPosition().y)
            if lo_x <= px <= hi_x and lo_y <= py <= hi_y:
                out.append(f'pad {fp.GetReference()}.{p.GetNumber()}'
                           f'@({px:.2f},{py:.2f})')
    for t in board.GetTracks():
        if t.GetNetname() != net:
            continue
        if t.Type() == pcbnew.PCB_VIA_T:
            px, py = MMt(t.GetPosition().x), MMt(t.GetPosition().y)
            if lo_x <= px <= hi_x and lo_y <= py <= hi_y:
                out.append(f'via@({px:.2f},{py:.2f})')
        else:
            sx, sy = MMt(t.GetStart().x), MMt(t.GetStart().y)
            ex, ey = MMt(t.GetEnd().x), MMt(t.GetEnd().y)
            if (min(sx, ex) <= hi_x and max(sx, ex) >= lo_x
                    and min(sy, ey) <= hi_y and max(sy, ey) >= lo_y):
                out.append(f'trk L{t.GetLayer()} ({sx:.2f},{sy:.2f})'
                           f'->({ex:.2f},{ey:.2f}) '
                           f'w={MMt(t.GetWidth()):.2f}')
    return '; '.join(out[:5])

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
            return (f'{n2} {desc} [{objects_near(n2, x1, y1, x2, y2)}]')
    return None

def disc_blocked(net, x, y):
    s = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MMf(x), MMf(y)),
                             pcbnew.VECTOR2I(MMf(x), MMf(y)), MMf(0.6))
    for kind, n2, l2, s2, desc in items:
        if n2 == net or kind == 'zone':
            continue
        need = need_for(net, n2, l2)
        if s.Collide(s2, MMf(need - 0.001)):
            return (f'{n2} {desc} [{objects_near(n2, x, y, x, y)}]')
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

def via_scan(net, sx, sy, xlo, xhi, ylo, yhi, step=0.25, w=0.25):
    """First (x,y) in the grid whose disc is clear AND whose
    straight F stub from (sx,sy) is clear. Returns (x, y)."""
    y = ylo
    while y <= yhi + 1e-9:
        x = xlo
        while x <= xhi + 1e-9:
            if (not disc_blocked(net, x, y)
                    and not seg_blocked(net, sx, sy, x, y, w,
                                        pcbnew.F_Cu)):
                return (x, y)
            x += step
        y += step
    return None

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

# 0. Facts: pad bboxes the hand geometry kept guessing.
def sec_facts():
    for ref, pin in [('U4', '11'), ('U4', '12'), ('U4', '14'),
                     ('U10', '7'), ('U10', '8'), ('U10', '11'),
                     ('U10', '3'), ('U10', '2'), ('D2', '3')]:
        print(f'  {ref}.{pin} bbox {pad_bbox(ref, pin)}')
section('0 pad bboxes', sec_facts)

# 1. +5V U14.6 south: rip EVERY GND F track in the stub corridor
# box, then stub + via + In2 + via up + stub (batch 4 route).
def sec_u14():
    rip('GND', pcbnew.F_Cu, 60.2, 60.95, 63.1, 64.9)
    p = pad_pos('U14', '6')
    add_track('+5V', p[0], 63.15, p[0], 64.8, w=0.3)
    add_via('+5V', p[0], 64.8)
    add_track('+5V', p[0], 64.8, 57.8, 61.6, layer=pcbnew.In2_Cu)
    refresh()
    add_via('+5V', 57.8, 61.6)
    add_track('+5V', 57.8, 61.6, 57.45, 61.3, w=0.3)
section('1 +5V U14.6 south, corridor ripped', sec_u14)

# 2. +3V3A east run at y=-17.1 (north of the PHY_1V8 stub end
# (87.25,-17.62): 0.52-0.225 clears the 0.25 class).
def sec_33a():
    add_track('+3V3A', 82.6, -17.6, 82.6, -17.1, w=0.25)
    add_track('+3V3A', 82.6, -17.1, 87.9, -17.1, w=0.25)
    add_track('+3V3A', 87.9, -17.1, 87.9, -18.56, w=0.25)
section('2 +3V3A y=-17.1', sec_33a)

# 3. HV_FBX In2: straighter line via (36.5,-3.9).
def sec_fbx():
    add_track('HV_FBX', 42.9, 0.1, 36.5, -3.9,
              layer=pcbnew.In2_Cu)
    add_track('HV_FBX', 36.5, -3.9, 34.5, -4.6,
              layer=pcbnew.In2_Cu)
    refresh()
    add_via('HV_FBX', 34.5, -4.6)
    add_track('HV_FBX', 34.5, -4.6, 33.46, -5.25)
section('3 HV_FBX In2 v3', sec_fbx)

# 4. HV_INTVCC: via_scan west/south-west of the pad, then In2
# west + north, via up, stub to C31.1's group.
def sec_intvcc():
    site = via_scan('HV_INTVCC', 16.15, -15.0,
                    13.9, 15.9, -16.4, -13.6)
    assert site, 'no via site found'
    print(f'  via site {site}')
    add_track('HV_INTVCC', 16.15, -15.0, site[0], site[1])
    add_via('HV_INTVCC', site[0], site[1])
    add_track('HV_INTVCC', site[0], site[1], 14.6, site[1],
              layer=pcbnew.In2_Cu)
    add_track('HV_INTVCC', 14.6, site[1], 14.6, -10.5,
              layer=pcbnew.In2_Cu)
    refresh()
    add_via('HV_INTVCC', 14.6, -10.5)
    add_track('HV_INTVCC', 14.6, -10.5, 13.62, -9.11)
section('4 HV_INTVCC via_scan', sec_intvcc)

# 5. HV_SS: via_scan from the batch-2 stub end (10.7,-15.0)
# over the west/south field, then In2 east, via up, stub in.
def sec_ss():
    site = via_scan('HV_SS', 10.7, -15.0,
                    9.2, 11.1, -16.2, -12.4)
    assert site, 'no via site found'
    print(f'  via site {site}')
    add_track('HV_SS', 10.7, -15.0, site[0], site[1])
    add_via('HV_SS', site[0], site[1])
    add_track('HV_SS', site[0], site[1], site[0], -11.0,
              layer=pcbnew.In2_Cu)
    add_track('HV_SS', site[0], -11.0, 15.4, -11.0,
              layer=pcbnew.In2_Cu)
    refresh()
    add_via('HV_SS', 15.4, -11.0)
    add_track('HV_SS', 15.4, -11.0, 16.02, -11.01)
section('5 HV_SS via_scan', sec_ss)

# 6. HV_RAW legs 2-4 (leg 1 placed in batch 4): from (43.3,-3.6)
# SW through the corridor R34's move opened.
def sec_raw():
    add_track('HV_RAW', 43.3, -3.6, 42.5, -4.5, w=0.4)
    add_track('HV_RAW', 42.5, -4.5, 40.2, -5.2, w=0.4)
    add_track('HV_RAW', 40.2, -5.2, 39.53, -9.8, w=0.4)
section('6 HV_RAW legs 2-4', sec_raw)

# 7. APD_K R34 group -> main: north run at x=41.5 from the moved
# R34.1 pad. Batch 4 refused it on R50.2 (HV_FBX): the run at
# x=41.5 passes R50.2's pad (41.16,-1.6) 1.12x2.65 -> x[40.60,
# 41.72]: the run is INSIDE the pad's x-range at 1.0 class.
# Route east of R50.2 instead: from R34.1 north to y=-4.4, east
# to x=43.4 (east of R50.2's shadow 41.72+1.0+0.2=42.92), north
# to the main track (41.38,0.38)?? that track is WEST. Main's
# east items: the staircase via (41.125,0.625) is west too.
# Go north at x=43.4 to y=1.5, west at y=1.5 to (41.4,1.5),
# south into (41.38,0.38).
def sec_apdk():
    r341 = pad_pos('R34', '1')
    add_track('APD_K', r341[0], r341[1], 41.54, -4.4, w=0.4)
    add_track('APD_K', 41.54, -4.4, 43.4, -4.4, w=0.4)
    add_track('APD_K', 43.4, -4.4, 43.4, 1.5, w=0.4)
    add_track('APD_K', 43.4, 1.5, 41.4, 1.5, w=0.4)
    add_track('APD_K', 41.4, 1.5, 41.38, 0.38, w=0.4)
section('7 APD_K R34 group -> main (east loop)', sec_apdk)

# 8. CC2: steeper first drop (clears B4's real bbox by 0.315),
# east at y=72.3, north into the track end.
def sec_cc2():
    add_track('CC2', 30.5, 72.55, 30.9, 72.3)
    add_track('CC2', 30.9, 72.3, 32.81, 72.3)
    add_track('CC2', 32.81, 72.3, 32.81, 72.42)
section('8 CC2 steep diagonal', sec_cc2)

# 9. +3V3D_CDR U4.12: NE diagonal (away from U4.11, over the
# REFCLKN fanout's tail) as a lengthened stub for heal.
def sec_u412():
    add_track('+3V3D_CDR', 54.75, -16.06, 55.9, -14.9, w=0.3)
section('9 +3V3D_CDR U4.12 NE stub', sec_u412)

board.Save(OUT)
board = pcbnew.LoadBoard(OUT)
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(OUT)
print(f'saved {OUT}')

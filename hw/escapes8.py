#!/usr/bin/env python3
"""Escape + join surgery batch 8 -- cross-section deconfliction
(batch 7's HV_FBX In2 vertical at x=42.9 fenced batch 7's own
HV_RAW via; the FBX In2 is reworked to a diagonal that stays
west, freeing the corridor mouth), plus via-site hunts with
dry-run checks. Last hand batch before the engine round.
Usage: xvfb-run -a python3 hw/escapes8.py <src> <out>
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

def objects_near(net, x, y, slack=2.2):
    out = []
    for t in board.GetTracks():
        if t.GetNetname() != net:
            continue
        if t.Type() == pcbnew.PCB_VIA_T:
            px, py = MMt(t.GetPosition().x), MMt(t.GetPosition().y)
            if abs(px - x) < slack and abs(py - y) < slack:
                out.append(f'via@({px:.2f},{py:.2f})')
        else:
            sx, sy = MMt(t.GetStart().x), MMt(t.GetStart().y)
            ex, ey = MMt(t.GetEnd().x), MMt(t.GetEnd().y)
            if (min(sx, ex) <= x + slack and max(sx, ex) >= x - slack
                    and min(sy, ey) <= y + slack
                    and max(sy, ey) >= y - slack):
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
            return (f'{n2} {desc} '
                    f'[{objects_near(n2, (x1 + x2) / 2, (y1 + y2) / 2)}]')
    return None

def disc_blocked(net, x, y):
    s = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MMf(x), MMf(y)),
                             pcbnew.VECTOR2I(MMf(x), MMf(y)), MMf(0.6))
    for kind, n2, l2, s2, desc in items:
        if n2 == net or kind == 'zone':
            continue
        need = need_for(net, n2, l2)
        if s.Collide(s2, MMf(need - 0.001)):
            return f'{n2} {desc} [{objects_near(n2, x, y)}]'
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

# 1. HV_FBX In2 rework: rip batch 7's x=42.9 vertical + west run
# at y=-5.6 (keep the (34.5,-5.6)->(34.5,-4.6) north stub), lay
# the diagonal (42.9,0.1)->(38.5,-1.2)->(34.5,-5.6), then via up
# jogged west to (33.2,-4.6) (R49.1's pad fences (34.5,-4.6)).
def sec_fbx():
    rip_exact('HV_FBX', pcbnew.In2_Cu,
              {(42.9, 0.1, 42.9, -5.6), (42.9, -5.6, 34.5, -5.6)})
    add_track('HV_FBX', 42.9, 0.1, 38.5, -1.2,
              layer=pcbnew.In2_Cu)
    add_track('HV_FBX', 38.5, -1.2, 34.5, -5.6,
              layer=pcbnew.In2_Cu)
    add_track('HV_FBX', 34.5, -4.6, 33.2, -4.6,
              layer=pcbnew.In2_Cu)
    refresh()
    add_via('HV_FBX', 33.2, -4.6)
    add_track('HV_FBX', 33.2, -4.6, 33.46, -5.25)
section('1 HV_FBX In2 diagonal + via west', sec_fbx)

# 2. HV_RAW v5 retry (mouth now free of the FBX vertical):
# F leg from batch 4's (43.3,-3.6), via (42.9,-4.7), In2 west,
# via up (39.9,-5.6), F jog + south into the island track.
def sec_raw():
    add_track('HV_RAW', 43.3, -3.6, 42.9, -4.7, w=0.4)
    add_via('HV_RAW', 42.9, -4.7)
    add_track('HV_RAW', 42.9, -4.7, 39.9, -5.6, w=0.4,
              layer=pcbnew.In2_Cu)
    refresh()
    add_via('HV_RAW', 39.9, -5.6)
    add_track('HV_RAW', 39.9, -5.6, 39.3, -7.5, w=0.4)
    add_track('HV_RAW', 39.3, -7.5, 39.53, -9.8, w=0.4)
section('2 HV_RAW v5 retry', sec_raw)

# 3. +5V U14.6 In2 reroute: batch 7 left the F stub + via at
# (60.45,64.8). The direct In2 diagonal hit a SET_A In2 track;
# waypoint south-west first.
def sec_u14():
    add_track('+5V', 60.45, 64.8, 59.0, 63.4,
              layer=pcbnew.In2_Cu)
    add_track('+5V', 59.0, 63.4, 57.8, 61.6,
              layer=pcbnew.In2_Cu)
    refresh()
    add_via('+5V', 57.8, 61.6)
    add_track('+5V', 57.8, 61.6, 57.45, 61.3, w=0.3)
section('3 +5V U14.6 In2 waypoint', sec_u14)

# 4. +3V3A via hunt along the placed F run (82.6..84.0, -17.1):
# batch 7's via at (84.0,-17.1) hit a USB_RST track; scan sites
# on/near the run for a clear disc + clear In2 east + the south
# stub at x=87.9 is fixed, so the In2 leg is (site)->(87.9,-17.1).
def sec_33a():
    for x, y in [(83.6, -17.1), (83.8, -16.8), (84.3, -16.9),
                 (83.4, -17.3), (84.0, -16.6)]:
        if disc_blocked('+3V3A', x, y):
            continue
        if seg_blocked('+3V3A', x, y, 87.9, -17.1, 0.25,
                       pcbnew.In2_Cu):
            continue
        print(f'  via site ({x},{y})')
        add_via('+3V3A', x, y)
        add_track('+3V3A', x, y, 87.9, -17.1,
                  layer=pcbnew.In2_Cu)
        refresh()
        add_via('+3V3A', 87.9, -17.1)
        add_track('+3V3A', 87.9, -17.1, 87.9, -18.56, w=0.25)
        return
    raise AssertionError('no via site in the candidate list')
section('4 +3V3A via hunt', sec_33a)

# 5. HV_INTVCC via-up grid hunt around the In2 end (14.6,-10.5).
def sec_intvcc():
    y = -11.4
    while y <= -9.4 + 1e-9:
        x = 13.4
        while x <= 15.8 + 1e-9:
            if (not disc_blocked('HV_INTVCC', x, y)
                    and not seg_blocked('HV_INTVCC', 14.6, -10.5,
                                        x, y, 0.25, pcbnew.In2_Cu)
                    and not seg_blocked('HV_INTVCC', x, y,
                                        13.62, -9.11, 0.25,
                                        pcbnew.F_Cu)):
                print(f'  via-up site ({x:.1f},{y:.1f})')
                add_track('HV_INTVCC', 14.6, -10.5, x, y,
                          layer=pcbnew.In2_Cu)
                refresh()
                add_via('HV_INTVCC', x, y)
                add_track('HV_INTVCC', x, y, 13.62, -9.11)
                return
            x += 0.2
        y += 0.2
    raise AssertionError('no via-up site in the grid')
section('5 HV_INTVCC via-up grid hunt', sec_intvcc)

# 6. CC2 south run at x=30.52 (batch 7's x=30.44 grazed a
# DP_CON track; 30.52 keeps 0.255 from B4's pad at neck width).
def sec_cc2():
    add_track('CC2', 30.5, 72.55, 30.52, 73.0, w=0.15)
    add_track('CC2', 30.52, 73.0, 30.52, 74.3, w=0.15)
    add_track('CC2', 30.52, 74.3, 33.71, 74.3)
section('6 CC2 x=30.52', sec_cc2)

board.Save(OUT)
board = pcbnew.LoadBoard(OUT)
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(OUT)
print(f'saved {OUT}')

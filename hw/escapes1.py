#!/usr/bin/env python3
"""Escape + join surgery batch 1 on the sealed-pad residue.

Every section is independent and non-fatal: segments are placed
with hops-style collision asserts (check_pcb.need_for); a refused
section prints REFUSED with the blocker and the batch continues.
Diagnosis per section is in its comment (probe_local /
probe-ulpi / escape-fan records in results/).
Usage: xvfb-run -a python3 hw/escapes1.py <src> <out>
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
            return (n2, desc)
    return None

def disc_blocked(net, x, y):
    s = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MMf(x), MMf(y)),
                             pcbnew.VECTOR2I(MMf(x), MMf(y)), MMf(0.6))
    for kind, n2, l2, s2, desc in items:
        if n2 == net or kind == 'zone':
            continue
        need = need_for(net, n2, l2)
        if s.Collide(s2, MMf(need - 0.001)):
            return (n2, desc)
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
    global items
    print(f'--- {name} ---')
    try:
        fn()
        refresh()
        print(f'  [{name} OK]')
    except AssertionError as exc:
        refresh()
        print(f'  [{name} REFUSED: {exc}]')

# A. +5V U11 cluster: stub ends (16.38,63.25/63.75) run east then
# north on F at x=16.9 (0.40 clear of the FB_3V3 endpoint at
# (16.08,66.21)), via down at (16.9,67.12) into the +5V L2 web
# track (15.62,67.12)->(19.12,67.12). U11.13 joins diagonally.
def sec_a():
    add_track('+5V', 16.38, 63.75, 16.9, 63.75, w=0.6)
    add_track('+5V', 16.9, 63.75, 16.9, 67.12, w=0.6)
    add_via('+5V', 16.9, 67.12)
    add_track('+5V', 15.34, 62.81, 15.79, 63.25)
section('A +5V U11 cluster', sec_a)

# B. +5V U14.6: NW exit above the GND staircase hugging its south,
# west at y=64.8, south at x=57.45 into the main stub (57.45,61.85).
def sec_b():
    p = pad_pos('U14', '6')
    add_track('+5V', p[0], p[1], 59.2, 64.8, w=0.3)
    add_track('+5V', 59.2, 64.8, 57.45, 64.8, w=0.3)
    add_track('+5V', 57.45, 64.8, 57.45, 61.85, w=0.3)
section('B +5V U14.6', sec_b)

# D. SET_P U13.7 (49.55,62.50): north to y=64.2, west under the
# C42/C43 pad row, up into the C42.1/R40.1 group's track end
# (42.73,64.47).
def sec_d():
    p = pad_pos('U13', '7')
    add_track('SET_P', p[0], p[1], p[0], 64.2)
    add_track('SET_P', p[0], 64.2, 42.73, 64.2)
    add_track('SET_P', 42.73, 64.2, 42.73, 64.47)
section('D SET_P U13.7', sec_d)

# F. +3V3A U7.6: west out of the pad row at x=82.6 (0.35 clear of
# the DM_PHY via (83.38,-18.38)), north, east at y=-17.6 (0.375
# clear of the U7 north stub ends), south into the +3V3A track
# (87.75,-18.56)->(88.00,-18.56).
def sec_f():
    p = pad_pos('U7', '6')
    add_track('+3V3A', p[0], p[1], 82.6, p[1], w=0.3)
    add_track('+3V3A', 82.6, p[1], 82.6, -17.6, w=0.3)
    add_track('+3V3A', 82.6, -17.6, 87.9, -17.6, w=0.3)
    add_track('+3V3A', 87.9, -17.6, 87.9, -18.56, w=0.3)
section('F +3V3A U7.6', sec_f)

# G. HV_FBX R50.2: south off the pad, via at (40.3,-3.6) (1.2
# clear of R50.1), In2 south-west, via up at (34.5,-4.6) beside
# the FBX web (same-net neighbours), F stub into the web track
# end (33.46,-5.25).
def sec_g():
    p = pad_pos('R50', '2')
    add_track('HV_FBX', p[0], -2.6, p[0], -3.6)
    add_track('HV_FBX', p[0], -3.6, 40.3, -3.6)
    add_via('HV_FBX', 40.3, -3.6)
    add_track('HV_FBX', 40.3, -3.6, 34.5, -4.6, layer=pcbnew.In2_Cu)
    refresh()
    add_via('HV_FBX', 34.5, -4.6)
    add_track('HV_FBX', 34.5, -4.6, 33.46, -5.25)
section('G HV_FBX R50.2', sec_g)

# H. HV_RAW R29.1: stub SW to via (43.45,-3.9) (1.18 clear of
# R29.2, 1.05 clear of R34.1), In2 SW, via up at (40.5,-8.8),
# F stub into the HV_RAW island track (39.53,-9.80).
def sec_h():
    p = pad_pos('R29', '1')
    add_track('HV_RAW', p[0], p[1], 43.45, -3.9)
    add_via('HV_RAW', 43.45, -3.9)
    add_track('HV_RAW', 43.45, -3.9, 40.5, -8.8,
              layer=pcbnew.In2_Cu)
    refresh()
    add_via('HV_RAW', 40.5, -8.8)
    add_track('HV_RAW', 40.5, -8.8, 39.53, -9.8)
section('H HV_RAW R29.1', sec_h)

# I. APD_K island (42.45,-10)->(43.02,-10): NW into R34.1's pad
# (main group since heal batch 2).
def sec_i():
    add_track('APD_K', 43.02, -10.0, 42.6, -7.2, w=0.4)
    r341 = pad_pos('R34', '1')
    add_track('APD_K', 42.6, -7.2, r341[0], r341[1], w=0.4)
section('I APD_K island->R34.1', sec_i)

# J. APD_K R47.2: south-east jog around the U9 GND pads and the
# GND stitch web, west into the (now main) island stub (43.02,-10).
def sec_j():
    p = pad_pos('R47', '2')
    add_track('APD_K', p[0], p[1], 49.9, -1.6, w=0.4)
    add_track('APD_K', 49.9, -1.6, 49.9, -7.0, w=0.4)
    add_track('APD_K', 49.9, -7.0, 47.5, -8.5, w=0.4)
    add_track('APD_K', 47.5, -8.5, 45.0, -9.5, w=0.4)
    add_track('APD_K', 45.0, -9.5, 43.02, -10.0, w=0.4)
section('J APD_K R47.2', sec_j)

# K. APD_K R31.1: rip the GND stitch column segments at x~32.88
# fencing the pad's east face (stitch copper; the pour still
# covers the area and GND re-stitches in a later round), then F
# from the staircase end (34.62,2.12) SW into the pad.
def sec_k():
    n = 0
    for t in list(board.GetTracks()):
        if t.GetNetname() != 'GND' or t.Type() == pcbnew.PCB_VIA_T:
            continue
        if t.GetLayer() != pcbnew.F_Cu:
            continue
        sx, sy = MMt(t.GetStart().x), MMt(t.GetStart().y)
        ex, ey = MMt(t.GetEnd().x), MMt(t.GetEnd().y)
        if all(32.6 <= x <= 33.1 and -3.5 <= y <= 1.5
               for x, y in ((sx, sy), (ex, ey))):
            board.Remove(t)
            n += 1
    print(f'  ripped {n} GND stitch segments in the R31.1 east fence')
    refresh()
    add_track('APD_K', 34.62, 2.12, 33.6, 0.5, w=0.4)
    add_track('APD_K', 33.6, 0.5, 33.6, -1.6, w=0.4)
    r311 = pad_pos('R31', '1')
    add_track('APD_K', 33.6, -1.6, r311[0], r311[1], w=0.4)
section('K APD_K R31.1', sec_k)

# L. GND R48.2: stub south off the moved R48's GND pad toward the
# pour (zone refill at save decides the join).
def sec_l():
    p = pad_pos('R48', '2')
    add_track('GND', p[0], p[1], p[0], p[1] + 2.2, w=0.3)
section('L GND R48.2 stub', sec_l)

# N. PHY_1V8: U7.26 group south track end (87.25,-24.38) east,
# north at x=89.3 (0.4 clear of the ULPI stub ends), west at
# y=-17.5 into U7.15's stub (87.25,-17.62).
def sec_n():
    add_track('PHY_1V8', 87.25, -24.38, 89.3, -24.38)
    add_track('PHY_1V8', 89.3, -24.38, 89.3, -17.5)
    add_track('PHY_1V8', 89.3, -17.5, 87.25, -17.5)
    add_track('PHY_1V8', 87.25, -17.5, 87.25, -17.62)
section('N PHY_1V8 U7.26<->U7.15', sec_n)

# T. CC2: J1.B5 stub end (30.5,73.18) east/north into the R19.1
# group's track end (32.81,72.42).
def sec_t():
    add_track('CC2', 30.5, 73.18, 31.8, 72.9)
    add_track('CC2', 31.8, 72.9, 32.81, 72.42)
section('T CC2 J1.B5', sec_t)

board.Save(OUT)
board = pcbnew.LoadBoard(OUT)
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(OUT)
print(f'saved {OUT}')

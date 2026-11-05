#!/usr/bin/env python3
"""Escape + join surgery batch 2: escapes1's refused sections with
the geometry corrected per the named blockers, plus stub
lengthening for the heal-refused hauls (engines take the stub
once its end stands in open field). Blockers print with bbox
centres this time. Non-fatal per section.
Usage: xvfb-run -a python3 hw/escapes2.py <src> <out>
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

def where(s2):
    try:
        bb = s2.GetBoundingBox()
        return (f'@({MMt(bb.GetCenter().x):.2f},'
                f'{MMt(bb.GetCenter().y):.2f})')
    except Exception:
        return ''

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
            return f'{n2} {desc}{where(s2)}'
    return None

def disc_blocked(net, x, y):
    s = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MMf(x), MMf(y)),
                             pcbnew.VECTOR2I(MMf(x), MMf(y)), MMf(0.6))
    for kind, n2, l2, s2, desc in items:
        if n2 == net or kind == 'zone':
            continue
        need = need_for(net, n2, l2)
        if s.Collide(s2, MMf(need - 0.001)):
            return f'{n2} {desc}{where(s2)}'
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

# A2. +5V U11 north run: escapes1 got (16.38,63.75)->(16.9,63.75)
# placed; the north run at x=16.9 was refused by a +3V3D track.
# Retry at x=17.6 (east), via into the L2 web at (17.6,67.12).
def sec_a2():
    add_track('+5V', 16.9, 63.75, 17.6, 63.75, w=0.6)
    add_track('+5V', 17.6, 63.75, 17.6, 67.12, w=0.6)
    add_via('+5V', 17.6, 67.12)
section('A2 +5V U11 north run retry', sec_a2)

# B2. +5V U14.6: east first (U14.7/SET_A fences the NW diagonal),
# north at x=61.6, west at y=65.9 (0.78 clear of the +3V3A via
# (62.38,65.12)), south at x=57.45 into the main stub.
def sec_b2():
    p = pad_pos('U14', '6')
    add_track('+5V', p[0], p[1], 61.6, p[1], w=0.3)
    add_track('+5V', 61.6, p[1], 61.6, 65.9, w=0.3)
    add_track('+5V', 61.6, 65.9, 57.45, 65.9, w=0.3)
    add_track('+5V', 57.45, 65.9, 57.45, 61.85, w=0.3)
section('B2 +5V U14.6', sec_b2)

# D2. SET_P U13.7: south exit first (U13.6/+5V fences the north
# run), east at y=60.8, north at x=51.5 (west of the +5V via
# (52.88,61.12), south of C43.1's pad), west at y=64.2, up into
# the group track end (42.73,64.47).
def sec_d2():
    p = pad_pos('U13', '7')
    add_track('SET_P', p[0], p[1], p[0], 60.8)
    add_track('SET_P', p[0], 60.8, 51.5, 60.8)
    add_track('SET_P', 51.5, 60.8, 51.5, 64.2)
    add_track('SET_P', 51.5, 64.2, 42.73, 64.2)
    add_track('SET_P', 42.73, 64.2, 42.73, 64.47)
section('D2 SET_P U13.7', sec_d2)

# F2. +3V3A U7.6: U7.5 is the QFN exposed pad (its west edge at
# x~83.5 is flush with the perimeter pads) -- start the west run
# at the pad's west EDGE (83.12) so it never overlaps the EP.
def sec_f2():
    add_track('+3V3A', 83.12, -20.25, 82.6, -20.25, w=0.25)
    add_track('+3V3A', 82.6, -20.25, 82.6, -17.6, w=0.25)
    add_track('+3V3A', 82.6, -17.6, 87.9, -17.6, w=0.25)
    add_track('+3V3A', 87.9, -17.6, 87.9, -18.56, w=0.25)
section('F2 +3V3A U7.6 edge exit', sec_f2)

# C. +5V U7.4 west stub (edge start, EP-safe), lengthened for a
# later heal/thread attempt.
def sec_c():
    add_track('+5V', 83.12, -21.25, 80.6, -21.25, w=0.3)
section('C +5V U7.4 stub', sec_c)

# U. DP_PHY U7.7 west stub (edge start).
def sec_u():
    add_track('DP_PHY', 83.12, -19.75, 81.0, -19.75)
section('U DP_PHY U7.7 stub', sec_u)

# G2. HV_FBX R50.2: escapes1's south stub refused by an APD_K
# stubcheck track near (41.16,-3). Go UNDER it: stub south on F
# only to y=-2.95 is the same wall; instead via at the pad's SE
# (42.3,-3.3) after a short F jog east along the pad's south face.
def sec_g2():
    add_track('HV_FBX', 41.16, -2.95, 42.3, -3.3)
    add_via('HV_FBX', 42.3, -3.3)
    add_track('HV_FBX', 42.3, -3.3, 34.5, -4.6,
              layer=pcbnew.In2_Cu)
    refresh()
    add_via('HV_FBX', 34.5, -4.6)
    add_track('HV_FBX', 34.5, -4.6, 33.46, -5.25)
section('G2 HV_FBX R50.2', sec_g2)

# H2. HV_RAW R29.1: via moved north to (43.45,-2.0), out of the
# CMP_QN B vertical's 1.0 shadow (its end is (43.12,-3.62)).
def sec_h2():
    p = pad_pos('R29', '1')
    add_track('HV_RAW', p[0], p[1], 43.45, -2.0)
    add_via('HV_RAW', 43.45, -2.0)
    add_track('HV_RAW', 43.45, -2.0, 40.5, -8.8,
              layer=pcbnew.In2_Cu)
    refresh()
    add_via('HV_RAW', 40.5, -8.8)
    add_track('HV_RAW', 40.5, -8.8, 39.53, -9.8)
section('H2 HV_RAW R29.1', sec_h2)

# J2. APD_K R47.2: the U9 pad columns admit no 1.0-class F
# corridor; cross under on In2 (0.3 internal need). Via south of
# the pad (1.67 clear of U9.2), In2 south + west, via up west of
# the TP_HV via, F stub into the island stub (43.02,-10).
def sec_j2():
    p = pad_pos('R47', '2')
    add_track('APD_K', p[0], p[1], p[0], -2.9, w=0.4)
    add_via('APD_K', p[0], -2.9)
    add_track('APD_K', p[0], -2.9, p[0], -8.6, w=0.4,
              layer=pcbnew.In2_Cu)
    add_track('APD_K', p[0], -8.6, 43.8, -8.6, w=0.4,
              layer=pcbnew.In2_Cu)
    add_track('APD_K', 43.8, -8.6, 43.8, -9.3, w=0.4,
              layer=pcbnew.In2_Cu)
    refresh()
    add_via('APD_K', 43.8, -9.3)
    add_track('APD_K', 43.8, -9.3, 43.02, -10.0, w=0.4)
section('J2 APD_K R47.2 via In2', sec_j2)

# K2. APD_K R31.1: rip the ONE GND column segment fencing the
# pocket ((32.83,-2.50)->(32.88,0.38); stitch copper, pour still
# covers), via ON the B-feed run at (33.3,-1.92) (1.003 clear of
# R31.2's pad at the 1.0 class), F stub west into the pad's east
# edge.
def sec_k2():
    n = 0
    for t in list(board.GetTracks()):
        if t.GetNetname() != 'GND' or t.Type() == pcbnew.PCB_VIA_T:
            continue
        sx, sy = MMt(t.GetStart().x), MMt(t.GetStart().y)
        ex, ey = MMt(t.GetEnd().x), MMt(t.GetEnd().y)
        mx, my = (sx + ex) / 2, (sy + ey) / 2
        if 32.6 <= mx <= 33.1 and -3.5 <= my <= 1.5:
            board.Remove(t)
            n += 1
    print(f'  ripped {n} GND segments fencing R31.1')
    refresh()
    add_via('APD_K', 33.3, -1.92)
    add_track('APD_K', 33.3, -1.92, 32.85, -1.7, w=0.4)
    r311 = pad_pos('R31', '1')
    add_track('APD_K', 32.85, -1.7, r311[0], r311[1], w=0.4)
section('K2 APD_K R31.1', sec_k2)

# N2. PHY_1V8: east run jogged south to y=-24.9 (the +3V3A via
# (88.12,-23.62) is fat; 1.28-0.5-0.125 clears at -24.9).
def sec_n2():
    add_track('PHY_1V8', 87.25, -24.38, 87.9, -24.9)
    add_track('PHY_1V8', 87.9, -24.9, 89.3, -24.9)
    add_track('PHY_1V8', 89.3, -24.9, 89.3, -17.5)
    add_track('PHY_1V8', 89.3, -17.5, 87.25, -17.5)
    add_track('PHY_1V8', 87.25, -17.5, 87.25, -17.62)
section('N2 PHY_1V8 U7.26<->U7.15', sec_n2)

# T2. CC2: south out of J1.B5 along its own column (0.225 clear
# of B4/B6), east at y=72.42 into the R19.1 group track end.
def sec_t2():
    add_track('CC2', 30.5, 73.18, 30.5, 72.42)
    add_track('CC2', 30.5, 72.42, 32.81, 72.42)
section('T2 CC2 J1.B5', sec_t2)

# E. +3V3D_CDR U4.12 north stub (from the pad's north edge).
def sec_e():
    add_track('+3V3D_CDR', 54.75, -16.5, 54.75, -13.2, w=0.3)
section('E +3V3D_CDR U4.12 stub', sec_e)

# Q. CDR_PIN: lengthen U4.5's stub SW into open field.
def sec_q():
    add_track('CDR_PIN', 52.205, -18.25, 50.0, -19.6)
section('Q CDR_PIN stub', sec_q)

# R. CDR_SQUELCH: lengthen U4.27's stub south.
def sec_r():
    add_track('CDR_SQUELCH', 55.75, -21.295, 55.75, -24.5)
section('R CDR_SQUELCH stub', sec_r)

# S. CAP_DATA: lengthen U5.3's stub south.
def sec_s():
    add_track('CAP_DATA', 66.42, -20.405, 66.42, -24.5)
section('S CAP_DATA stub', sec_s)

# V. HV_INTVCC U10.8: via east at (17.5,-15.0) (0.42/0.5 clear
# of U10.7/U10.9 pads, 1.45 clear of the MOS_G palisade), In2
# north + west, via up at (14.2,-10.5), stub into C31.1's group
# track end (13.62,-9.11).
def sec_v():
    add_via('HV_INTVCC', 17.5, -15.0)
    add_track('HV_INTVCC', 16.875, -15.0, 17.5, -15.0)
    add_track('HV_INTVCC', 17.5, -15.0, 17.5, -10.5,
              layer=pcbnew.In2_Cu)
    add_track('HV_INTVCC', 17.5, -10.5, 14.2, -10.5,
              layer=pcbnew.In2_Cu)
    refresh()
    add_via('HV_INTVCC', 14.2, -10.5)
    add_track('HV_INTVCC', 14.2, -10.5, 13.62, -9.11)
section('V HV_INTVCC U10.8', sec_v)

# W. HV_SS U10.3: stub west off its stub end, via at (10.7,-15),
# In2 east along y=-11 (north of the FBX L2 staircase), via up
# at (15.4,-11.0), stub into C30.1's group track (16.02,-11.01).
def sec_w():
    add_track('HV_SS', 11.205, -15.0, 10.7, -15.0)
    add_via('HV_SS', 10.7, -15.0)
    add_track('HV_SS', 10.7, -15.0, 10.7, -11.0,
              layer=pcbnew.In2_Cu)
    add_track('HV_SS', 10.7, -11.0, 15.4, -11.0,
              layer=pcbnew.In2_Cu)
    refresh()
    add_via('HV_SS', 15.4, -11.0)
    add_track('HV_SS', 15.4, -11.0, 16.02, -11.01)
section('W HV_SS U10.3', sec_w)

board.Save(OUT)
board = pcbnew.LoadBoard(OUT)
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(OUT)
print(f'saved {OUT}')

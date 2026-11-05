#!/usr/bin/env python3
"""APD_K fence rip + HV midpoint hops + APD_K re-feed (one surgery).

Diagnosis (probe dumps on exp34): APD_K's old feed to R31.1's OLD
position survives as a doubled fence at x~36.4-36.9, y 0.38..-5.0
plus a southern tail cluster (x 29..37, y -8..-4.5). R31.2/R49.1's
pads sit inside its 1.0 mm shadow, so no midpoint hop can leave
the pads. The fence fed a pad that moved west; it is ripped here
and APD_K is re-fed to R31.1 (32.24,-1.6) from the northern web's
west end, down the x=33.4 lane (exactly 1.0 off R31.2's pad).

Deletions (APD_K F.Cu tracks only):
- both endpoints in x[34,43] y[-8,1] (the fence pair + jogs), or
- both endpoints in x[29,37] y[-8,-4.5] (the southern tail), or
- an endpoint at (41.96,-10) (the stub from R29's old pad).
Then the midpoint hops (HV_R31A/B, HV_R29M, HV_R30M), the APD_K
feed, and the TP_HV tail-island deletion (45.28,20.68). All placed
segments collision-asserted with the audit's need_for.
Usage: xvfb-run -a python3 hw/hops2.py <src> <out>

hops2 (successor, 2026-11-05): hops.py rebased onto exp33 (the
secured pass-82 base) with ONE change -- the TP_HV re-stitch takes
the south corridor (see the TP_HV section comment). hops.py's
diagonal (39.375,2.2)->(42.3,-3.3) is geometrically impossible: it
crosses R50.2's 1.0 mm HV shadow. Everything else is hops.py
verbatim; every placed segment is collision-asserted in-script, so
any exp33/exp34 geometry drift fails loud, never silent.
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
_DEAD = []

def ends(t):
    return [(MMt(t.GetStart().x), MMt(t.GetStart().y)),
            (MMt(t.GetEnd().x), MMt(t.GetEnd().y))]

n = 0
for t in list(board.GetTracks()):
    if t.GetNetname() != 'APD_K' or t.Type() == pcbnew.PCB_VIA_T:
        continue
    if t.GetLayer() != pcbnew.F_Cu:
        continue
    e = ends(t)
    in_fence = all(34 <= x <= 43 and -8 <= y <= 1 for x, y in e)
    in_tail = all(29 <= x <= 37 and -8 <= y <= -4.5 for x, y in e)
    stub29 = any(abs(x - 41.96) < 0.05 and abs(y + 10) < 0.05
                 for x, y in e)
    if in_fence or in_tail or stub29:
        _DEAD.append(t)
        board.Remove(t)
        n += 1
print(f'ripped {n} APD_K fence/tail segments')

# TP_HV's heal-placed vertical at x=39.375 (y -5..0.4) sits 0.45 mm
# from R50.1's pad — no F channel exists between the string pads
# for it. Rip its south run (x[38,41.5] y[-7,2]); it is re-stitched
# below east of the strings, north of R34.
ntp = 0
for t in list(board.GetTracks()):
    if t.GetNetname() != 'TP_HV' or t.Type() == pcbnew.PCB_VIA_T:
        continue
    if t.GetLayer() != pcbnew.F_Cu:
        continue
    e = ends(t)
    if all(38 <= x <= 41.5 and -7 <= y <= 2 for x, y in e):
        _DEAD.append(t)
        board.Remove(t)
        ntp += 1
print(f'ripped {ntp} TP_HV south-run segments')

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
    print(f'  {net}: ({x1:.2f},{y1:.2f})->({x2:.2f},{y2:.2f})')

def hop(net, a, b, waypoints=()):
    (x1, y1), (x2, y2) = a, b
    if not seg_blocked(net, x1, y1, x2, y2, 0.25, pcbnew.F_Cu):
        add_track(net, x1, y1, x2, y2)
        return
    for (wx, wy) in waypoints:
        if not seg_blocked(net, x1, y1, wx, wy, 0.25, pcbnew.F_Cu) \
                and not seg_blocked(net, wx, wy, x2, y2, 0.25,
                                    pcbnew.F_Cu):
            add_track(net, x1, y1, wx, wy)
            add_track(net, wx, wy, x2, y2)
            return
    print(f'  {net} direct blocked by: '
          f'{seg_blocked(net, x1, y1, x2, y2, 0.25, pcbnew.F_Cu)}')
    for (wx, wy) in waypoints:
        print(f'  {net} via ({wx},{wy}): leg1 '
              f'{seg_blocked(net, x1, y1, wx, wy, 0.25, pcbnew.F_Cu)} '
              f'leg2 {seg_blocked(net, wx, wy, x2, y2, 0.25, pcbnew.F_Cu)}')
    raise AssertionError(f'{net} hop: no clear path')

print('midpoint hops:')
hop('HV_R31A', pad_pos('R31', '2'), pad_pos('R49', '1'),
    [(34.9, -3.4), (35.6, -3.4)])
hop('HV_R31B', pad_pos('R49', '2'), pad_pos('R50', '1'),
    [(37.6, -3.4), (37.3, -3.2), (38.3, -3.4)])
print('GND stitch re-lay (clears the HV_R29M corridor):')
# the F stitch (46.74,-14.23)->(46.88,0.12) fences R29.2 from
# R47.1 at the 1.0 HV class. Re-lay its middle on In2: F stub
# south of the pads' latitude band, via down, In2 north under the
# pads (no shared layer), via up into the east run at (46.88,0.12).
for t in list(board.GetTracks()):
    if t.GetNetname() != 'GND' or t.Type() == pcbnew.PCB_VIA_T:
        continue
    e = ends(t)
    if any(abs(x - 46.74) < 0.05 and abs(y + 14.23) < 0.05
           for x, y in e) and \
            any(abs(x - 46.88) < 0.05 and abs(y - 0.12) < 0.05
                for x, y in e):
        _DEAD.append(t)
        board.Remove(t)
        print('  deleted the F GND stitch segment')
        break
items = build_items(board)

def disc_blocked(net, x, y):
    s = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MMf(x), MMf(y)),
                             pcbnew.VECTOR2I(MMf(x), MMf(y)),
                             MMf(0.6))
    for kind, n2, l2, s2, desc in items:
        if n2 == net or kind == 'zone':
            continue
        need = need_for(net, n2, l2)
        if s.Collide(s2, MMf(need - 0.001)):
            return (n2, desc)
    return None

def add_via(net, x, y):
    bad = disc_blocked(net, x, y)
    assert not bad, f'{net} via ({x},{y}): {bad}'
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(MMf(x), MMf(y)))
    v.SetWidth(MMf(0.6))
    v.SetDrill(MMf(0.3))
    v.SetNet(board.FindNet(net))
    board.Add(v)

add_track('GND', 46.74, -14.23, 46.74, -4.4, w=0.25)
add_via('GND', 46.74, -4.4)
add_track('GND', 46.74, -4.4, 46.88, 0.12, w=0.25,
          layer=pcbnew.In2_Cu)
add_via('GND', 46.88, 0.12)
items = build_items(board)

print('midpoint hops (continued):')
hop('HV_R29M', pad_pos('R29', '2'), pad_pos('R47', '1'),
    [(46.5, -0.9), (46.5, -2.7)])
print('R48 move + HV_R30M In2 underpass:')
# R48 (placed by the re-sync at (17.5,28.5)) sits ON the GND fence
# track at y=29 — its pad overlaps the fence. Move it north to
# y=27.3 (pad edge clears the fence by 1.05) and run the R30M hop
# under the fence on In2.
import gridplace
r48 = board.FindFootprintByReference('R48')
got = gridplace.place(board, r48, (16.8, 26.9, 18.2, 27.7),
                      (17.5, 27.3), log=print)
assert got, 'R48: no feasible point'
items = build_items(board)
add_track('HV_R30M', 15.9, 30.4, *pad_pos('R30', '2'))
add_via('HV_R30M', 15.9, 30.4)
add_track('HV_R30M', 15.9, 30.4, 16.04, 27.55, layer=pcbnew.In2_Cu)
add_via('HV_R30M', 16.04, 27.55)
r481 = pad_pos('R48', '1')
add_track('HV_R30M', 16.04, 27.55, r481[0], r481[1])

print('APD_K re-feed to R31.1:')
# The GND stitch web in x[29,34.5] y[-3,3] (staircase + the
# x=32.88 vertical) fences every F approach to R31.1's pad at the
# 1.0 class — the pad sits 0.08 from the vertical's spine. The web
# is stitch copper, not pads: rip it; the GND campaign re-stitches
# after the strings are placed (pours still cover the area).
ng = 0
for t in list(board.GetTracks()):
    if t.GetNetname() != 'GND' or t.Type() == pcbnew.PCB_VIA_T:
        continue
    if t.GetLayer() != pcbnew.F_Cu:
        continue
    e = ends(t)
    if all(29 <= x <= 34.5 and -3 <= y <= 3 for x, y in e) or \
            all(32.5 <= x <= 33.3 and -3 <= y <= 11 for x, y in e):
        _DEAD.append(t)
        board.Remove(t)
        ng += 1
print(f'  ripped {ng} GND stitch segments in the R31 box')
items = build_items(board)
r311 = pad_pos('R31', '1')
# Feed on B.Cu from the staircase's via (34.62,2.12), up west of
# the pad, F stub in. (The F lane between the ripped GND column
# and R31.2's pad is fenced by the HV_FBX via at (32.12,0.62);
# B is empty in this box.) Non-fatal: if the asserts refuse, the
# board still saves and heal_nets takes APD_K on the saved board.
try:
    add_track('APD_K', 34.62, 2.12, 33.9, 0.6, w=0.4,
              layer=pcbnew.B_Cu)
    add_track('APD_K', 33.9, 0.6, 33.9, -1.9, w=0.4,
              layer=pcbnew.B_Cu)
    add_track('APD_K', 33.9, -1.9, 31.5, -1.95, w=0.4,
              layer=pcbnew.B_Cu)
    add_track('APD_K', 31.5, -1.95, 30.35, 0.35, w=0.4,
              layer=pcbnew.B_Cu)
    add_via('APD_K', 30.35, 0.35)
    add_track('APD_K', 30.35, 0.35, 31.9, -0.9, w=0.4)
    add_track('APD_K', 31.9, -0.9, r311[0], r311[1], w=0.4)
    print('  APD_K B-feed placed')
except AssertionError as exc:
    print(f'  APD_K B-feed REFUSED in-script: {exc} '
          f'(heal_nets takes APD_K on the saved board)')

print('TP_HV re-stitch (NORTH + In2 drop, hops2 rev3):')
# Diagnosis (results/probe-tphv-exp33.txt, probe_r29.py,
# check_pcb.need_for): need(TP_HV, any foreign net) = 1.0 on
# surface layers, 0.3 on internal-only pairs. Every F column south
# is shadow-blocked: the string-pad slot is empty (west edges
# demand centre >= 39.93, R50.2 demands <= 39.48); x=44.46 hits
# R29.1's shadow (x[42.28,45.08] y[-3.28,-0.33]); x=43.4 hits both
# R29.1 and R34.1; the R29.2/R47.1 gap is 1.55 < 2x1.0+0.25.
# Route: F east at y=2.2 (1.05 clear of the APD_K via
# (41.125,0.625)), jog north, via down at (44.46,2.9) -- the via
# at (44.46,2.2) misses R29.1 by 0.115, the jog clears it -- In2
# south at the 0.3 internal need (no In2 items in the corridor),
# via up at (44.46,-7.6) (2.36 clear of R34.1), F stub into
# R34.2 (44.462,-6.0). The heal-placed x=39.38 vertical's south
# stub is ripped above and NOT recreated (it was itself a
# violation vs R49.2).
add_track('TP_HV', 39.38, 2.2, 44.46, 2.2)
add_track('TP_HV', 44.46, 2.2, 44.46, 2.9)
add_via('TP_HV', 44.46, 2.9)
add_track('TP_HV', 44.46, 2.9, 44.46, -7.6, layer=pcbnew.In2_Cu)
items = build_items(board)
# via-up at x=44.46 grazes the CMP_QN B.Cu vertical at x=43.12
# (0.89 < 1.0); x=44.9 clears it by 1.33 and the F stub angles in.
add_via('TP_HV', 44.9, -7.6)
r342 = pad_pos('R34', '2')
add_track('TP_HV', 44.9, -7.6, r342[0], r342[1])

print('TP_HV tail island:')
for t in list(board.GetTracks()):
    if t.GetNetname() != 'TP_HV' or t.Type() == pcbnew.PCB_VIA_T:
        continue
    e = ends(t)
    cx = (e[0][0] + e[1][0]) / 2
    cy = (e[0][1] + e[1][1]) / 2
    if abs(cx - 45.28) < 0.4 and abs(cy - 20.68) < 0.4:
        _DEAD.append(t)
        board.Remove(t)
        print(f'  deleted TP_HV tail stub at ({cx:.2f},{cy:.2f})')

board.Save(OUT)
board = pcbnew.LoadBoard(OUT)
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(OUT)
print(f'saved {OUT}')

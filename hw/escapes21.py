#!/usr/bin/env python3
"""Escape batch 21 -- ULPI residue hand routes (engines refused
all five: heal first-move wall, thread_far no-thread/no-pair).
- D4/D5 order fix: rip D5's F stub segments, hand-route D4
  flat at y=14.32 then SE into its via (80.12,15.38); D5
  re-heals afterwards over D4's track (0.23 clearance).
- D2: F north from U7 stub end, via at (79.05,6.6), In2 under
  ULPI_D0's F track (y=5.88), via up (78.4,5.2), F into the
  U6 stub end (78.25,5.42).
Board-agnostic: xvfb-run -a python3 hw/escapes21.py <src> <out>
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

def add_track(net, x1, y1, x2, y2, w=0.2, layer=pcbnew.F_Cu):
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
            if (abs(p[0] - x1) < 0.1 and abs(p[1] - y1) < 0.1
                    and abs(q[0] - x2) < 0.1 and abs(q[1] - y2) < 0.1):
                board.Remove(t)
                print(f'  rip {net} ({a[0]:.2f},{a[1]:.2f})->'
                      f'({b[0]:.2f},{b[1]:.2f})')
                return
    print(f'  rip {net} ({x1},{y1})->({x2},{y2}): NOT FOUND')

def section(name, fn):
    print(f'--- {name} ---')
    try:
        fn()
        refresh()
        print(f'  [{name} OK]')
    except AssertionError as exc:
        refresh()
        print(f'  [{name} REFUSED: {exc}]')

def sec_d5rip():
    rip_seg('ULPI_D5', 78.44, 14.75, 79.50, 14.75)
    rip_seg('ULPI_D5', 79.69, 14.75, 78.44, 14.75)
section('0 D5 stub rips', sec_d5rip)

def sec_d4():
    add_track('ULPI_D4', 78.69, 14.25, 79.45, 14.32)
    add_track('ULPI_D4', 79.45, 14.32, 79.35, 15.05)
    add_track('ULPI_D4', 79.35, 15.05, 80.12, 15.38)
section('1 D4 hand route', sec_d4)

def sec_d2():
    add_track('ULPI_D2', 79.05, 13.25, 79.05, 6.60)
    add_via('ULPI_D2', 79.05, 6.60)
    add_track('ULPI_D2', 79.05, 6.60, 78.40, 5.20,
              layer=pcbnew.In2_Cu)
    refresh()
    add_via('ULPI_D2', 78.40, 5.20)
    add_track('ULPI_D2', 78.40, 5.20, 78.25, 5.42)
section('2 D2 hand route', sec_d2)

board.Save(OUT)
board = pcbnew.LoadBoard(OUT)
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(OUT)
print(f'saved {OUT}')

#!/usr/bin/env python3
"""Escape batch 22 -- ULPI residue hand routes, second aim.
- D4: flat run shortened to (79.15,14.30) (CDR_DATP via at
  (79.62,13.88) fences the longer run), then SE into its via.
- D2: north run shifted east to x=79.25 (U7.23 D1 pad fences
  x=79.05), via (79.25,6.6), In2 under D0's F track, via up
  (78.4,5.2), F into the U6 stub.
- D3: F haul NE from U7 stub end (78.90,13.75) east of D2's
  run, across the open mid-band to the U6 stub end (88.3,4.66).
- STP: F haul W then N from U7 stub end (76.25,17.15) to the
  U6 west-edge stub end (69.9,-2.25).
Board-agnostic: xvfb-run -a python3 hw/escapes22.py <src> <out>
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

def section(name, fn):
    print(f'--- {name} ---')
    try:
        fn()
        refresh()
        print(f'  [{name} OK]')
    except AssertionError as exc:
        refresh()
        print(f'  [{name} REFUSED: {exc}]')

def sec_d4():
    add_track('ULPI_D4', 78.69, 14.25, 79.15, 14.30)
    add_track('ULPI_D4', 79.15, 14.30, 79.30, 15.02)
    add_track('ULPI_D4', 79.30, 15.02, 80.12, 15.38)
section('1 D4 route', sec_d4)

def sec_d2():
    add_track('ULPI_D2', 79.05, 13.25, 79.25, 12.90)
    add_track('ULPI_D2', 79.25, 12.90, 79.25, 6.60)
    add_via('ULPI_D2', 79.25, 6.60)
    add_track('ULPI_D2', 79.25, 6.60, 78.40, 5.20,
              layer=pcbnew.In2_Cu)
    refresh()
    add_via('ULPI_D2', 78.40, 5.20)
    add_track('ULPI_D2', 78.40, 5.20, 78.25, 5.42)
section('2 D2 route', sec_d2)

def sec_d3():
    add_track('ULPI_D3', 78.90, 13.75, 80.60, 12.60)
    add_track('ULPI_D3', 80.60, 12.60, 84.00, 6.50)
    add_track('ULPI_D3', 84.00, 6.50, 88.30, 5.20)
    add_track('ULPI_D3', 88.30, 5.20, 88.30, 4.66)
section('3 D3 route', sec_d3)

def sec_stp():
    add_track('ULPI_STP', 76.25, 17.15, 72.00, 17.60)
    add_track('ULPI_STP', 72.00, 17.60, 70.50, 10.00)
    add_track('ULPI_STP', 70.50, 10.00, 69.90, 2.00)
    add_track('ULPI_STP', 69.90, 2.00, 69.90, -2.25)
section('4 STP route', sec_stp)

board.Save(OUT)
board = pcbnew.LoadBoard(OUT)
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(OUT)
print(f'saved {OUT}')

#!/usr/bin/env python3
"""Escape batch 23 -- ULPI residue hand routes, third aim
(per-segment attempts; a route stops at its first refused
segment, placed segments stay).
- D4: south leg threaded at x=79.22 between D5's pad corner
  exclusion and D6's diagonal, then east into its via.
- D2: via at (79.20,13.45) west of D1's staircase, In2 north
  at x=79.25, via up north of D0's F track, In2 west, via up,
  stub into U6's stub end.
- D3: NE haul detouring north of the CDR_DATN via (80.62,12.12).
- STP: via at (72.6,17.5), In2 north under CAP_CLK's F track
  (x=71.88), via up at (69.9,0.5), F into the U6 stub end.
Board-agnostic: xvfb-run -a python3 hw/escapes23.py <src> <out>
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

def try_track(net, x1, y1, x2, y2, w=0.2, layer=pcbnew.F_Cu):
    bad = seg_blocked(net, x1, y1, x2, y2, w, layer)
    if bad:
        print(f'  {net}: ({x1:.2f},{y1:.2f})->({x2:.2f},{y2:.2f}) '
              f'REFUSED: {bad}')
        return False
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MMf(x1), MMf(y1)))
    t.SetEnd(pcbnew.VECTOR2I(MMf(x2), MMf(y2)))
    t.SetWidth(MMf(w))
    t.SetLayer(layer)
    t.SetNet(board.FindNet(net))
    board.Add(t)
    refresh()
    print(f'  {net}: ({x1:.2f},{y1:.2f})->({x2:.2f},{y2:.2f}) '
          f'L{layer} OK')
    return True

def try_via(net, x, y):
    bad = disc_blocked(net, x, y)
    if bad:
        print(f'  {net}: via ({x:.2f},{y:.2f}) REFUSED: {bad}')
        return False
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(MMf(x), MMf(y)))
    v.SetWidth(MMf(0.6))
    v.SetDrill(MMf(0.3))
    v.SetNet(board.FindNet(net))
    board.Add(v)
    refresh()
    print(f'  {net}: via ({x:.2f},{y:.2f}) OK')
    return True

def route(name, steps):
    print(f'--- {name} ---')
    for st in steps:
        if st[0] == 'T':
            ok = try_track(st[1], *st[2])
        else:
            ok = try_via(st[1], *st[2])
        if not ok:
            print(f'  [{name} STOPPED]')
            return
    print(f'  [{name} COMPLETE]')

F = pcbnew.F_Cu
I2 = pcbnew.In2_Cu

route('D4', [
    ('T', 'ULPI_D4', (79.15, 14.30, 79.22, 14.98)),
    ('T', 'ULPI_D4', (79.22, 14.98, 79.60, 15.18)),
    ('T', 'ULPI_D4', (79.60, 15.18, 80.12, 15.38)),
])
route('D2', [
    ('T', 'ULPI_D2', (79.05, 13.25, 79.20, 13.45)),
    ('V', 'ULPI_D2', (79.20, 13.45)),
    ('T', 'ULPI_D2', (79.20, 13.45, 79.25, 6.60, 0.2, I2)),
    ('V', 'ULPI_D2', (79.25, 6.60)),
    ('T', 'ULPI_D2', (79.25, 6.60, 78.40, 5.20, 0.2, I2)),
    ('V', 'ULPI_D2', (78.40, 5.20)),
    ('T', 'ULPI_D2', (78.40, 5.20, 78.25, 5.42)),
])
route('D3', [
    ('T', 'ULPI_D3', (78.90, 13.75, 80.20, 12.90)),
    ('T', 'ULPI_D3', (80.20, 12.90, 81.00, 13.30)),
    ('T', 'ULPI_D3', (81.00, 13.30, 82.20, 11.80)),
    ('T', 'ULPI_D3', (82.20, 11.80, 84.00, 6.50)),
    ('T', 'ULPI_D3', (84.00, 6.50, 88.30, 5.20)),
    ('T', 'ULPI_D3', (88.30, 5.20, 88.30, 4.66)),
])
route('STP', [
    ('T', 'ULPI_STP', (76.25, 17.15, 72.60, 17.50)),
    ('V', 'ULPI_STP', (72.60, 17.50)),
    ('T', 'ULPI_STP', (72.60, 17.50, 70.60, 8.00, 0.2, I2)),
    ('T', 'ULPI_STP', (70.60, 8.00, 69.90, 0.50, 0.2, I2)),
    ('V', 'ULPI_STP', (69.90, 0.50)),
    ('T', 'ULPI_STP', (69.90, 0.50, 69.90, -2.25)),
])

board.Save(OUT)
board = pcbnew.LoadBoard(OUT)
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(OUT)
print(f'saved {OUT}')

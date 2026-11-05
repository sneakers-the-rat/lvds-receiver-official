#!/usr/bin/env python3
"""Escape batch 26 -- ULPI knot rework (choreographed).
Phase A rips (fences only; every ripped net keeps a viable
rejoin and is re-done in this batch or the immediate heal
follow-up):
- ULPI_D1 F staircase x3 (D2 via field) -> D1 pad+stub group
  separated; D1 re-heal is the follow-up's first job.
- ULPI_D5 vertex segment (D4 tail approach).
- ULPI_D6 stub + first diagonal (D5 dive field; D6 re-heal
  in the follow-up).
- ULPI_DIR F chain x2 + via (STP dive field; DIR rejoined
  in phase B below).
Phase B hand routes: D2 (via-hop In2 north), D3 (corridor
between D4 flat run and CDR_DATP via, apex (79.62,14.55)),
D4 tail into its via, STP (via (76.6,17.5), In2 north),
DIR rejoin (F south-west, via (74.9,19.7), B stub into its
staircase end), RST stub.
Board-agnostic: xvfb-run -a python3 hw/escapes26.py <src> <out>
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

def rip_seg(netname, x1, y1, x2, y2, tol=0.1):
    for t in list(board.GetTracks()):
        if t.GetNetname() != netname or t.Type() != pcbnew.PCB_TRACE_T:
            continue
        s, e = t.GetStart(), t.GetEnd()
        d1 = max(abs(MMt(s.x) - x1), abs(MMt(s.y) - y1)) + \
            max(abs(MMt(e.x) - x2), abs(MMt(e.y) - y2))
        d2 = max(abs(MMt(s.x) - x2), abs(MMt(s.y) - y2)) + \
            max(abs(MMt(e.x) - x1), abs(MMt(e.y) - y1))
        if min(d1, d2) <= tol:
            board.Remove(t)
            print(f'  ripped {netname} ({x1:.2f},{y1:.2f})->'
                  f'({x2:.2f},{y2:.2f})')
            refresh()
            return True
    print(f'  rip MISS {netname} ({x1:.2f},{y1:.2f})->({x2:.2f},{y2:.2f})')
    return False

def rip_via(netname, x, y, tol=0.1):
    for t in list(board.GetTracks()):
        if t.GetNetname() != netname or t.Type() != pcbnew.PCB_VIA_T:
            continue
        p = t.GetPosition()
        if abs(MMt(p.x) - x) <= tol and abs(MMt(p.y) - y) <= tol:
            board.Remove(t)
            print(f'  ripped via {netname} ({x:.2f},{y:.2f})')
            refresh()
            return True
    print(f'  rip-via MISS {netname} ({x:.2f},{y:.2f})')
    return False

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
B = pcbnew.B_Cu
I2 = pcbnew.In2_Cu

print('--- phase A rips ---')
rip_seg('ULPI_D1', 79.62, 12.88, 79.88, 13.12)
rip_seg('ULPI_D1', 79.88, 13.12, 80.12, 13.38)
rip_seg('ULPI_D1', 80.12, 13.38, 80.38, 13.62)
rip_seg('ULPI_D5', 79.69, 14.75, 80.38, 14.62)
rip_seg('ULPI_D6', 78.44, 15.25, 78.69, 15.25)
rip_seg('ULPI_D6', 78.69, 15.25, 79.12, 15.38)
rip_seg('ULPI_DIR', 75.88, 17.62, 76.12, 17.88)
rip_seg('ULPI_DIR', 76.12, 17.88, 76.38, 18.12)
rip_via('ULPI_DIR', 76.38, 18.12)

route('D2', [
    ('T', 'ULPI_D2', (79.05, 13.25, 79.55, 12.72)),
    ('V', 'ULPI_D2', (79.55, 12.72)),
    ('T', 'ULPI_D2', (79.55, 12.72, 79.25, 6.60, 0.2, I2)),
    ('V', 'ULPI_D2', (79.25, 6.60)),
    ('T', 'ULPI_D2', (79.25, 6.60, 78.40, 5.20, 0.2, I2)),
    ('V', 'ULPI_D2', (78.40, 5.20)),
    ('T', 'ULPI_D2', (78.40, 5.20, 78.25, 5.42)),
])
route('D3', [
    ('T', 'ULPI_D3', (78.90, 13.75, 79.15, 14.05)),
    ('T', 'ULPI_D3', (79.15, 14.05, 79.62, 14.55)),
    ('T', 'ULPI_D3', (79.62, 14.55, 80.60, 13.60)),
    ('T', 'ULPI_D3', (80.60, 13.60, 82.20, 11.80)),
    ('T', 'ULPI_D3', (82.20, 11.80, 84.00, 6.50)),
    ('T', 'ULPI_D3', (84.00, 6.50, 88.30, 5.20)),
    ('T', 'ULPI_D3', (88.30, 5.20, 88.30, 4.66)),
])
route('D4', [
    ('T', 'ULPI_D4', (79.22, 14.98, 79.55, 15.05)),
    ('T', 'ULPI_D4', (79.55, 15.05, 80.12, 15.38)),
])
route('STP', [
    ('T', 'ULPI_STP', (76.25, 17.15, 76.60, 17.50)),
    ('V', 'ULPI_STP', (76.60, 17.50)),
    ('T', 'ULPI_STP', (76.60, 17.50, 70.60, 8.00, 0.2, I2)),
    ('T', 'ULPI_STP', (70.60, 8.00, 69.90, 0.50, 0.2, I2)),
    ('V', 'ULPI_STP', (69.90, 0.50)),
    ('T', 'ULPI_STP', (69.90, 0.50, 69.90, -2.25)),
])
route('DIR-rejoin', [
    ('T', 'ULPI_DIR', (75.88, 17.62, 75.20, 18.80)),
    ('T', 'ULPI_DIR', (75.20, 18.80, 74.90, 19.70)),
    ('V', 'ULPI_DIR', (74.90, 19.70)),
    ('T', 'ULPI_DIR', (74.90, 19.70, 75.38, 19.12, 0.2, B)),
])
route('RST-stub', [
    ('T', 'USB_RST', (74.25, 16.44, 74.25, 17.15)),
])

board.Save(OUT)
board = pcbnew.LoadBoard(OUT)
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(OUT)
print(f'saved {OUT}')

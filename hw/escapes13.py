#!/usr/bin/env python3
"""Escape + join surgery batch 13 -- repairs + HV_RAW F route.
- Re-place the 5 APD_K In2 staircase segments batch 12's
  rip_touching removed collaterally (exact coordinates from
  the batch-12 rip log).
- HV_RAW: continue on F from the fan stub end (42.90,-4.70)
  west at y~-4.55 (1.05 clear of the APD_K F track end), via
  (40.6,-4.6), In2 hop, via up (39.9,-5.6), F into the island.
- Restore HV_FBX's dive via at (10.12,-15.38) (batch 12 ripped
  it for a re-site that HV_VC's web refuses; original dive is
  the only legal one -- HV_SS's seal at U10 is a separate,
  placement-level problem).
Board-agnostic: xvfb-run -a python3 hw/escapes13.py <src> <out>
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

# 1. APD_K staircase repair (exact batch-12 rip coordinates).
def sec_stair():
    chain = [((40.88, -3.12), (40.62, -2.88)),
             ((40.62, -2.88), (40.38, -2.62)),
             ((40.38, -2.62), (40.12, -2.38)),
             ((40.12, -2.38), (39.88, -2.12)),
             ((39.88, -2.12), (39.62, -1.88))]
    for (a, b) in chain:
        add_track('APD_K', a[0], a[1], b[0], b[1], w=0.4,
                  layer=pcbnew.In2_Cu)
section('1 APD_K staircase repair', sec_stair)

# 2. HV_RAW F continuation + In2 hop into the island.
def sec_raw():
    add_track('HV_RAW', 42.90, -4.70, 41.6, -4.55, w=0.4)
    add_track('HV_RAW', 41.6, -4.55, 40.6, -4.6, w=0.4)
    add_via('HV_RAW', 40.6, -4.6)
    add_track('HV_RAW', 40.6, -4.6, 39.9, -5.6, w=0.4,
              layer=pcbnew.In2_Cu)
    refresh()
    add_via('HV_RAW', 39.9, -5.6)
    add_track('HV_RAW', 39.9, -5.6, 39.3, -7.5, w=0.4)
    add_track('HV_RAW', 39.3, -7.5, 39.53, -9.8, w=0.4)
section('2 HV_RAW F + In2', sec_raw)

# 3. Restore HV_FBX dive via.
def sec_fbx_via():
    add_via('HV_FBX', 10.12, -15.38)
section('3 HV_FBX via restore', sec_fbx_via)

board.Save(OUT)
board = pcbnew.LoadBoard(OUT)
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(OUT)
print(f'saved {OUT}')

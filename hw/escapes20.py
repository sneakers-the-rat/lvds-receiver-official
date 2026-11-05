#!/usr/bin/env python3
"""Escape batch 20 -- ULPI fanout round 2: residue-first.
Round 1's landed routes fence the residue pads (D7's F track
at y=17.38 seals STP/CK south exits; D4's diagonal seals D5's
east exit; NXT's F track seals RST). Rip the fence segments
(D7/D4/NXT split and re-heal AFTER the residue), stub the
seven sealed U7 pads, then heal round 2 connects stub-first.
Board-agnostic: xvfb-run -a python3 hw/escapes20.py <src> <out>
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
    print(f'  {net}: ({x1:.2f},{y1:.2f})->({x2:.2f},{y2:.2f})')

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

def rip_via(net, x, y):
    for t in list(board.GetTracks()):
        if t.Type() != pcbnew.PCB_VIA_T or t.GetNetname() != net:
            continue
        if (abs(MMt(t.GetPosition().x) - x) < 0.3
                and abs(MMt(t.GetPosition().y) - y) < 0.3):
            board.Remove(t)
            print(f'  rip via {net} @({x},{y})')
            return
    print(f'  rip via {net} @({x},{y}): NOT FOUND')

def section(name, fn):
    print(f'--- {name} ---')
    try:
        fn()
        refresh()
        print(f'  [{name} OK]')
    except AssertionError as exc:
        refresh()
        print(f'  [{name} REFUSED: {exc}]')

def sec_rips():
    rip_seg('ULPI_NXT', 74.12, 17.38, 73.88, 17.12)
section('0 NXT diagonal rip', sec_rips)

def stub_from(x, y, net, tx, ty):
    def fn():
        add_track(net, x, y, tx, ty)
    return fn

section('1 D2 U6 stub', stub_from(78.25, 4.66, 'ULPI_D2', 78.25, 5.42))
section('2 D3 U6 stub', stub_from(89.25, 4.66, 'ULPI_D3', 88.30, 4.66))
section('3 STP U6 stub', stub_from(71.34, -2.25, 'ULPI_STP', 69.90, -2.25))
section('4 D4 stub ext', stub_from(78.69, 14.25, 'ULPI_D4', 79.30, 14.45))
section('5 RST stub', stub_from(74.25, 16.44, 'USB_RST', 74.25, 17.30))

board.Save(OUT)
board = pcbnew.LoadBoard(OUT)
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(OUT)
print(f'saved {OUT}')

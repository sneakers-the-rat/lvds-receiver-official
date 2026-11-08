#!/usr/bin/env python3
"""t_ah6_phya_build.py -- hand-laid PHY_1V8A connection, fully gated.

Route (designed against the rip2 exact item model; see session notes):
  F stub U7.29 (75.75,11.5625) -> (75.75,11.0) -> via V1 (75.875,10.6875)
    [the via lens between C16.1's NE corner, XI's SW corner and U7.30's
     SE corner: exact-model margins ~+0.001..+0.004]
  In2 west at y10.6875, SW parallel to XO's staircase at ~0.5 offset,
    west at y~9.3 to x64.6, north at x64.6 to y17.1, east to x70.1,
    south to via V2 (70.05,14.35) inside the C23 pocket
    [B-gate vs +3V3D B vertical x70.875: +0.025]
  F stub V2 -> C23.1 pad (69.975,14.75).
Every segment and via is gated against the exact item model BEFORE
anything is added (all-or-nothing). After saving, the board is reloaded
and the PHY_1V8A item census is diffed against expectation (contact
rename check). Usage: t_ah6_phya_build.py IN OUT [--build]
Without --build it only reports gate margins.
"""
import math, sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import repair
from router import netclass, dist_to_item

SRC, OUT = sys.argv[1], sys.argv[2]
BUILD = '--build' in sys.argv
NET = 'PHY_1V8A'
F, IN2, B = pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu
LAY = {F: 0, IN2: 1, B: 2}
W = 0.20

V1 = (75.875, 10.6875)
V2 = (70.05, 14.35)
F_SEGS = [((75.75, 11.5625), (75.75, 11.0)),
          ((75.75, 11.0), V1),
          (V2, (69.975, 14.75))]
IN2_PTS = [V1, (73.6, 10.6875), (72.9, 10.9), (72.52, 10.52),
           (72.27, 10.02), (72.02, 9.77), (71.77, 9.52),
           (64.6, 9.3), (64.6, 17.1), (70.1, 17.1), (70.1, 15.0),
           V2]
IN2_SEGS = list(zip(IN2_PTS, IN2_PTS[1:]))

board = pcbnew.LoadBoard(SRC)
items, _ = repair.build_items(board)

def pair_clr(other):
    return max(netclass(NET)[1], netclass(other)[1] if other else 0.2)

def gate_pt(li, x, y, rad):
    """worst margin of a point (radius rad) on layer li vs foreign items"""
    worst = (1e9, None)
    for it in items[li].near(li, x, y):
        if it[1] == NET:
            continue
        m = dist_to_item(it, x, y) - (rad + pair_clr(it[1]))
        if m < worst[0]:
            worst = (m, it)
    return worst

def gate_seg(li, a, c):
    worst = (1e9, None, None)
    n = max(2, int(math.hypot(c[0] - a[0], c[1] - a[1]) / 0.05) + 1)
    for s in range(n + 1):
        x = a[0] + (c[0] - a[0]) * s / n
        y = a[1] + (c[1] - a[1]) * s / n
        m, it = gate_pt(li, x, y, W / 2)
        if m < worst[0]:
            worst = (m, it, (round(x, 3), round(y, 3)))
    return worst

ok = True
for a, c in F_SEGS:
    m, it, at = gate_seg(0, a, c)
    print(f'F seg {a}->{c}: margin {m:+.3f} vs {it[1] if it else None} '
          f'{tuple(round(v,3) for v in it[2]) if it else None} at {at}')
    ok &= m >= 0
for a, c in IN2_SEGS:
    m, it, at = gate_seg(1, a, c)
    print(f'In2 seg {a}->{c}: margin {m:+.3f} vs {it[1] if it else None} '
          f'{tuple(round(v,3) for v in it[2]) if it else None} at {at}')
    ok &= m >= 0
for nm, v in (('V1', V1), ('V2', V2)):
    for li in range(3):
        m, it = gate_pt(li, v[0], v[1], 0.25)
        print(f'{nm} {v} layer{li}: margin {m:+.3f} vs '
              f'{it[1] if it else None} '
              f'{tuple(round(x,3) for x in it[2]) if it else None}')
        ok &= m >= 0
print('ALL GATES PASS' if ok else 'GATE FAILURE -- nothing built')
if not (ok and BUILD):
    sys.exit(0 if ok else 1)

code = board.GetNetcodeFromNetname(NET)
assert code >= 0

def add_seg(a, c, layer):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(a[0]), pcbnew.FromMM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(c[0]), pcbnew.FromMM(c[1])))
    t.SetWidth(pcbnew.FromMM(W))
    t.SetLayer(layer)
    t.SetNetCode(code)
    board.Add(t)

def add_via(p):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(p[0]),
                                  pcbnew.FromMM(p[1])))
    v.SetWidth(pcbnew.FromMM(0.5))
    v.SetDrill(pcbnew.FromMM(0.25))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(F, B)
    v.SetNetCode(code)
    board.Add(v)

for a, c in F_SEGS:
    add_seg(a, c, F)
for a, c in IN2_SEGS:
    add_seg(a, c, IN2)
add_via(V1)
add_via(V2)
board.Save(OUT)
print('saved', OUT)

# reload census: PHY_1V8A must have exactly the items just added
b2 = pcbnew.LoadBoard(OUT)
nseg = sum(1 for t in b2.GetTracks()
           if t.GetNetname() == NET and t.Type() == pcbnew.PCB_TRACE_T)
nvia = sum(1 for t in b2.GetTracks()
           if t.GetNetname() == NET and t.Type() == pcbnew.PCB_VIA_T)
exp_seg = len(F_SEGS) + len(IN2_SEGS)
print(f'reload census: {NET} segs {nseg} (expect {exp_seg}), '
      f'vias {nvia} (expect 2)')
assert nseg == exp_seg and nvia == 2, 'CENSUS MISMATCH -- save rename?'
print('census OK')

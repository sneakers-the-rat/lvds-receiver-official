#!/usr/bin/env python3
"""Connect SWDIO (U6.105 group -> J4.2 web), with a DBG_TX relay.

The F band east of U6 is a woven fence (DBG_RX/LED_STAT/DBG_TX
escapes), and pass 123's heal laid ULPI_D3's B staircase + a
long B vertical at x=96.12 down the east edge. Route:
1. DBG_TX relay: rip its west jog (93.91,-11.25)->(94.38,-10.88)
   ->(94.88,-10.88); via A (93.95,-10.98) on the escape end;
   In2 (93.95,-10.98)->(94.10,-12.40)->(95.125,-12.40); via2 at
   (95.125,-12.40) on DBG_TX's own north vertical. DBG_TX must
   stay 1 group.
2. SWDIO: B (93.17,-13.04)->(94.30,-13.05) from its own via;
   dive V0 (94.30,-13.05); In2 east (96.30,-13.05), north to
   y=-11.80, west to V1b (95.45,-11.80); dive; B south at
   x=95.45 to (95.45,6.90); dive V2a; In2 south to (95.45,10.40)
   (hopping ULPI_D3's B snake); dive V2b; B south to
   (95.45,54.80); dive V3p; F west to (93.60,54.80); dive V3;
   In2 diagonal onto the J4 web track (93.12,57.90).
All pieces exact-tested in order; SWDIO 2 -> 1, DBG_TX 1 -> 1,
or the board is not saved.

Run: xvfb-run -a python3 hw/fix_swdio.py IN OUT
"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import check_pcb, repair6, repair
from hand_stub import build_items

check_pcb.SURFACE = {pcbnew.F_Cu, pcbnew.B_Cu}
need_for = check_pcb.need_for
MM = pcbnew.FromMM
F, B = pcbnew.F_Cu, pcbnew.B_Cu
IN1, IN2 = pcbnew.In1_Cu, pcbnew.In2_Cu
SAFETY = 0.005
W = 0.20
VD = 0.60

SRC, OUT = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(SRC)
items = build_items(board)
print(f"items: {len(items)}")
ALL = {F, IN1, IN2, B}


def seg_shape(a, b, w):
    return pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])),
                                pcbnew.VECTOR2I(MM(b[0]), MM(b[1])),
                                MM(w))


def blockers(net, layers, shape):
    out = []
    for kind, n2, l2, s2, desc in items:
        if n2 == net or kind == 'zone':
            continue
        shared = layers & l2
        if not shared:
            continue
        need = need_for(net, n2, shared)
        if s2.Collide(shape, MM(need - 0.001 + SAFETY)):
            out.append((n2, desc, need))
    return out


def ngroups(net):
    return len(repair.compute_groups(board)[net])


def add_track(net, a, b, layer):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(MM(b[0]), MM(b[1])))
    t.SetWidth(MM(W))
    t.SetLayer(layer)
    t.SetNet(board.FindNet(net))
    board.Add(t)
    return t


def add_via(net, p):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(MM(p[0]), MM(p[1])))
    v.SetDrill(MM(0.30))
    v.SetWidth(MM(VD))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(F, B)
    v.SetNet(board.FindNet(net))
    board.Add(v)
    return v


def test_seg(net, tag, a, b, layer):
    bl = blockers(net, {layer}, seg_shape(a, b, W))
    print(tag, a, '->', b, 'blockers:', bl[:4] if bl else 'none')
    if bl:
        sys.exit(1)


def test_via(net, tag, p):
    c = pcbnew.SHAPE_CIRCLE(pcbnew.VECTOR2I(MM(p[0]), MM(p[1])),
                            MM(VD / 2))
    bl = blockers(net, ALL, c)
    print(tag, p, 'blockers:', bl[:4] if bl else 'none')
    if bl:
        sys.exit(1)


def rip(net, a, b):
    n = 0
    for t in list(board.GetTracks()):
        if isinstance(t, pcbnew.PCB_VIA) or t.GetNetname() != net:
            continue
        s = (round(pcbnew.ToMM(t.GetStart().x), 2),
             round(pcbnew.ToMM(t.GetStart().y), 2))
        e = (round(pcbnew.ToMM(t.GetEnd().x), 2),
             round(pcbnew.ToMM(t.GetEnd().y), 2))
        if {s, e} == {a, b}:
            board.Remove(t)
            n += 1
    print(f'ripped {net} {a}->{b}: {n}')
    assert n == 1


gs0, gt0 = ngroups('SWDIO'), ngroups('DBG_TX')
print('groups before: SWDIO', gs0, 'DBG_TX', gt0)
assert gs0 == 2 and gt0 == 1

VA = (93.95, -10.98)
VA2 = (95.125, -12.40)
V0 = (93.45, -13.60)
V1B = (95.45, -11.80)
V2A = (95.45, 6.90)
V2B = (95.45, 10.40)
V3P = (95.45, 54.80)
V3 = (93.60, 54.80)

# --- DBG_TX relay tests ---
test_via('DBG_TX', 'viaA', VA)
test_seg('DBG_TX', 'In2 relay 1', VA, (93.80, -11.90), IN2)
test_seg('DBG_TX', 'In2 relay 1b', (93.80, -11.90), (94.10, -12.40),
         IN2)
test_seg('DBG_TX', 'In2 relay 2', (94.10, -12.40), VA2, IN2)
test_via('DBG_TX', 'viaA2', VA2)
# --- SWDIO tests ---
test_seg('SWDIO', 'B entry', (93.17, -13.04), V0, B)
test_via('SWDIO', 'via0', V0)
test_seg('SWDIO', 'In2 east', V0, (96.30, -13.05), IN2)
test_seg('SWDIO', 'In2 north', (96.30, -13.05), (96.30, -11.80),
         IN2)
test_seg('SWDIO', 'In2 west', (96.30, -11.80), V1B, IN2)
test_via('SWDIO', 'via1b', V1B)
test_seg('SWDIO', 'B south 1', V1B, V2A, B)
test_via('SWDIO', 'via2a', V2A)
test_seg('SWDIO', 'In2 hop', V2A, V2B, IN2)
test_via('SWDIO', 'via2b', V2B)
test_seg('SWDIO', 'B south 2', V2B, V3P, B)
test_via('SWDIO', 'via3p', V3P)
test_seg('SWDIO', 'F west', V3P, V3, F)
test_via('SWDIO', 'via3', V3)
test_seg('SWDIO', 'In2 land', V3, (93.12, 57.90), IN2)

# --- apply ---
rip('DBG_TX', (93.91, -11.25), (94.38, -10.88))
rip('DBG_TX', (94.38, -10.88), (94.88, -10.88))
add_via('DBG_TX', VA)
add_track('DBG_TX', VA, (93.80, -11.90), IN2)
add_track('DBG_TX', (93.80, -11.90), (94.10, -12.40), IN2)
add_track('DBG_TX', (94.10, -12.40), VA2, IN2)
add_via('DBG_TX', VA2)

add_track('SWDIO', (93.17, -13.04), V0, B)
add_via('SWDIO', V0)
add_track('SWDIO', V0, (96.30, -13.05), IN2)
add_track('SWDIO', (96.30, -13.05), (96.30, -11.80), IN2)
add_track('SWDIO', (96.30, -11.80), V1B, IN2)
add_via('SWDIO', V1B)
add_track('SWDIO', V1B, V2A, B)
add_via('SWDIO', V2A)
add_track('SWDIO', V2A, V2B, IN2)
add_via('SWDIO', V2B)
add_track('SWDIO', V2B, V3P, B)
add_via('SWDIO', V3P)
add_track('SWDIO', V3P, V3, F)
add_via('SWDIO', V3)
add_track('SWDIO', V3, (93.12, 57.90), IN2)

gs1, gt1 = ngroups('SWDIO'), ngroups('DBG_TX')
print('groups after: SWDIO', gs1, 'DBG_TX', gt1)
assert gs1 == 1 and gt1 == 1, 'join failed'
repair6.save_checkpoint(board, OUT)
print('saved', OUT)

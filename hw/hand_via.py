#!/usr/bin/env python3
"""Via-first escape stubs for pads sealed on F.Cu.

Shape: a short neck from the pad edge to a via, then (when one
clears) a tail segment on In2.Cu. A via alone is already a valid
result — the router starts from the via's buried-layer cells.
All tests are the audit's own (KiCad SHAPE.Collide at the class
clearance via check_pcb.need_for); zone fills excluded (the pour
re-carves at refill; the post-pass audit verifies).

Run: xvfb-run -a python3 hw/hand_via.py IN OUT NET:PAD [NET:PAD...]
"""
import sys, math
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import repair6
import check_pcb
from router import netclass
from hand_stub import build_items

check_pcb.SURFACE = {pcbnew.F_Cu, pcbnew.B_Cu}
need_for = check_pcb.need_for
MM = pcbnew.FromMM
ALL_LAYERS = {pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu}

def ok(items, net, shape, layers, safety):
    for kind, n2, l2, s2, desc in items:
        if n2 == net:
            continue
        shared = layers & l2
        if not shared:
            continue
        need = need_for(net, n2, shared)
        if shape.Collide(s2, MM(need - 0.001 + safety)):
            return False
    return True

def find(items, net, pos, half, width):
    px, py = pos
    hx, hy = half
    fallback = None
    for safety in (0.02, 0.005, 0.0):
        for w in (min(width, 0.25), 0.2):
            for soff in (-0.02, 0.02):
                for dv in (0.55, 0.7, 0.85, 1.0, 1.15):
                    for k in range(16):
                        a = k * math.pi / 8
                        ca, sa = math.cos(a), math.sin(a)
                        ext = hx * abs(ca) + hy * abs(sa)
                        sx = px + (ext + soff) * ca
                        sy = py + (ext + soff) * sa
                        vx, vy = px + dv * ca, py + dv * sa
                        neck = pcbnew.SHAPE_SEGMENT(
                            pcbnew.VECTOR2I(MM(sx), MM(sy)),
                            pcbnew.VECTOR2I(MM(vx), MM(vy)), MM(w))
                        if not ok(items, net, neck, {pcbnew.F_Cu}, safety):
                            continue
                        # via disc as a zero-length segment (a plus
                        # of two segments would poke 0.3 mm past the
                        # disc on the axes — that bug sealed U9.5)
                        via_disc = pcbnew.SHAPE_SEGMENT(
                            pcbnew.VECTOR2I(MM(vx), MM(vy)),
                            pcbnew.VECTOR2I(MM(vx), MM(vy)), MM(0.6))
                        if not ok(items, net, via_disc, ALL_LAYERS,
                                  safety):
                            continue
                        if fallback is None:
                            fallback = (sx, sy, vx, vy, vx, vy, w)
                        for da in (0.0, math.pi / 4, -math.pi / 4,
                                   math.pi / 2, -math.pi / 2):
                            aa = a + da
                            ca2, sa2 = math.cos(aa), math.sin(aa)
                            for tl in (1.0, 1.5, 2.0):
                                ex, ey = vx + tl * ca2, vy + tl * sa2
                                tail = pcbnew.SHAPE_SEGMENT(
                                    pcbnew.VECTOR2I(MM(vx), MM(vy)),
                                    pcbnew.VECTOR2I(MM(ex), MM(ey)), MM(w))
                                if ok(items, net, tail,
                                      {pcbnew.In2_Cu}, safety):
                                    return (sx, sy, vx, vy, ex, ey, w)
    return fallback

def main():
    src, out = sys.argv[1], sys.argv[2]
    targets = [tuple(s.split(':', 1)) for s in sys.argv[3:]]
    board = pcbnew.LoadBoard(src)
    pad_info = {}
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            bb = pad.GetBoundingBox()
            pad_info[f"{fp.GetReference()}.{pad.GetNumber()}"] = (
                pad.GetNetname(), pcbnew.ToMM(pad.GetPosition()),
                (pcbnew.ToMM(bb.GetWidth()) / 2,
                 pcbnew.ToMM(bb.GetHeight()) / 2))
    items = build_items(board)
    placed = 0
    for net, desc in targets:
        n2, pos, half = pad_info[desc]
        assert n2 == net
        width, clr = netclass(net)
        r = find(items, net, pos, half, width)
        if r is None:
            print(f"  {net} {desc}: NO VIA STUB FOUND", flush=True)
            continue
        sx, sy, vx, vy, ex, ey, w = r
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(MM(sx), MM(sy)))
        t.SetEnd(pcbnew.VECTOR2I(MM(vx), MM(vy)))
        t.SetWidth(MM(w))
        t.SetLayer(pcbnew.F_Cu)
        t.SetNet(board.FindNet(net))
        board.Add(t)
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pcbnew.VECTOR2I(MM(vx), MM(vy)))
        v.SetWidth(MM(0.6))
        v.SetDrill(MM(0.3))
        v.SetNet(board.FindNet(net))
        board.Add(v)
        if (ex, ey) != (vx, vy):
            t2 = pcbnew.PCB_TRACK(board)
            t2.SetStart(pcbnew.VECTOR2I(MM(vx), MM(vy)))
            t2.SetEnd(pcbnew.VECTOR2I(MM(ex), MM(ey)))
            t2.SetWidth(MM(w))
            t2.SetLayer(pcbnew.In2_Cu)
            t2.SetNet(board.FindNet(net))
            board.Add(t2)
        items = build_items(board)
        placed += 1
        print(f"  {net} {desc}: via stub via@({vx:.2f},{vy:.2f}) "
              f"tail->({ex:.2f},{ey:.2f}) w={w}", flush=True)
    repair6.save_checkpoint(board, out)
    print(f"hand_via done: {placed}/{len(targets)} placed", flush=True)

if __name__ == "__main__":
    main()

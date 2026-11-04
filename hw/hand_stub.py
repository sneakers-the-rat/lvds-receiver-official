#!/usr/bin/env python3
"""Hand-placed escape stubs for pads the router's fanout model seals.

Root cause (measured, results in WORKING_NOTES Addendum 5): router6
anchors fanout at pad CENTRES; on 0.5 mm-pitch rows a centre-anchored
first segment starts within (halfwidth + clearance) of a sibling pad
or the exposed pad, so every cardinal first move is refused even in a
cleared field ("0-second" failures). The audit (hw/check_pcb.py)
judges exact shapes: a stub drawn from the pad toward open field
passes it easily. This tool searches 16 compass directions for the
shortest stub whose exact shape keeps the class clearance to every
foreign item (KiCad SHAPE.Collide, the audit's own test; zone fills
excluded — the pour re-carves around new copper at refill, which the
post-stub audit then verifies), with an endpoint disc that must also
clear, so the router can take over from the stub's end.

Run: xvfb-run -a python3 hw/hand_stub.py IN OUT NET:PAD [NET:PAD...]
"""
import sys, math
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import repair6
import check_pcb
from router import netclass

check_pcb.SURFACE = {pcbnew.F_Cu, pcbnew.B_Cu}
need_for = check_pcb.need_for

MM = pcbnew.FromMM
SAFETY = 0.02

def build_items(board):
    items = []  # (kind, net, layers:set, shape, desc)
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            net = pad.GetNetname()
            if not net:
                continue
            layers = {l for l in (pcbnew.F_Cu, pcbnew.In1_Cu,
                                  pcbnew.In2_Cu, pcbnew.B_Cu)
                      if pad.IsOnLayer(l)}
            items.append(("pad", net, layers, pad.GetEffectiveShape(),
                          f"{fp.GetReference()}.{pad.GetNumber()}"))
    for t in board.GetTracks():
        net = t.GetNetname()
        if not net:
            continue
        if t.Type() == pcbnew.PCB_VIA_T:
            layers = {pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu,
                      pcbnew.B_Cu}
            kind = "via"
        else:
            layers = {t.GetLayer()}
            kind = "track"
        items.append((kind, net, layers, t.GetEffectiveShape(),
                      f"{kind}@stubcheck"))
    return items

def stub_ok(items, net, shape, layers, safety):
    for kind, n2, l2, s2, desc in items:
        if n2 == net or kind == 'zone':
            continue
        shared = layers & l2
        if not shared:
            continue
        need = need_for(net, n2, shared)
        if shape.Collide(s2, MM(need - 0.001 + safety)):
            return False
    return True

def find_stub(items, net, pad_pos, half, width):
    px, py = pad_pos
    hx, hy = half
    layers = {pcbnew.F_Cu}
    for safety in (SAFETY, 0.005, 0.0):
        for w in (width, 0.25, 0.2):
            for ln in (0.5, 0.65, 0.8, 1.1, 1.4, 1.7, 2.0, 2.4, 2.8, 3.2):
                for k in range(16):
                    a = k * math.pi / 8
                    ca, sa = math.cos(a), math.sin(a)
                    ext = hx * abs(ca) + hy * abs(sa)
                    sx, sy = px + (ext - 0.02) * ca, py + (ext - 0.02) * sa
                    ex, ey = px + (ext + ln) * ca, py + (ext + ln) * sa
                    seg = pcbnew.SHAPE_SEGMENT(
                        pcbnew.VECTOR2I(MM(sx), MM(sy)),
                        pcbnew.VECTOR2I(MM(ex), MM(ey)), MM(w))
                    if not stub_ok(items, net, seg, layers, safety):
                        continue
                    # endpoint openness: one 0.5 mm neck-width step
                    # out of the endpoint (straight or +-45 degrees)
                    open_ = False
                    for da in (0.0, math.pi / 4, -math.pi / 4):
                        aa = a + da
                        ca2, sa2 = math.cos(aa), math.sin(aa)
                        ext_seg = pcbnew.SHAPE_SEGMENT(
                            pcbnew.VECTOR2I(MM(ex), MM(ey)),
                            pcbnew.VECTOR2I(MM(ex + 0.5 * ca2),
                                            MM(ey + 0.5 * sa2)), MM(0.2))
                        if stub_ok(items, net, ext_seg, layers, safety):
                            open_ = True
                            break
                    if open_:
                        return (sx, sy, ex, ey, w)
    return None

def main():
    src, out = sys.argv[1], sys.argv[2]
    targets = []
    for spec in sys.argv[3:]:
        net, desc = spec.split(':', 1)
        targets.append((net, desc))
    board = pcbnew.LoadBoard(src)
    pad_pos = {}
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            bb = pad.GetBoundingBox()
            half = (pcbnew.ToMM(bb.GetWidth()) / 2,
                    pcbnew.ToMM(bb.GetHeight()) / 2)
            pad_pos[f"{fp.GetReference()}.{pad.GetNumber()}"] = (
                pad.GetNetname(), pcbnew.ToMM(pad.GetPosition()), half)
    items = build_items(board)
    placed = 0
    for net, desc in targets:
        n2, pos, half = pad_pos[desc]
        assert n2 == net, f"{desc} is {n2}, not {net}"
        width, clr = netclass(net)
        r = find_stub(items, net, pos, half, width)
        if r is None:
            print(f"  {net} {desc}: NO STUB FOUND", flush=True)
            continue
        x1, y1, x2, y2, w = r
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(MM(x1), MM(y1)))
        t.SetEnd(pcbnew.VECTOR2I(MM(x2), MM(y2)))
        t.SetWidth(MM(w))
        t.SetLayer(pcbnew.F_Cu)
        t.SetNet(board.FindNet(net))
        board.Add(t)
        items = build_items(board)
        placed += 1
        print(f"  {net} {desc}: stub ({x1:.2f},{y1:.2f})->"
              f"({x2:.2f},{y2:.2f}) w={w}", flush=True)
    repair6.save_checkpoint(board, out)
    print(f"hand_stub done: {placed}/{len(targets)} stubs placed",
          flush=True)

if __name__ == "__main__":
    main()

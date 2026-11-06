#!/usr/bin/env python3
"""Place one stitch via ON a named net's lone track segment (the
segment is identified by its GetPosition), sampling along the
segment until the via disc clears every foreign item on all layers
(hand_via's own test). The via drops the track to the buried GND
plane (In1), which the F/B notch rule areas do not carve.

Run: xvfb-run -a python3 hw/stitch_track.py IN OUT NET X Y
"""
import sys, math
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import repair6
import check_pcb
from hand_stub import build_items
from hand_via import ok, ALL_LAYERS

check_pcb.SURFACE = {pcbnew.F_Cu, pcbnew.B_Cu}
MM = pcbnew.FromMM
TM = pcbnew.ToMM

def main():
    src, out, net = sys.argv[1], sys.argv[2], sys.argv[3]
    gx, gy = float(sys.argv[4]), float(sys.argv[5])
    board = pcbnew.LoadBoard(src)
    seg = None
    for t in board.GetTracks():
        if t.GetNetname() != net or isinstance(t, pcbnew.PCB_VIA):
            continue
        p = t.GetPosition()
        if abs(TM(p.x) - gx) < 0.01 and abs(TM(p.y) - gy) < 0.01:
            seg = t; break
    assert seg is not None, "segment not found"
    a = (TM(seg.GetStart().x), TM(seg.GetStart().y))
    b = (TM(seg.GetEnd().x), TM(seg.GetEnd().y))
    print(f"segment {a} -> {b} layer {seg.GetLayer()}")
    items = build_items(board)
    n = 40
    for i in range(n + 1):
        f = i / n
        x = a[0] + (b[0] - a[0]) * f
        y = a[1] + (b[1] - a[1]) * f
        disc = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(x), MM(y)),
                                    pcbnew.VECTOR2I(MM(x), MM(y)), MM(0.6))
        if ok(items, net, disc, ALL_LAYERS, 0.0):
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
            v.SetWidth(MM(0.6)); v.SetDrill(MM(0.3))
            v.SetNet(board.FindNet(net))
            board.Add(v)
            print(f"via placed at ({x:.3f},{y:.3f}) f={f:.2f}")
            repair6.save_checkpoint(board, out)
            print('saved', out)
            return
    print("NO CLEAR VIA POSITION ON SEGMENT")

if __name__ == "__main__":
    main()

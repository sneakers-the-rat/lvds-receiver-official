#!/usr/bin/env python3
"""Carve the F.Cu/B.Cu GND pours back from HV copper in the strip.

Same mechanism as hw/notch.py (copper-pour keepout RULE AREAS +
refill), for the pass-65 expansion strip. Extending the GND pours
into the strip (hw/refill_strip.py) let the F.Cu pour approach the
moved U10 cluster's HV pads at the pour's own 0.25 mm clearance,
while the audit's surface creepage rule (check_pcb.HV_NETS =
{APD_K, HV_RAW, HV_SEC}) needs 1.0 mm — 8 new violations.

Rects are not hand-drawn here: they are computed from the actual
extents of every HV-net pad/track/via whose copper reaches the
strip side (centre y < 5 mm), each expanded by 1.35 mm (so the
refilled pour keeps >= 1.0 mm from the copper, as in notch.py's
>=1.3 expansion), then merged where they overlap.

Run: xvfb-run -a python3 hw/notch_strip.py [IN] [OUT]
     (defaults: hw/pdlvds_rx.expanded.kicad_pcb, in place)
"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import repair6
import check_pcb

MM = pcbnew.FromMM
TM = pcbnew.ToMM
EXPAND = 1.35
STRIP_Y = 5.0   # collect HV copper centred north of this line

def merge(rects):
    """Merge overlapping (or touching after expansion) rects."""
    rects = list(rects)
    changed = True
    while changed:
        changed = False
        for i in range(len(rects)):
            for j in range(i + 1, len(rects)):
                a, b = rects[i], rects[j]
                if a[0] <= b[2] and b[0] <= a[2] and \
                   a[1] <= b[3] and b[1] <= a[3]:
                    rects[i] = (min(a[0], b[0]), min(a[1], b[1]),
                                max(a[2], b[2]), max(a[3], b[3]))
                    del rects[j]
                    changed = True
                    break
            if changed:
                break
    return rects

def main():
    src = sys.argv[1] if len(sys.argv) > 1 else 'hw/pdlvds_rx.expanded.kicad_pcb'
    out = sys.argv[2] if len(sys.argv) > 2 else src
    board = pcbnew.LoadBoard(src)
    rects = []
    def take(bb):
        x0, y0 = TM(bb.GetX()), TM(bb.GetY())
        x1, y1 = TM(bb.GetRight()), TM(bb.GetBottom())
        if (y0 + y1) / 2 < STRIP_Y:
            rects.append((x0 - EXPAND, y0 - EXPAND, x1 + EXPAND, y1 + EXPAND))
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname() in check_pcb.HV_NETS:
                take(pad.GetBoundingBox())
    for t in board.GetTracks():
        if t.GetNetname() in check_pcb.HV_NETS:
            take(t.GetBoundingBox())
    rects = merge(rects)
    print(f"HV strip rects ({len(rects)}):")
    for r in rects:
        print(f"  ({r[0]:.2f},{r[1]:.2f})-({r[2]:.2f},{r[3]:.2f})")
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        for (x0, y0, x1, y1) in rects:
            z = pcbnew.ZONE(board)
            z.SetIsRuleArea(True)
            z.SetDoNotAllowCopperPour(True)
            z.SetLayer(layer)
            o = z.Outline()
            o.NewOutline()
            for (x, y) in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
                o.Append(pcbnew.VECTOR2I(MM(x), MM(y)))
            board.Add(z)
    repair6.save_checkpoint(board, out)
    print('notch_strip saved', out, flush=True)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Carve the F.Cu/B.Cu GND pours back from the HV (APD_K) copper.

The audit's HV surface rule needs 1.0 mm between APD_K and the
ground pours; the pours' own fill clearance only holds ~0.5 mm.
Rather than move the pour outlines by hand, add RULE AREAS
(copper-pour keepout only — tracks/vias/pads unaffected) drawn as
the APD_K copper's extents expanded by >1.0 mm, then refill.

Rects: A = northern APD_K cluster (pads/tracks x 5.2..13.0,
y 24.1..31.0), B = D1.5's escape neck+via (x 9.5..11.1,
y 36.3..40.3), C = RJ2.2 pad. Each expanded by >=1.3 mm so the
pour's remaining clearance to the copper is >=1.0 mm.

Run: xvfb-run -a python3 hw/notch.py IN OUT
"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import repair6

RECTS = [
    (3.5, 22.0, 14.8, 33.0),    # A: northern APD_K cluster (R30.1 is
                                #    a 1.12x1.75 pad at (13.04,31.0);
                                #    its 1.0 mm expansion reaches
                                #    x 14.60, y 32.88)
    (8.4, 35.3, 12.3, 41.2),    # B: D1.5 escape neck + via
    (12.1, 55.3, 15.5, 58.7),   # C: RJ2.2
]
MM = pcbnew.FromMM

def main():
    src, out = sys.argv[1], sys.argv[2]
    board = pcbnew.LoadBoard(src)
    # The In1 GND plane's antipads are carved at the zone clearance
    # (0.25); the buried-layer HV rule needs 0.3 around the APD_K
    # via. Raise the plane's clearance to 0.35 and refill.
    for z in board.Zones():
        if z.GetNetname() == 'GND' and z.GetLayer() == pcbnew.In1_Cu:
            z.SetLocalClearance(MM(0.35))
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        for (x0, y0, x1, y1) in RECTS:
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
    print('notch saved', out, flush=True)

if __name__ == "__main__":
    main()

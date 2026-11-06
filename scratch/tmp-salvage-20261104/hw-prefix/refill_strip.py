#!/usr/bin/env python3
"""Extend the GND zone outlines into the expansion strip and refill.

Pass 65 enlarged the outline 100x80 -> 100x110 mm (+30 mm north,
y -30..0 in file coords) and moved the U7/U4/U9/U10 clusters into the
strip, but the three GND zone outlines (F.Cu / In1.Cu / B.Cu) still
span only the old field (y 0.3..79.7), so the moved parts' GND pads
sit over bare strip: GND read 51 groups at pass 65.

This script moves the north edge of each GND zone rectangle from
y=0.3 to y=-29.7 (same 0.3 mm board-edge inset as the other three
sides) and saves through repair6.save_checkpoint, which refills all
zones on a reload cycle — the toolchain's normal checkpoint save.

No tracks, vias, pads or footprints are touched.

Run: xvfb-run -a python3 hw/refill_strip.py [IN] [OUT]
     (defaults: hw/pdlvds_rx.expanded.kicad_pcb, in place)
"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import repair6

MM = pcbnew.FromMM
OLD_NORTH = 0.3     # mm, current north edge of the GND rectangles
NEW_NORTH = -29.7   # mm, 0.3 inside the new edge (edge cuts at -30.025)

def main():
    src = sys.argv[1] if len(sys.argv) > 1 else 'hw/pdlvds_rx.expanded.kicad_pcb'
    out = sys.argv[2] if len(sys.argv) > 2 else src
    board = pcbnew.LoadBoard(src)
    moved = 0
    for z in board.Zones():
        if z.GetNetname() != 'GND':
            continue
        o = z.Outline()
        ch = o.Outline(0)
        layer = pcbnew.LayerName(z.GetFirstLayer())
        for i in range(ch.PointCount()):
            p = ch.CPoint(i)
            x, y = pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)
            if abs(y - OLD_NORTH) < 0.01:
                ch.SetPoint(i, pcbnew.VECTOR2I(p.x, MM(NEW_NORTH)))
                moved += 1
                print(f"  {layer}: point ({x:.2f},{y:.2f}) -> y={NEW_NORTH}")
        z.SetOutline(o)
    print(f"extended {moved} outline points across GND zones")
    assert moved == 6, f"expected 6 north points (3 zones x 2), got {moved}"
    repair6.save_checkpoint(board, out)
    print(f"saved {out} (zones refilled)")

if __name__ == "__main__":
    main()

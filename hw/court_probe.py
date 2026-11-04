#!/usr/bin/env python3
"""Probe: courtyard bbox + centre for refs on a board.
Usage: xvfb-run -a python3 hw/court_probe.py <board> REF [REF ...]"""
import sys
import pcbnew


def mm(v):
    return pcbnew.ToMM(v)


def main():
    b = pcbnew.LoadBoard(sys.argv[1])
    fps = {fp.GetReference(): fp for fp in b.GetFootprints()}
    for ref in sys.argv[2:]:
        fp = fps[ref]
        layer = pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd
        poly = fp.GetCourtyard(layer)
        p = fp.GetPosition()
        if poly is None or poly.OutlineCount() == 0:
            print("%-5s centre=(%6.2f,%6.2f) NO COURTYARD (fp bbox x %.2f..%.2f y %.2f..%.2f)"
                  % (ref, mm(p.x), mm(p.y),
                     mm(fp.GetBoundingBox().GetLeft()),
                     mm(fp.GetBoundingBox().GetRight()),
                     mm(fp.GetBoundingBox().GetTop()),
                     mm(fp.GetBoundingBox().GetBottom())))
        else:
            bb = poly.BBox()
            print("%-5s centre=(%6.2f,%6.2f) crt x %6.2f..%6.2f y %6.2f..%6.2f"
                  % (ref, mm(p.x), mm(p.y), mm(bb.GetLeft()),
                     mm(bb.GetRight()), mm(bb.GetTop()), mm(bb.GetBottom())))


if __name__ == "__main__":
    main()

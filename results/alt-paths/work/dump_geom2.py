#!/usr/bin/env python3
"""Full placement geometry dump: every footprint (ref, pos, rot, side,
bbox, courtyard bbox) and every pad (number, net, abs pos, size).
Usage: dump_geom2.py <board> <out.txt>   (one board per process)"""
import sys
import pcbnew


def mm(v):
    return v / 1e6


def main():
    b = pcbnew.LoadBoard(sys.argv[1])
    out = open(sys.argv[2], "w")
    bb = b.GetBoardEdgesBoundingBox()
    out.write("edges bbox mm: %.2f %.2f .. %.2f %.2f\n"
              % (mm(bb.GetLeft()), mm(bb.GetTop()), mm(bb.GetRight()), mm(bb.GetBottom())))
    for fp in sorted(b.GetFootprints(), key=lambda f: f.GetReference()):
        ref = fp.GetReference()
        p = fp.GetPosition()
        fb = fp.GetBoundingBox()
        layer = pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd
        crt = fp.GetCourtyard(layer)
        cb = crt.BBox() if crt is not None and crt.OutlineCount() else None
        out.write("FP %s pos=(%.2f,%.2f) rot=%.0f side=%s bbox=(%.2f,%.2f)-(%.2f,%.2f) crt=%s\n"
                  % (ref, mm(p.x), mm(p.y), fp.GetOrientationDegrees(),
                     "B" if fp.IsFlipped() else "F",
                     mm(fb.GetLeft()), mm(fb.GetTop()), mm(fb.GetRight()), mm(fb.GetBottom()),
                     ("(%.2f,%.2f)-(%.2f,%.2f)" % (mm(cb.GetLeft()), mm(cb.GetTop()),
                                                  mm(cb.GetRight()), mm(cb.GetBottom()))) if cb else "none"))
        for pad in fp.Pads():
            pp = pad.GetPosition()
            sz = pad.GetSize()
            out.write("   PAD %s net=%s pos=(%.2f,%.2f) size=(%.2f,%.2f)\n"
                      % (pad.GetNumber(), pad.GetNetname(), mm(pp.x), mm(pp.y),
                         mm(sz.x), mm(sz.y)))
    out.close()
    print("dumped", sys.argv[2])


if __name__ == "__main__":
    main()

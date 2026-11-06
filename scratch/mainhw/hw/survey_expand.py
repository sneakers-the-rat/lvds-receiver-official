#!/usr/bin/env python3
"""Survey for the pass-65 board expansion: outline geometry, cluster
bounding boxes, connector/analog-cluster positions, neighbourhood
membership around the congested clusters (U7, U4, U9, U10).

Usage: xvfb-run -a python3 hw/survey_expand.py <board> <out.txt>
One board per process. Coordinates are pcbnew board mm (x right,
y DOWN on screen: larger y = south edge).
"""
import sys
import pcbnew


def mm(v):
    return pcbnew.ToMM(v)


def main():
    board_path, out_path = sys.argv[1], sys.argv[2]
    b = pcbnew.LoadBoard(board_path)
    lines = []

    # ---- outline: all drawings on Edge.Cuts
    edges = []
    for d in b.GetDrawings():
        if d.GetLayer() != pcbnew.Edge_Cuts:
            continue
        bb = d.GetBoundingBox()
        edges.append((type(d).__name__,
                      mm(bb.GetLeft()), mm(bb.GetTop()),
                      mm(bb.GetRight()), mm(bb.GetBottom())))
    xs0 = min(e[1] for e in edges); ys0 = min(e[2] for e in edges)
    xs1 = max(e[3] for e in edges); ys1 = max(e[4] for e in edges)
    lines.append("EDGE.CUTS segments: %d" % len(edges))
    for e in edges:
        lines.append("  %s (%.2f,%.2f)-(%.2f,%.2f)" % e)
    lines.append("OUTLINE BBOX: x %.2f..%.2f (w %.2f)  y %.2f..%.2f (h %.2f)"
                 % (xs0, xs1, xs1 - xs0, ys0, ys1, ys1 - ys0))

    fps = {fp.GetReference(): fp for fp in b.GetFootprints()}
    lines.append("FOOTPRINTS: %d" % len(fps))

    def describe(ref):
        fp = fps[ref]
        p = fp.GetPosition()
        bb = fp.GetBoundingBox()
        pads = list(fp.Pads())
        px = [mm(pad.GetPosition().x) for pad in pads]
        py = [mm(pad.GetPosition().y) for pad in pads]
        return ("%-6s pos=(%6.2f,%6.2f) rot=%5.1f flip=%s bbox x %6.2f..%6.2f "
                "y %6.2f..%6.2f  pads x %6.2f..%6.2f y %6.2f..%6.2f npads=%d"
                % (ref, mm(p.x), mm(p.y), fp.GetOrientationDegrees(),
                   fp.IsFlipped(), mm(bb.GetLeft()), mm(bb.GetRight()),
                   mm(bb.GetTop()), mm(bb.GetBottom()),
                   min(px), max(px), min(py), max(py), len(pads)))

    for ref in ("J1", "J2", "D1", "U1", "R1"):
        if ref in fps:
            lines.append(describe(ref))
    lines.append("--- congested clusters ---")
    for ref in ("U7", "U4", "U9", "U10"):
        lines.append(describe(ref))

    # neighbourhoods: footprints whose centre is within R mm of cluster centre
    def centre(ref):
        p = fps[ref].GetPosition()
        return mm(p.x), mm(p.y)

    for cref, R in (("U7", 14), ("U4", 12), ("U9", 12), ("U10", 12)):
        cx, cy = centre(cref)
        near = []
        for ref, fp in fps.items():
            if ref == cref:
                continue
            x, y = centre(ref)
            d2 = (x - cx) ** 2 + (y - cy) ** 2
            if d2 <= R * R:
                near.append((d2 ** 0.5, ref, x, y, fp.IsFlipped()))
        near.sort()
        lines.append("NEAR %s (R=%d, centre %.2f,%.2f): %s"
                     % (cref, R, cx, cy,
                        ", ".join("%s@%.1f%s" % (r, d, "B" if f else "")
                                  for d, r, x, y, f in near)))

    # occupancy grid: 5 mm cells over the outline, footprint-centre counts
    lines.append("--- centre-density grid (5 mm cells, x cols, y rows) ---")
    gx0, gy0 = int(xs0 // 5) * 5, int(ys0 // 5) * 5
    cols = int((xs1 - gx0) // 5) + 1
    rows = int((ys1 - gy0) // 5) + 1
    grid = [[0] * cols for _ in range(rows)]
    for ref, fp in fps.items():
        x, y = centre(ref)
        c = min(cols - 1, max(0, int((x - gx0) // 5)))
        r = min(rows - 1, max(0, int((y - gy0) // 5)))
        grid[r][c] += 1
    lines.append("      " + "".join("%4d" % (gx0 + 5 * c) for c in range(cols)))
    for r in range(rows):
        lines.append("%5d " % (gy0 + 5 * r) + "".join("%4d" % v for v in grid[r]))

    # full table sorted by (y, x)
    lines.append("--- all footprints (ref x y w h flip) ---")
    rows = []
    for ref, fp in fps.items():
        bb = fp.GetBoundingBox()
        x, y = centre(ref)
        rows.append((y, x, ref, mm(bb.GetWidth()), mm(bb.GetHeight()),
                     fp.IsFlipped(), fp.GetOrientationDegrees()))
    for y, x, ref, w, h, fl, rot in sorted(rows):
        lines.append("%-6s %6.2f %6.2f  %5.2f x %5.2f  rot=%5.1f %s"
                     % (ref, x, y, w, h, rot, "BOT" if fl else ""))

    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines[:60]))


if __name__ == "__main__":
    main()

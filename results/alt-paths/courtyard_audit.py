#!/usr/bin/env python3
"""Courtyard-collision audit for the photodiode LVDS receiver board.

Metric (state precisely): two footprints COLLIDE when they are on the same
board side (both F.Cu or both B.Cu) and the intersection area of their
courtyard polygons (F.CrtYd for top parts, B.CrtYd for bottom parts) is
> 0.001 mm^2 (polygon-exact, via SHAPE_POLY_SET.BooleanIntersection).
Also reports the bounding-box overlap count (upper bound) for comparison
with the parent's quick measurement.

Usage: courtyard_audit.py <board.kicad_pcb> <out.txt> <log.txt>
One board per process (KiCad 7 SWIG corrupts a second LoadBoard).
Progress: timestamped lines appended to <log.txt>, flushed each line.
"""
import sys, time, datetime
import pcbnew


def log(logf, msg):
    line = "%s %s" % (datetime.datetime.now().isoformat(timespec="seconds"), msg)
    print(line, flush=True)
    with open(logf, "a") as f:
        f.write(line + "\n")


def main():
    board_path, out_path, log_path = sys.argv[1], sys.argv[2], sys.argv[3]
    log(log_path, "courtyard_audit start board=%s" % board_path)
    b = pcbnew.LoadBoard(board_path)
    fps = list(b.GetFootprints())
    log(log_path, "loaded %d footprints" % len(fps))

    entries = []  # (ref, side, crt_layer, poly, bbox)
    nocrt = []
    for fp in fps:
        ref = fp.GetReference()
        side = "top" if not fp.IsFlipped() else "bottom"
        layer = pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd
        try:
            poly = fp.GetCourtyard(layer)
        except Exception as e:
            nocrt.append((ref, str(e)))
            continue
        if poly is None or poly.OutlineCount() == 0:
            nocrt.append((ref, "empty"))
            continue
        entries.append((ref, side, poly, poly.BBox()))
    log(log_path, "courtyards: %d with polygon, %d without" % (len(entries), len(nocrt)))

    bbox_pairs = []
    poly_pairs = []
    n = len(entries)
    for i in range(n):
        ri, si, pi, bi = entries[i]
        for j in range(i + 1, n):
            rj, sj, pj, bj = entries[j]
            if si != sj:
                continue
            if not bi.Intersects(bj):
                continue
            bbox_pairs.append((ri, rj, si))
            # polygon-exact: intersect and measure area
            inter = pcbnew.SHAPE_POLY_SET(pi)
            inter.BooleanIntersection(pj, pcbnew.SHAPE_POLY_SET.PM_FAST)
            area_nm2 = 0
            for k in range(inter.OutlineCount()):
                area_nm2 += inter.Outline(k).Area()
            area_mm2 = area_nm2 / 1e12  # nm^2 -> mm^2 (1 mm = 1e6 nm, area 1e12)
            if area_mm2 > 0.001:
                poly_pairs.append((ri, rj, si, area_mm2))
        if i % 20 == 0:
            log(log_path, "progress %d/%d footprints, bbox_pairs=%d poly_pairs=%d"
                % (i, n, len(bbox_pairs), len(poly_pairs)))

    with open(out_path, "w") as f:
        f.write("board: %s\n" % board_path)
        f.write("footprints total: %d\n" % len(fps))
        f.write("footprints with courtyard polygon: %d\n" % len(entries))
        f.write("footprints without courtyard: %s\n" % (nocrt,))
        f.write("same-side courtyard BBOX overlap pairs: %d\n" % len(bbox_pairs))
        for ri, rj, si in sorted(bbox_pairs):
            f.write("  BBOX %s x %s (%s)\n" % (ri, rj, si))
        f.write("same-side courtyard POLYGON overlap pairs (area > 0.001 mm^2): %d\n"
                % len(poly_pairs))
        for ri, rj, si, a in sorted(poly_pairs):
            f.write("  POLY %s x %s (%s) area=%.4f mm^2\n" % (ri, rj, si, a))
    log(log_path, "done bbox=%d poly=%d -> %s" % (len(bbox_pairs), len(poly_pairs), out_path))


if __name__ == "__main__":
    main()

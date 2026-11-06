#!/usr/bin/env python3
"""Cluster moat: for each expansion group, the minimum distance from
any of the group's pads to the nearest pad of a footprint NOT in the
group (any net, any layer a pad occupies). This is the open field a
cluster's escapes have before they meet a foreign part.

Usage: xvfb-run -a python3 hw/moat_probe.py <board> <out.txt>
Groups must match hw/expand_board.py.
"""
import math, sys
import wx
_app = wx.App(False)
import pcbnew

GROUPS = {
    "U7": ["U7", "X1", "C21", "C20", "R17", "C24", "C23", "C22"],
    "U4": ["U4", "R14", "R13", "FB1", "C13", "C12", "R12", "C15",
           "X2", "C14", "C51", "C50", "U5", "C9"],
    "U9": ["U9"],
    "U10": ["U10", "R27", "C31", "C30", "R26", "R23", "R24", "R25",
            "C35", "Q1", "C29", "R28", "T1", "R33", "C34", "R31",
            "R32", "D5", "C32", "R29", "R34"],
}


def mm(v):
    return pcbnew.ToMM(v)


def main():
    b = pcbnew.LoadBoard(sys.argv[1])
    fps = {fp.GetReference(): fp for fp in b.GetFootprints()}
    pads = {}
    for ref, fp in fps.items():
        pads[ref] = [(mm(p.GetPosition().x), mm(p.GetPosition().y))
                     for p in fp.Pads()]
    lines = ["board: %s" % sys.argv[1]]
    for seed, members in GROUPS.items():
        inset = set(members)
        best = (1e9, None, None)
        for ref in members:
            for (x, y) in pads[ref]:
                for oref, opads in pads.items():
                    if oref in inset:
                        continue
                    for (ox, oy) in opads:
                        d = math.hypot(x - ox, y - oy)
                        if d < best[0]:
                            best = (d, ref, oref)
        lines.append("group %-4s (%2d parts): moat %.2f mm  (%s pad -> %s)"
                     % (seed, len(members), best[0], best[1], best[2]))
    with open(sys.argv[2], "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()

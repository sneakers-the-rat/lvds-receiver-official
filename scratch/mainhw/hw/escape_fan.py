#!/usr/bin/env python3
"""Escape-fan measurement for named pads.

For each named pad, cast 16 rays (every 22.5 deg) of length RAY_LEN
from the pad centre in the F.Cu plane. A ray is BLOCKED if the
segment comes within PROBE_CLEAR (netclass clearance 0.2 + half of a
0.25 mm track, rounded) of any pad belonging to a different footprint
and a different net. A pad's fan score = free rays / 16; a pad that
was sealed has most rays blocked at its own doorstep.

Usage: xvfb-run -a python3 hw/escape_fan.py <board> <out.txt> REF.PIN [...]
"""
import math, sys
import wx
_app = wx.App(False)
import pcbnew

RAY_LEN = 4.0          # mm
PROBE_CLEAR = 0.33     # mm
NAMED = {
    "U7": ["6", "7", "9", "11", "12", "13", "15", "18", "19", "20",
           "21", "26", "27", "29", "32"],
    "U4": ["1", "3", "4", "9", "10", "11", "14", "15", "18", "20",
           "21", "26", "27", "29"],
    "U9": ["1", "3", "5", "6"],
    "U10": ["4", "7", "8", "9"],
}


def mm(v):
    return pcbnew.ToMM(v)


def main():
    board_path, out_path = sys.argv[1], sys.argv[2]
    b = pcbnew.LoadBoard(board_path)
    fps = {fp.GetReference(): fp for fp in b.GetFootprints()}
    foreign = []   # (ref, net, shape) for F.Cu pads
    targets = {}
    for ref, fp in fps.items():
        for pad in fp.Pads():
            if not pad.IsOnLayer(pcbnew.F_Cu):
                continue
            entry = (ref, pad.GetNetname(), pad.GetEffectiveShape())
            foreign.append(entry)
            if ref in NAMED and pad.GetNumber() in NAMED[ref]:
                p = pad.GetPosition()
                targets[(ref, pad.GetNumber())] = (mm(p.x), mm(p.y),
                                                   pad.GetNetname())
    lines = []
    for (ref, pin), (x, y, net) in sorted(targets.items()):
        free = 0
        blocked_dirs = []
        for k in range(16):
            ang = math.radians(k * 22.5)
            seg = pcbnew.SHAPE_SEGMENT(
                pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)),
                pcbnew.VECTOR2I(
                    pcbnew.FromMM(x + RAY_LEN * math.cos(ang)),
                    pcbnew.FromMM(y + RAY_LEN * math.sin(ang))))
            blocked = False
            for fref, fnet, fshape in foreign:
                if fref == ref or fnet == net:
                    continue
                if seg.Collide(fshape, pcbnew.FromMM(PROBE_CLEAR)):
                    blocked = True
                    break
            if blocked:
                blocked_dirs.append(k * 22.5)
            else:
                free += 1
        lines.append("%s.%s (%s) at (%.2f,%.2f): free %d/16%s"
                     % (ref, pin, net, x, y, free,
                        (" blocked@" + ",".join("%g" % d
                                                for d in blocked_dirs))
                        if blocked_dirs else ""))
    with open(out_path, "w") as f:
        f.write("board: %s\n" % board_path + "\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()

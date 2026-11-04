#!/usr/bin/env python3
"""Pass 65: board EXPANSION — the density fix.

Diagnosis (passes 11-64, docs/00-status.md): every routing stall on
this board traced to placement density — pads sealed by neighbouring
footprints, heal yields decaying 68/40/17/12/1 (pass 64) in a field
with no open escape channels. Nothing in docs/01 fixes the receiver
board's dimensions; the 100x80 outline was a pass-1 placement choice.
So the outline grows and the four congested clusters move into the
new field.

What happens here:
  * Outline extended +30 mm NORTH (y 0 -> -30): 100x80 -> 100x110 mm.
    North is the only side that moves neither connector edge (J1
    south, J2 east) nor the APD/TIA analog cluster (D1/U1/R1 west).
  * The four congested clusters move as rigid groups into the new
    strip (intra-cluster geometry, incl. decoupling adjacency,
    preserved exactly). Membership derived by hw/groups_expand.py
    (signal-net BFS + decoupling radius, GND/rails excluded from BFS)
    plus a hand-verified supplement for U10: D5/C32/R29/R34 are the
    HV secondary chain (rectifier, reservoir, divider string —
    pad nets probed: HV_RAW/HV_SEC/APD_K/TP_HV) which the BFS cannot
    see because it attaches through rail nets only.
  * ALL tracks/vias of every net touching a moved pad are ripped
    (GND excepted, per the move_cluster.py precedent — plus any
    track/via of any net whose endpoint sits on a moved pad's old
    position, i.e. GND stubs physically attached to moved pads).
    Every other net's copper is untouched.
  * NUDGES: small intra-group corrections applied after the rigid
    shift for courtyard grazes a rigid shift cannot separate
    (pairs both of whose members are in the same group). Filled in
    from courtyard_audit.py runs on this script's output.

Run: xvfb-run -a python3 hw/expand_board.py [in] [out]
"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew

GROUPS = {
    # seed: (members, (dx, dy)) — shifts in mm, y down-positive
    "U7": (["X1", "C21", "C20", "R17", "C24", "C23", "C22"],
           (56.0, -82.0)),
    "U4": (["R14", "R13", "FB1", "C13", "C12", "R12", "C15", "X2",
            "C14", "C51", "C50", "U5", "C9"],
           (3.0, -70.5)),
    "U9": ([], (42.0, -53.0)),
    "U10": (["R27", "C31", "C30", "R26", "R23", "R24", "R25", "C35",
             "Q1", "C29", "R28", "T1", "R33", "C34", "R31", "R32",
             "D5", "C32", "R29", "R34"],
            (-2.0, -25.0)),
}
NUDGES = {    # ref: (dx, dy) applied after the group shift; each from
    # courtyard-bbox arithmetic on the un-nudged expansion (see
    # results/courtyard-expanded-1.txt): the six intra-group grazes a
    # rigid shift cannot separate, cleared with >=0.4 mm to spare.
    "C21": (-1.2, 0.0),    # X1 x C21: west, away from the crystal
    "C51": (-0.8, 0.0),    # C51 x C13: west
    "C30": (-1.1, -0.9),   # R24 x C30: west+north (C31 clears by 0.44)
    "R28": (0.9, 0.0),     # R24 x R28: east
    "R27": (-0.7, 0.0),    # R27 x C35: west
    "C14": (0.0, 0.7),     # X2 x C14: south
}
NEW_NORTH_Y = -30.0


def mm(v):
    return pcbnew.ToMM(v)


def main(src="hw/pdlvds_rx.fr51.kicad_pcb",
         out="hw/pdlvds_rx.expanded.kicad_pcb"):
    board = pcbnew.LoadBoard(src)
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}

    moved = {}   # ref -> (dx, dy) total
    for seed, (members, shift) in GROUPS.items():
        for ref in [seed] + members:
            moved[ref] = shift
    for ref, (dx, dy) in NUDGES.items():
        gx, gy = moved[ref]
        moved[ref] = (gx + dx, gy + dy)

    # original pad positions of moved footprints (for stub ripping)
    old_pads = []
    affected = set()
    for ref in moved:
        for pad in fps[ref].Pads():
            p = pad.GetPosition()
            old_pads.append((mm(p.x), mm(p.y)))
            if pad.GetNetname():
                affected.add(pad.GetNetname())
    affected.discard("GND")
    print("moved footprints: %d" % len(moved))
    for seed, (members, shift) in GROUPS.items():
        print("  group %s shift (%+.1f,%+.1f): %s"
              % (seed, shift[0], shift[1],
                 ", ".join([seed] + members)))
    if NUDGES:
        print("  nudges: %s" % (NUDGES,))
    print("affected nets (ripped, GND excepted): %d" % len(affected))

    # move footprints
    for ref, (dx, dy) in moved.items():
        fp = fps[ref]
        p = fp.GetPosition()
        fp.SetPosition(pcbnew.VECTOR2I(p.x + pcbnew.FromMM(dx),
                                       p.y + pcbnew.FromMM(dy)))

    # rip copper
    def near_old_pad(pt):
        return any((pt[0] - q[0]) ** 2 + (pt[1] - q[1]) ** 2 <= 0.25
                   for q in old_pads)

    ripped = {"track": 0, "via": 0, "gnd_stub": 0}
    for tr in list(board.GetTracks()):
        is_via = isinstance(tr, pcbnew.PCB_VIA)
        if is_via:
            pts = [(mm(tr.GetPosition().x), mm(tr.GetPosition().y))]
        else:
            pts = [(mm(tr.GetStart().x), mm(tr.GetStart().y)),
                   (mm(tr.GetEnd().x), mm(tr.GetEnd().y))]
        if tr.GetNetname() in affected:
            board.RemoveNative(tr)
            ripped["via" if is_via else "track"] += 1
        elif any(near_old_pad(p) for p in pts):
            board.RemoveNative(tr)
            ripped["gnd_stub"] += 1
    print("ripped: %s" % (ripped,))

    # extend the outline north: top edge y=0 -> NEW_NORTH_Y, and the
    # west/east edges extended to meet it. Interior Edge.Cuts features
    # (the x12..46 / y23.6..25.1 rectangle) are not touched.
    n_edge = 0
    for d in board.GetDrawings():
        if d.GetLayer() != pcbnew.Edge_Cuts:
            continue
        s, e = d.GetStart(), d.GetEnd()
        sx, sy, ex, ey = mm(s.x), mm(s.y), mm(e.x), mm(e.y)
        def isx(v, t): return abs(v - t) < 0.1
        top = isx(sy, 0) and isx(ey, 0) and abs(ex - sx) > 90
        west = isx(sx, 0) and isx(ex, 0) and abs(ey - sy) > 70
        east = isx(sx, 100) and isx(ex, 100) and abs(ey - sy) > 70
        if top:
            d.SetStart(pcbnew.VECTOR2I(s.x, pcbnew.FromMM(NEW_NORTH_Y)))
            d.SetEnd(pcbnew.VECTOR2I(e.x, pcbnew.FromMM(NEW_NORTH_Y)))
            n_edge += 1
        elif west or east:
            for getter, setter in ((d.GetStart, d.SetStart),
                                   (d.GetEnd, d.SetEnd)):
                p = getter()
                if isx(mm(p.y), 0):
                    setter(pcbnew.VECTOR2I(p.x,
                                           pcbnew.FromMM(NEW_NORTH_Y)))
            n_edge += 1
    print("outline segments rewritten: %d" % n_edge)
    bb = board.GetBoardEdgesBoundingBox()
    print("new outline bbox: x %.2f..%.2f (w %.2f)  y %.2f..%.2f (h %.2f)"
          % (mm(bb.GetLeft()), mm(bb.GetRight()),
             mm(bb.GetRight()) - mm(bb.GetLeft()),
             mm(bb.GetTop()), mm(bb.GetBottom()),
             mm(bb.GetBottom()) - mm(bb.GetTop())))

    board.Save(out)
    print("saved", out)


if __name__ == "__main__":
    main(*(sys.argv[1:3] if len(sys.argv) > 1 else []))

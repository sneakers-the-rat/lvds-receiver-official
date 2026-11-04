#!/usr/bin/env python3
"""Surgical placement revision on a routed board.

Moves a set of footprints to new positions, rips ALL tracks/vias
of every net that touches a moved pad (plus any net whose copper
lies within RIP_R of a moved footprint's new pads — bystander
copper in the landing zone), and saves to a new file. The affected
nets are left as pad-only groups for repair6 to re-route in the
new geometry. Everything else — including the 45 groups repair6
attempt 1 connected — is preserved untouched.

Why: results/diagnose-repaired6b.txt — 50 NO_EXIT + 16 POCKET
groups, concentrated where the original placement packs
0.5 mm-pitch parts inside each other's clearance envelopes,
including literal pad-rect overlaps (U7.25/26/27 vs L2.1,
U12.9 vs U7.32, X1 vs U12/C21). No router can escape a pad whose
clearance envelope is occupied by another footprint's pad.

Moves (placement.py coordinates, mm, rotation unchanged):
  U12 (27,58)   -> (20,52)     LT3757 cluster out of U7's field
  L2  (32.5,58) -> (20,57.5)   S of U12, off U7's north row
  R38 (24.5,52.5) -> (20,47.5) U12 timing/comp parts follow
  R39 (29,52.5)   -> (24,47.5)
  C39 (31,54.5)   -> (21.5,49)
  R5  (22,50)     -> (16.5,50.5) clears U12.13 (cut 2 finding)
  X1  (25,57)     -> (30,55)   crystal N of U7's XI/XO pins
  C21 (25.5,56)   -> (27,54)   crystal load follows
  R14 (58,55.5)   -> (57,54)   clears X2.4 pad pair
First-cut positions (X1 at (30,56.5), L2 at (25.5,51), C39 at
(25.5,55.5)) were audited and corrected: X1's pads reached U7's
north row (8 new pairs), L2 hit R6 and an SH1 shield pad, C39 hit
a GND stitch via. The positions above are the audited second cut
(results/audit-moved.txt is the first cut's record).

Run: xvfb-run -a python3 hw/move_cluster.py [in] [out]
"""
import math, sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew

MOVES = {
    "U12": (20, 52), "L2": (20, 57.5), "R38": (20, 47.5),
    "R39": (24, 47.5), "C39": (21.5, 49), "X1": (30, 55),
    "C21": (27, 54), "R14": (57, 54), "R5": (16.5, 50.5),
}
RIP_R = 2.0   # mm around new pad positions: bystander copper rips

def main(src="hw/pdlvds_rx.repaired6b.kicad_pcb",
         out="hw/pdlvds_rx.moved.kicad_pcb"):
    board = pcbnew.LoadBoard(src)
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    affected = set()
    new_pads = []
    for ref, (x, y) in MOVES.items():
        fp = fps[ref]
        for pad in fp.Pads():
            if pad.GetNetname():
                affected.add(pad.GetNetname())
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x),
                                       pcbnew.FromMM(y)))
        for pad in fp.Pads():
            new_pads.append(pcbnew.ToMM(pad.GetPosition()))
        print(f"moved {ref} -> ({x}, {y})")
    # bystander nets: copper within RIP_R of any new pad centre
    def near_new_pad(pt):
        return any((pt[0] - q[0]) ** 2 + (pt[1] - q[1]) ** 2
                   <= RIP_R ** 2 for q in new_pads)
    for tr in list(board.GetTracks()):
        if isinstance(tr, pcbnew.PCB_VIA):
            pts = [pcbnew.ToMM(tr.GetPosition())]
        else:
            pts = [pcbnew.ToMM(tr.GetStart()),
                   pcbnew.ToMM(tr.GetEnd())]
        if any(near_new_pad(p) for p in pts):
            if tr.GetNetname():
                affected.add(tr.GetNetname())
    affected.discard("GND")
    print("affected nets:", sorted(affected))
    n_rip = 0
    for tr in list(board.GetTracks()):
        if tr.GetNetname() in affected:
            board.Remove(tr)
            n_rip += 1
    print(f"ripped {n_rip} tracks/vias")
    board.Save(out)
    print("saved", out)

if __name__ == "__main__":
    main(*sys.argv[1:])

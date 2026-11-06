#!/usr/bin/env python3
"""Regression test: thread/thread_far execute their via-priced
rips (regression for the Class T fix).

Failure history (pass 76): thread's A* priced foreign items
blocking a via disc (via_blockers) into the path's rip set, but
the reconstruction re-tested only same-layer path SEGMENTS
against live tracks and capped removals at len(rips). Via-priced
victims were never removed, so the placed vias violated the very
tracks they had priced: 15 of pass 76's 17 audit violations
(SLICEP via vs CDR_NIN/SLICEN, the HV cluster threads). The
anchor stubs (facing point -> first lattice node and last node
-> facing point) were placed with no blocker test at all; the
other 2 non-D1 violations were stub grazes against pads.

Fixture: two TGT pads face each other across a wide foreign PAD
(a wall: pads are unrippable) on F_Cu, forcing a layer change.
A victim track of net VIC lies on In1_Cu — a layer thread never
places tracks on — as a wide bar across every point the forced
via can land on (a second wall pad closes the F_Cu walk-around
to the south, so dodging the rip zone costs more than the rip),
so ONLY the via disc can price it. Checks, for both thread.py
and thread_far.py:
  1. the thread succeeds and places >= 1 via;
  2. exactly the priced victim is ripped (VIC track gone);
  3. a mini-audit (check_pcb.need_for shape math) finds no
     collision between the placed TGT copper and any remaining
     foreign item.

Pre-fix code fails 2 and 3: the via is placed, the victim
survives, and the via violates it.

Run: xvfb-run -a python3 hw/tests/test_thread_via_rip.py [HW_DIR]
(HW_DIR defaults to the repo's hw/; point it at a tree with the
pre-fix thread.py/thread_far.py to watch it fail.)
Exit 0 iff every check passes.
"""
import os
import sys

HW = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else \
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HW)
import wx
_app = wx.App(False)
import pcbnew
import check_pcb
import thread
import thread_far
from hand_stub import build_items

MM, TM = pcbnew.FromMM, pcbnew.ToMM
failures = []


def check(name, cond, detail=""):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}  {detail}")
    if not cond:
        failures.append(name)


def add_pad(board, ref, net, x, y, w, h):
    fp = pcbnew.FOOTPRINT(board)
    fp.SetReference(ref)
    fp.SetLayer(pcbnew.F_Cu)
    fp.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    board.Add(fp)
    pad = pcbnew.PAD(fp)
    pad.SetNumber("1")
    pad.SetShape(pcbnew.PAD_SHAPE_RECT)
    pad.SetSize(pcbnew.VECTOR2I(MM(w), MM(h)))
    ls = pcbnew.LSET()
    ls.AddLayer(pcbnew.F_Cu)
    pad.SetLayerSet(ls)
    pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
    pad.SetNet(net)
    fp.Add(pad)
    pad.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))


def make_board():
    board = pcbnew.BOARD()
    nets = {}
    for name in ("TGT", "VIC", "WALL"):
        nets[name] = pcbnew.NETINFO_ITEM(board, name)
        board.Add(nets[name])
    add_pad(board, "A1", nets["TGT"], 20.0, 20.0, 1.0, 0.5)
    add_pad(board, "A2", nets["TGT"], 20.0, 22.9, 1.0, 0.5)
    # walls: wider than the +-5 mm search corridor around x=20;
    # W2 closes the F_Cu walk-around south of A1
    add_pad(board, "W1", nets["WALL"], 20.0, 21.45, 12.0, 0.8)
    add_pad(board, "W2", nets["WALL"], 20.0, 18.6, 12.0, 0.8)
    # victim: a wide In1_Cu bar (y 19.9..21.1) under every via
    # landing the geometry allows; only a via disc can price it
    vic = pcbnew.PCB_TRACK(board)
    vic.SetStart(pcbnew.VECTOR2I(MM(14.0), MM(20.5)))
    vic.SetEnd(pcbnew.VECTOR2I(MM(26.0), MM(20.5)))
    vic.SetWidth(MM(1.2))
    vic.SetLayer(pcbnew.In1_Cu)
    vic.SetNet(nets["VIC"])
    board.Add(vic)
    return board


def mini_audit(board):
    """Collisions involving TGT copper, audit shape math."""
    items = build_items(board)
    bad = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            k1, n1, l1, s1, d1 = items[i]
            k2, n2, l2, s2, d2 = items[j]
            if n1 == n2 or (n1 != "TGT" and n2 != "TGT"):
                continue
            shared = l1 & l2
            if not shared:
                continue
            need = check_pcb.need_for(n1, n2, shared)
            if s1.Collide(s2, MM(need - 0.001)):
                bad.append(f"{n1}({d1}) vs {n2}({d2})")
    return bad


def main():
    for mod, label in ((thread_far, "thread_far"), (thread, "thread")):
        board = make_board()
        items = build_items(board)
        n_vic_before = sum(1 for t in board.GetTracks()
                           if t.GetNetname() == "VIC")
        check(f"{label}: fixture carries the VIC victim",
              n_vic_before == 1, f"got {n_vic_before}")
        res = mod.thread_one(board, items, "TGT")
        print(f"    {label}: {res}")
        check(f"{label}: thread succeeds", res.startswith("threaded"),
              res)
        vias = [t for t in board.GetTracks()
                if t.Type() == pcbnew.PCB_VIA_T
                and t.GetNetname() == "TGT"]
        check(f"{label}: a via was placed", len(vias) >= 1,
              f"got {len(vias)}")
        n_vic_after = sum(1 for t in board.GetTracks()
                          if t.GetNetname() == "VIC")
        check(f"{label}: via-priced victim was ripped",
              n_vic_after == 0, f"VIC tracks left: {n_vic_after}")
        bad = mini_audit(board)
        check(f"{label}: placed copper is audit-clean", not bad,
              "; ".join(bad[:4]))

    print("RESULT:", "FAIL" if failures else "PASS",
          f"({len(failures)} failed)")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()

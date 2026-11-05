#!/usr/bin/env python3
"""Respread prototype attempt 2: same MOVES as respread_u6u7.py but
LOCAL rip semantics (what a human doing this move in KiCad would
actually delete):
  (a) collision rip — any track/via (any net, incl GND) whose geometry
      comes within (pad radius + 0.30 mm) of a NEW pad centre of a
      moved footprint, on a layer the pad lives on (vias: all layers);
  (b) stub rip — tracks/vias of a net that touches a moved pad, when
      the item lies within 4 mm of that net's OLD pad position.
Everything else survives, including same-net copper that happens to
land next to a new pad (a free connection). Zones are NOT refilled by
this script; run hw/refill.py afterwards if the audit asks for it.

Run: xvfb-run -a python3 hw/respread_u6u7_local.py [in] [out]
"""
import math, sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
from respread_u6u7 import MOVES

def seg_pt_dist(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx-ax, by-ay
    L2 = dx*dx + dy*dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px-ax)*dx + (py-ay)*dy)/L2))
    cx, cy = ax + t*dx, ay + t*dy
    return math.hypot(px-cx, py-cy)

def track_pts(tr):
    if isinstance(tr, pcbnew.PCB_VIA):
        return [pcbnew.ToMM(tr.GetPosition())]
    return [pcbnew.ToMM(tr.GetStart()), pcbnew.ToMM(tr.GetEnd())]

def track_dist_to_pt(tr, p):
    pts = track_pts(tr)
    if len(pts) == 1:
        return math.hypot(pts[0][0]-p[0], pts[0][1]-p[1])
    return seg_pt_dist(p, pts[0], pts[1])

def main(src="hw/pdlvds_rx.exp41.kicad_pcb",
         out="hw/pdlvds_rx.exp43.kicad_pcb"):
    board = pcbnew.LoadBoard(src)
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    old_pads = {}   # net -> list of old pad centres (moved fps only)
    for ref in MOVES:
        for pad in fps[ref].Pads():
            n = pad.GetNetname()
            if n:
                old_pads.setdefault(n, []).append(pcbnew.ToMM(pad.GetPosition()))
    new_pads = []   # (centre, radius_mm, net)
    for ref, (x, y, rot) in MOVES.items():
        fp = fps[ref]
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
        if rot is not None:
            fp.SetOrientationDegrees(rot)
        for pad in fp.Pads():
            sz = pad.GetSize()
            r = 0.5 * math.hypot(pcbnew.ToMM(sz.x), pcbnew.ToMM(sz.y)) / math.sqrt(2) \
                + max(pcbnew.ToMM(sz.x), pcbnew.ToMM(sz.y)) / 2
            new_pads.append((pcbnew.ToMM(pad.GetPosition()), r, pad.GetNetname()))
        print(f"moved {ref} -> ({x}, {y}) rot={rot}")
    moved_nets = set(old_pads)
    rip, why = [], {}
    for tr in list(board.GetTracks()):
        net = tr.GetNetname()
        is_via = isinstance(tr, pcbnew.PCB_VIA)
        kill = None
        # (a) collision with a new pad of a different net
        for (c, r, pnet) in new_pads:
            if pnet == net and net:
                continue
            if is_via or tr.GetLayer() == pcbnew.F_Cu:
                if track_dist_to_pt(tr, c) <= r + 0.30:
                    kill = f"collision near new pad of {pnet}"
                    break
        # (b) stub of a moved net near its old pad
        if kill is None and net in moved_nets and net != "GND":
            for c in old_pads[net]:
                if track_dist_to_pt(tr, c) <= 4.0:
                    kill = "stub at old site"
                    break
        if kill:
            rip.append(tr); why[net] = why.get(net, 0) + 1
    for tr in rip:
        board.Remove(tr)
    print(f"ripped {len(rip)} items; by net:", dict(sorted(why.items())))
    board.Save(out)
    print("saved", out)

if __name__ == "__main__":
    main(*sys.argv[1:])

#!/usr/bin/env python3
"""Delete dead copper from a board: segments with a free end under a
STRENGTHENED anchor test, iterated to a fixpoint.

Written 2026-11-05 after the dead-end census (scratch/dead_end_census.py)
found 363 one-ended + 71 both-ended segments on exp147 that prune_dead's
own internal graph model had absorbed. This deleter differs from the
census in the two places the census is known-weak, both resolved in the
safe direction (a segment is spared if either test anchors it):

- pad contact is judged against the pad's bounding box (a track ending
  on a pad's copper, away from its centre, is anchored), not only by
  1 um centre coincidence;
- a segment whose net owns a zone (pour) on its layer is never
  deleted: zone contact is not modelled, so pour-net stubs are left
  for a zone-aware pass.

Iteration matters: deleting a tooth can turn the segment behind it
into a tooth (chains), so classification repeats on the surviving set
until no new segment qualifies.

Implementation note (learned the hard way, KiCad 8.0.9): after any
board.Remove(), later reads through pcbnew proxies break
(GetTracks() -> 'SwigPyObject' object is not iterable; GetStart() ->
proxy with no .x). So this script extracts PLAIN DATA first, computes
the whole fixpoint on tuples, and only then touches the board again:
one batch of Remove() calls followed by Save().

Usage: python3 scratch/delete_dead.py IN.kicad_pcb OUT.kicad_pcb

v1 (centreline tolerances) produced exp148: 1,240 segments deleted and
KiCad DRC unconnected ROSE 50 -> 115 with via_dangling 7 -> 106 --
rejected, never committed. v2 uses copper-overlap tolerances
throughout; DRC remains the referee (unconnected must not rise).
"""
import sys, math
from collections import defaultdict
import pcbnew

TOL = 2000  # 2 um in nm, point-on-segment collinearity
CU = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)

src, dst = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(src)

zone_nl = {(z.GetNetname(), z.GetLayer()) for z in board.Zones()}

# ---- phase 1: plain-data snapshot ---------------------------------
segs = []   # [net, layer, x0, y0, x1, y1, width]
for t in board.GetTracks():
    if t.Type() == pcbnew.PCB_TRACE_T:
        a, b = t.GetStart(), t.GetEnd()
        segs.append([t.GetNetname(), t.GetLayer(), a.x, a.y, b.x, b.y,
                     t.GetWidth()])
via_by_net = defaultdict(list)
for t in board.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        p = t.GetPosition()
        via_by_net[t.GetNetname()].append((p.x, p.y, t.GetWidth() // 2))
pad_by_net = defaultdict(list)   # net -> [(layers, cx, cy, bbox)]
for fp in board.GetFootprints():
    for p in fp.Pads():
        bb = p.GetBoundingBox()
        pos = p.GetPosition()
        layers = {l for l in CU if p.IsOnLayer(l)}
        pad_by_net[p.GetNetname()].append(
            (layers, pos.x, pos.y,
             (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom())))

def classify(segs):
    seg_by_nl = defaultdict(list)
    for i, s in enumerate(segs):
        seg_by_nl[(s[0], s[1])].append(i)

    def anchored(s, x, y, self_idx):
        # Copper-overlap semantics (v2 fix): two pieces of copper are
        # connected when they physically touch, so every test uses the
        # tracks' real widths -- v1's 1-2 um centreline tests called
        # ring-landing via joints and shallow T-junctions "free" and
        # severed live routes (DRC unconnected 50 -> 115).
        net, layer, hw = s[0], s[1], s[6] // 2
        for layers, cx, cy, (l, t, r, b) in pad_by_net.get(net, ()):
            if layer not in layers:
                continue
            if abs(cx - x) <= 1000 and abs(cy - y) <= 1000:
                return True
            if l - hw <= x <= r + hw and t - hw <= y <= b + hw:
                return True
        for (px, py, vr) in via_by_net.get(net, ()):
            if math.hypot(px - x, py - y) <= vr + hw + 1000:
                return True
        for j in seg_by_nl.get((net, layer), ()):
            if j == self_idx:
                continue
            o = segs[j]
            reach = hw + o[6] // 2 + 1000
            if math.hypot(o[2] - x, o[3] - y) <= reach or \
               math.hypot(o[4] - x, o[5] - y) <= reach:
                return True
            dx, dy = o[4] - o[2], o[5] - o[3]
            L2 = dx * dx + dy * dy
            if L2 == 0:
                continue
            cross = (x - o[2]) * dy - (y - o[3]) * dx
            if abs(cross) * 1.0 / math.sqrt(L2) > reach:
                continue
            dot = (x - o[2]) * dx + (y - o[3]) * dy
            if -reach * math.sqrt(L2) < dot < L2 + reach * math.sqrt(L2):
                return True
        return False

    dead_idx, spared = [], 0
    for i, s in enumerate(segs):
        if anchored(s, s[2], s[3], i) and anchored(s, s[4], s[5], i):
            continue
        if (s[0], s[1]) in zone_nl:
            spared += 1
            continue
        dead_idx.append(i)
    return dead_idx, spared

total = 0
for it in range(500):
    dead_idx, spared = classify(segs)
    print(f'iteration {it}: {len(segs)} segments, {len(dead_idx)} dead '
          f'(zone-spared: {spared})', flush=True)
    if not dead_idx:
        break
    drop = set(dead_idx)
    total += len(dead_idx)
    segs = [s for i, s in enumerate(segs) if i not in drop]
print(f'TOTAL dead (plain-data fixpoint): {total}')

# ---- phase 2: apply to the board ----------------------------------
# Recompute the surviving key set, then remove every board track whose
# key is not in it. Keys are (net, layer, x0, y0, x1, y1); duplicate
# identical segments share a key and are kept/deleted together, which
# matches the plain-data model (they anchor each other there too --
# identical twins are both kept or both dead consistently because the
# model treats them symmetrically).
alive_keys = {(s[0], s[1], s[2], s[3], s[4], s[5]) for s in segs}
to_remove = []
for t in board.GetTracks():
    if t.Type() != pcbnew.PCB_TRACE_T:
        continue
    a, b = t.GetStart(), t.GetEnd()
    if (t.GetNetname(), t.GetLayer(), a.x, a.y, b.x, b.y) not in alive_keys:
        to_remove.append(t)
removed = 0
for t in to_remove:
    board.Remove(t)
    removed += 1
print(f'removed from board: {removed}')
board.Save(dst)
print(f'saved {dst}')

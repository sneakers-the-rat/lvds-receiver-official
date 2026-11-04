#!/usr/bin/env python3
"""Surgery 2: for pads sealed by 1-3 foreign items, find the exit
direction whose audit-exact neck (0.2 mm wide, up to 1.6 mm long)
has the fewest foreign blockers, rip exactly those tracks/vias,
and place the neck as the pad's stub. One fetch of the track list
per rip decision (SWIG discipline from surgery1).

Run: xvfb-run -a python3 hw/surgery2.py IN OUT NET:REF.PAD [...]
Prints per pad: direction, ripped items, stub placed or not.
"""
import sys, math
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import check_pcb, repair6
from hand_stub import build_items

check_pcb.SURFACE = {pcbnew.F_Cu, pcbnew.B_Cu}
MM = pcbnew.FromMM
FCU = {pcbnew.F_Cu}

def seg(x1, y1, x2, y2, w):
    return pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(x1), MM(y1)),
                                pcbnew.VECTOR2I(MM(x2), MM(y2)),
                                MM(w))

def blockers(items, net, shape):
    out = []
    for kind, n2, l2, s2, d2 in items:
        if n2 == net:
            continue
        shared = FCU & l2
        if not shared:
            continue
        need = check_pcb.need_for(net, n2, shared)
        if shape.Collide(s2, MM(need - 0.001)):
            out.append((kind, n2, d2))
    return out

def main():
    src, out = sys.argv[1], sys.argv[2]
    targets = [tuple(s.split(':', 1)) for s in sys.argv[3:]]
    board = pcbnew.LoadBoard(src)
    pads = {}
    for fp in board.GetFootprints():
        for p in fp.Pads():
            pads[f'{fp.GetReference()}.{p.GetPadName()}'] = p
    for net, desc in targets:
        pad = pads[desc]
        cx, cy = pcbnew.ToMM(pad.GetPosition())
        items = build_items(board)
        best = None
        for k in range(16):
            a = math.radians(k * 22.5)
            dx, dy = math.cos(a), math.sin(a)
            for L in (0.8, 1.1, 1.4, 1.7):
                s = seg(cx + dx * 0.05, cy + dy * 0.05,
                        cx + dx * L, cy + dy * L, 0.2)
                bl = blockers(items, net, s)
                # pads cannot be ripped: price them at 10, tracks
                # and vias at 1, so the search prefers a direction
                # blocked only by rippable copper
                key = (sum(1 if d in ('track@stubcheck',
                                      'via@stubcheck') else 10
                           for _, _, d in bl), L)
                if best is None or key < best[0]:
                    best = (key, dx, dy, L, bl)
        (_, dx, dy, L, bl) = best
        rip_keys = {(n, d) for _, n, d in bl}
        print(f'{desc} ({net}): dir ({dx:.2f},{dy:.2f}) L={L} '
              f'blockers {sorted(rip_keys)}', flush=True)
        if len(rip_keys) > 4:
            print(f'  {desc}: too many blockers, skipped', flush=True)
            continue
        # rip: match tracks/vias by net + shape identity via desc is
        # impossible for tracks (all 'track@stubcheck'); instead
        # re-test each board track/via against the neck shape.
        s = seg(cx + dx * 0.05, cy + dy * 0.05,
                cx + dx * L, cy + dy * L, 0.2)
        items2 = build_items(board)
        shapemap = {}
        for kind, n2, l2, s2, d2 in items2:
            shapemap.setdefault(id(s2), (kind, n2))
        ripped = 0
        tracks = list(board.GetTracks())
        for t in tracks:
            if t.GetNetname() == net:
                continue
            if not t.IsOnLayer(pcbnew.F_Cu):
                continue
            ts = t.GetEffectiveShape()
            shared = FCU
            need = check_pcb.need_for(net, t.GetNetname(), shared)
            if s.Collide(ts, MM(need - 0.001)):
                board.Remove(t)
                ripped += 1
        print(f'  ripped {ripped} items', flush=True)
        # place the neck
        items = build_items(board)
        if blockers(items, net, s):
            print(f'  {desc}: neck still blocked after rip', flush=True)
            continue
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(MM(cx + dx * 0.05),
                                   MM(cy + dy * 0.05)))
        t.SetEnd(pcbnew.VECTOR2I(MM(cx + dx * L), MM(cy + dy * L)))
        t.SetWidth(MM(0.2))
        t.SetLayer(pcbnew.F_Cu)
        t.SetNet(board.FindNet(net))
        board.Add(t)
        print(f'  {desc}: stub placed', flush=True)
    repair6.save_checkpoint(board, out)
    print('saved', out, flush=True)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Dump one net's audit-exact groups (check_pcb's item model and
union-find, full membership + positions), plus each non-main group's
nearest main-group items by bbox distance.

Run: xvfb-run -a python3 hw/dump_groups.py BOARD NET
"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew

TM = pcbnew.ToMM

def main():
    board = pcbnew.LoadBoard(sys.argv[1])
    want = sys.argv[2]
    items = []  # (kind, net, layers, shape, bbox, desc, pos)
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            net = pad.GetNetname()
            if not net: continue
            layers = {l for l in (pcbnew.F_Cu, pcbnew.In1_Cu,
                                  pcbnew.In2_Cu, pcbnew.B_Cu)
                      if pad.IsOnLayer(l)}
            items.append(("pad", net, layers, pad.GetEffectiveShape(),
                          pad.GetBoundingBox(),
                          f"{fp.GetReference()}.{pad.GetNumber()}",
                          TM(pad.GetPosition().x), TM(pad.GetPosition().y)))
    for t in board.GetTracks():
        net = t.GetNetname()
        if isinstance(t, pcbnew.PCB_VIA):
            layers = {pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu}
            kind = "via"
        else:
            layers = {t.GetLayer()}; kind = "track"
        p = t.GetPosition()
        items.append((kind, net, layers, t.GetEffectiveShape(),
                      t.GetBoundingBox(), f"{kind}@{TM(p.x):.3f},{TM(p.y):.3f}",
                      TM(p.x), TM(p.y)))
    for z in board.Zones():
        net = z.GetNetname(); layer = z.GetLayer()
        poly = z.GetFilledPolysList(layer)
        if poly.OutlineCount() == 0: continue
        bb = z.GetBoundingBox()
        items.append(("zone", net, {layer}, poly, bb, f"zone L{layer}",
                      TM(bb.GetCenter().x), TM(bb.GetCenter().y)))
    parent = list(range(len(items)))
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb: parent[ra] = rb
    idxs = [i for i, it in enumerate(items) if it[1] == want]
    for ai in range(len(idxs)):
        for bi in range(ai + 1, len(idxs)):
            a, b = items[idxs[ai]], items[idxs[bi]]
            if not (a[2] & b[2]): continue
            if not a[4].Intersects(b[4]): continue
            try:
                if a[3].Collide(b[3], 0): union(idxs[ai], idxs[bi])
            except Exception:
                union(idxs[ai], idxs[bi])
    groups = {}
    for i in idxs: groups.setdefault(find(i), []).append(i)
    gs = sorted(groups.values(), key=len, reverse=True)
    print(f"{want}: {len(gs)} groups")
    main = gs[0]
    print(f"MAIN group: {len(main)} items")
    for gi, g in enumerate(gs[1:], 1):
        print(f"--- group {gi}: {len(g)} items")
        for i in g:
            it = items[i]
            print(f"    {it[5]} layers={sorted(it[2])} pos=({it[6]:.2f},{it[7]:.2f})")
        # nearest main-group items by bbox-centre distance
        import math
        cand = []
        for i in g:
            a = items[i]
            for j in main:
                b = items[j]
                d = math.hypot(a[6]-b[6], a[7]-b[7])
                cand.append((d, a[5], b[5], sorted(a[2] & b[2])))
        cand.sort()
        for d, da, db, shared in cand[:3]:
            print(f"    near: {da} -> {db} centre-dist {d:.2f} shared-layers {shared}")

if __name__ == "__main__":
    main()

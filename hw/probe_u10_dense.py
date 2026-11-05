#!/usr/bin/env python3
"""Dense 2D retest of the U10 east-column seal (pass-78 diagnosis).

The pass-78 WORKING_NOTES diagnosis priced the seal as "0.25 neck +
2x0.25 clearance = 0.75 > 0.70 channel" — but every tool in the tree
(check_pcb.need_for, router.netclass, hand_stub, hand_via, thread)
assigns the U10 control nets the DEFAULT class (0.20 mm), not 0.25:
the HV 1.0 class is an explicit set {APD_K, HV_RAW, HV_SEC} and the
0.25 power class is an explicit rail set. This probe re-tests the
row with the audit's own need_for on a dense 2D grid of via sites
(step 0.05) around each target pin, neck width 0.20 (router NECK_W)
from the pad in the site direction, via disc 0.6/0.3 as placed by
pass 78, on the CURRENT board (so pass 78's placed U10.7 via is a
live obstacle). A site is CLEAR iff neck (F.Cu) and disc (all
layers) both have zero blockers at need_for.

Run: xvfb-run -a python3 hw/probe_u10_dense.py BOARD TARGET [TARGET...]
"""
import sys, math
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import check_pcb

check_pcb.SURFACE = {pcbnew.F_Cu, pcbnew.B_Cu}
need_for = check_pcb.need_for
MM = pcbnew.FromMM
ALL = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)
LAYERS_OF = {l: i for i, l in enumerate(ALL)}

def build_items(board):
    items = []  # (kind, net, layers:set, shape, bbox, desc)
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            net = pad.GetNetname()
            if not net:
                continue
            layers = {l for l in ALL if pad.IsOnLayer(l)}
            items.append(("pad", net, layers, pad.GetEffectiveShape(),
                          pad.GetBoundingBox(),
                          f"{fp.GetReference()}.{pad.GetNumber()}"))
    for t in board.GetTracks():
        net = t.GetNetname()
        if not net:
            continue
        if t.Type() == pcbnew.PCB_VIA_T:
            layers = set(ALL)
            kind = "via"
        else:
            layers = {t.GetLayer()}
            kind = "track"
        items.append((kind, net, layers, t.GetEffectiveShape(),
                      t.GetBoundingBox(), f"{kind}@probe"))
    return items

def bbox_gap(bb, x, y):
    """Distance from point (mm) to bbox (mm); 0 if inside."""
    x0, y0 = pcbnew.ToMM(bb.GetX()), pcbnew.ToMM(bb.GetY())
    x1, y1 = x0 + pcbnew.ToMM(bb.GetWidth()), y0 + pcbnew.ToMM(bb.GetHeight())
    dx = max(x0 - x, 0.0, x - x1)
    dy = max(y0 - y, 0.0, y - y1)
    return math.hypot(dx, dy)

def blockers(items, net, shape, layers, cx, cy, reach):
    out = []
    for kind, n2, l2, s2, bb, desc in items:
        if n2 == net:
            continue
        shared = layers & l2
        if not shared:
            continue
        if bbox_gap(bb, cx, cy) > reach + 1.05:  # max need 1.0 + margin
            continue
        need = need_for(net, n2, shared)
        if shape.Collide(s2, MM(need - 0.001)):
            out.append((kind, n2, desc, round(need, 3)))
    return out

def main():
    path = sys.argv[1]
    targets = sys.argv[2:]
    board = pcbnew.LoadBoard(path)
    items = build_items(board)
    pads = {}
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            bb = pad.GetBoundingBox()
            pads[f"{fp.GetReference()}.{pad.GetNumber()}"] = (
                pad.GetNetname(), pcbnew.ToMM(pad.GetPosition()),
                (pcbnew.ToMM(bb.GetWidth()) / 2, pcbnew.ToMM(bb.GetHeight()) / 2))
    for target in targets:
        net, (px, py), (hx, hy) = pads[target]
        print(f"== {target} net={net} pos=({px:.2f},{py:.2f}) half=({hx:.2f},{hy:.2f})")
        clear_sites = []
        near = []
        xi = 0
        x = px + 0.30
        while x <= px + 3.20 + 1e-9:
            y = py - 1.25
            while y <= py + 1.25 + 1e-9:
                dx, dy = x - px, y - py
                dist = math.hypot(dx, dy)
                if dist > 0.3:
                    a = math.atan2(dy, dx)
                    ca, sa = math.cos(a), math.sin(a)
                    ext = min(hx / abs(ca) if ca else 1e9,
                              hy / abs(sa) if sa else 1e9)
                    startd = max(ext - 0.08, 0.25 * ext)
                    sx, sy = px + startd * ca, py + startd * sa
                    neck = pcbnew.SHAPE_SEGMENT(
                        pcbnew.VECTOR2I(MM(sx), MM(sy)),
                        pcbnew.VECTOR2I(MM(x), MM(y)), MM(0.20))
                    nb = blockers(items, net, neck, {pcbnew.F_Cu},
                                  (sx + x) / 2, (sy + y) / 2,
                                  dist / 2 + 0.4)
                    disc = pcbnew.SHAPE_SEGMENT(
                        pcbnew.VECTOR2I(MM(x), MM(y)),
                        pcbnew.VECTOR2I(MM(x), MM(y)), MM(0.6))
                    db = blockers(items, net, disc, set(ALL), x, y, 0.35)
                    tot = len(nb) + len(db)
                    if tot == 0:
                        clear_sites.append((round(x, 2), round(y, 2)))
                    elif tot == 1:
                        near.append(((round(x, 2), round(y, 2)),
                                     [b[1] + ':' + b[0] + ':need' + str(b[3]) for b in nb],
                                     [b[1] + ':' + b[0] + ':need' + str(b[3]) for b in db]))
                y += 0.05
            x += 0.05
            xi += 1
        print(f"   CLEAR sites: {len(clear_sites)}")
        for s in clear_sites[:40]:
            print(f"     site {s}")
        print(f"   1-blocker sites: {len(near)}")
        seen = set()
        for site, nb, db in near:
            key = (tuple(nb), tuple(db))
            if key in seen:
                continue
            seen.add(key)
            print(f"     site {site} neck={nb} disc={db}")
            if len(seen) >= 12:
                break

if __name__ == "__main__":
    main()

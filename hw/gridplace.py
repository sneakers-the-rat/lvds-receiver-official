#!/usr/bin/env python3
"""Grid-search placer for the re-sync's big/cluster parts.

For a footprint and a search region, finds the feasible position
closest to a home point: the part's pads clear every other part's
pads by >= gap (exact shape Collide, with a centre-distance
shortlist so only nearby pads are shape-tested), and optionally
the body box clears other pads and given solid boxes.
"""
import math
import pcbnew

MMf = pcbnew.FromMM
MMt = pcbnew.ToMM

def _others(board, exclude_ref):
    out = []
    for fp in board.GetFootprints():
        if fp.GetReference() == exclude_ref:
            continue
        for p in fp.Pads():
            pp = p.GetPosition()
            out.append((MMt(pp.x), MMt(pp.y), p))
    return out

def place(board, fp, region, home, rots=(0,), gap=0.25, body=False,
          solids=(), step=0.5, log=print, body_wh=None):
    """region = (x1, y1, x2, y2) centre search box; home = (x, y).
    Returns (x, y, rot) or None. Leaves fp at the winning pose."""
    x1, y1, x2, y2 = region
    others = _others(board, fp.GetReference())
    best = None
    nx = int(round((x2 - x1) / step)) + 1
    ny = int(round((y2 - y1) / step)) + 1
    for rot in rots:
        fp.SetOrientation(pcbnew.EDA_ANGLE(rot, pcbnew.DEGREES_T))
        for i in range(nx):
            for j in range(ny):
                x = x1 + i * step
                y = y1 + j * step
                d = math.hypot(x - home[0], y - home[1])
                if best is not None and d >= best[0]:
                    continue
                fp.SetPosition(pcbnew.VECTOR2I(MMf(x), MMf(y)))
                bb = fp.GetBoundingBox()
                cx, cy = MMt(bb.Centre().x), MMt(bb.Centre().y)
                reach = 0.5 * math.hypot(
                    MMt(bb.GetRight() - bb.GetLeft()),
                    MMt(bb.GetBottom() - bb.GetTop())) + gap + 1.0
                near = [(ox, oy, op) for (ox, oy, op) in others
                        if abs(ox - cx) < reach and abs(oy - cy) < reach]
                bad = False
                for p in fp.Pads():
                    s = p.GetEffectiveShape(0)
                    for (ox, oy, op) in near:
                        if s.Collide(op.GetEffectiveShape(0),
                                     MMf(gap - 0.001)):
                            bad = True
                            break
                    if bad:
                        break
                if bad:
                    continue
                if body:
                    if body_wh is not None:
                        # physical body rect centred on the part
                        # (the footprint bbox may carry oversized
                        # graphics — EFD20's spans 59.9 mm against
                        # a 23.11 mm frame)
                        w, h = body_wh
                        if rot in (90, 270):
                            w, h = h, w
                        rect = pcbnew.SHAPE_RECT(
                            pcbnew.VECTOR2I(MMf(x - w / 2),
                                            MMf(y - h / 2)),
                            MMf(w), MMf(h))
                    else:
                        rect = pcbnew.SHAPE_RECT(
                            pcbnew.VECTOR2I(bb.GetLeft(), bb.GetTop()),
                            int(bb.GetRight() - bb.GetLeft()),
                            int(bb.GetBottom() - bb.GetTop()))
                    for (ox, oy, op) in near:
                        if rect.Collide(op.GetEffectiveShape(0),
                                        MMf(0.0)):
                            bad = True
                            break
                    if not bad:
                        for (sx1, sy1, sx2, sy2) in solids:
                            r2 = pcbnew.SHAPE_RECT(
                                pcbnew.VECTOR2I(MMf(sx1), MMf(sy1)),
                                MMf(sx2 - sx1), MMf(sy2 - sy1))
                            if r2.Collide(rect, MMf(0.0)):
                                bad = True
                                break
                    if bad:
                        continue
                best = (d, x, y, rot)
    if best is None:
        log(f'  {fp.GetReference()}: NO feasible point in {region}')
        return None
    _, x, y, rot = best
    fp.SetPosition(pcbnew.VECTOR2I(MMf(x), MMf(y)))
    fp.SetOrientation(pcbnew.EDA_ANGLE(rot, pcbnew.DEGREES_T))
    log(f'  {fp.GetReference()} grid-placed @({x},{y}) rot={rot}')
    return (x, y, rot)

"""Silk reflow v3: exact rotated-pad distance, own-shape obstacles,
Edge.Cuts obstacles (0.5 gap), 0/90-degree text, radius 25.
Usage: t_al20_silk3.py board_in board_out drc_json"""
import sys, json, math, re, wx
_app = wx.App(False)
import pcbnew

SRC, OUT, DRCJ = sys.argv[1], sys.argv[2], sys.argv[3]
d = json.load(open(DRCJ))
bad = set()
for v in d['violations']:
    if not v['type'].startswith('silk'):
        continue
    for it in v['items']:
        m = re.search(r"Reference '(\w+)'", it['description'])
        if m:
            bad.add(m.group(1))
print(f'{len(bad)} refs to reflow: {sorted(bad)}', flush=True)

board = pcbnew.LoadBoard(SRC)
MM = pcbnew.ToMM
GAP = 0.06
GEDGE = 0.5
CELL = 2.0

def pt_seg(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    if L == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))

def seg_seg(ax, ay, bx, by, cx, cy, dx, dy):
    def orient(px, py, qx, qy, rx, ry):
        return (qx - px) * (ry - py) - (qy - py) * (rx - px)
    o1, o2 = orient(ax, ay, bx, by, cx, cy), orient(ax, ay, bx, by, dx, dy)
    o3, o4 = orient(cx, cy, dx, dy, ax, ay), orient(cx, cy, dx, dy, bx, by)
    if (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0):
        return 0.0
    return min(pt_seg(ax, ay, cx, cy, dx, dy), pt_seg(bx, by, cx, cy, dx, dy),
               pt_seg(cx, cy, ax, ay, bx, by), pt_seg(dx, dy, ax, ay, bx, by))

def seg_rect(ax, ay, bx, by, x0, y0, x1, y1):
    if x0 <= ax <= x1 and y0 <= ay <= y1:
        return 0.0
    if x0 <= bx <= x1 and y0 <= by <= y1:
        return 0.0
    return min(seg_seg(ax, ay, bx, by, x0, y0, x1, y0), seg_seg(ax, ay, bx, by, x1, y0, x1, y1),
               seg_seg(ax, ay, bx, by, x1, y1, x0, y1), seg_seg(ax, ay, bx, by, x0, y1, x0, y0))

def pt_rect(px, py, x0, y0, x1, y1):
    return math.hypot(max(x0 - px, px - x1, 0), max(y0 - py, py - y1, 0))

def rect_rect(ax0, ay0, ax1, ay1, bx0, by0, bx1, by1):
    return math.hypot(max(bx0 - ax1, ax0 - bx1, 0), max(by0 - ay1, ay0 - by1, 0))

copper_b = {}
def add_copper(kind, data, cx, cy, reach):
    obj = (kind, data)
    for gx in range(int((cx - reach) // CELL), int((cx + reach) // CELL) + 1):
        for gy in range(int((cy - reach) // CELL), int((cy + reach) // CELL) + 1):
            copper_b.setdefault((gx, gy), []).append(obj)

def bucket_near(buckets, x0, y0, x1, y1):
    out = []
    for cx in range(int(x0 // CELL), int(x1 // CELL) + 1):
        for cy in range(int(y0 // CELL), int(y1 // CELL) + 1):
            out.extend(buckets.get((cx, cy), []))
    return out

for fp in board.GetFootprints():
    for pad in fp.Pads():
        if pad.IsOnLayer(pcbnew.F_Cu):
            x, y = MM(pad.GetPosition()); sx, sy = MM(pad.GetSize())
            rot = math.radians(pad.GetOrientationDegrees())
            cs, sn = math.cos(rot), math.sin(rot)
            corners = []
            for (lx, ly) in [(sx / 2, sy / 2), (sx / 2, -sy / 2), (-sx / 2, sy / 2), (-sx / 2, -sy / 2)]:
                corners.append((x + lx * cs - ly * sn, y + lx * sn + ly * cs))
            add_copper('pad', corners, x, y, math.hypot(sx, sy) / 2 + 0.3)
for t in board.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        x, y = MM(t.GetPosition()); r = MM(t.GetWidth()) / 2
        add_copper('via', (x, y, r), x, y, r + 0.3)
    elif t.GetLayer() == pcbnew.F_Cu:
        a = MM(t.GetStart()); b = MM(t.GetEnd()); w = MM(t.GetWidth())
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        add_copper('seg', (a[0], a[1], b[0], b[1], w / 2), mx, my,
                   math.hypot(a[0] - b[0], a[1] - b[1]) / 2 + w / 2 + 0.3)

def copper_clear(x0, y0, x1, y1):
    for kind, data in bucket_near(copper_b, x0 - 0.3, y0 - 0.3, x1 + 0.3, y1 + 0.3):
        if kind == 'via':
            cx, cy, r = data
            if pt_rect(cx, cy, x0, y0, x1, y1) - r < GAP:
                return False
        elif kind == 'seg':
            ax, ay, bx, by, hw = data
            if seg_rect(ax, ay, bx, by, x0, y0, x1, y1) - hw < GAP:
                return False
        else:
            corners = data
            for i in range(4):
                ax, ay = corners[i]; bx, by = corners[(i + 1) % 4]
                if seg_rect(ax, ay, bx, by, x0, y0, x1, y1) < GAP:
                    return False
            cx = sum(c[0] for c in corners) / 4; cy = sum(c[1] for c in corners) / 4
            if x0 <= cx <= x1 and y0 <= cy <= y1:
                return False
    return True

# edge cuts as segment obstacles
edge_segs = []
def harvest_edge(item):
    bb = item.GetBoundingBox()
    edge_segs.append((MM(bb.GetLeft()), MM(bb.GetTop()), MM(bb.GetRight()), MM(bb.GetBottom())))
for dr in board.GetDrawings():
    if dr.GetLayer() == pcbnew.Edge_Cuts:
        harvest_edge(dr)
for fp in board.GetFootprints():
    for gi in fp.GraphicalItems():
        if gi.GetLayer() == pcbnew.Edge_Cuts:
            harvest_edge(gi)
# NOTE: bboxes of edge items used as thin rects -- conservative approx:
# treat each as its bbox rect expanded; distance via rect_rect on the
# item's own bbox is wrong for lines, so instead store centreline segs
# when the shape is a segment.
edge_segs = []
def harvest_edge2(item):
    try:
        a = MM(item.GetStart()); b = MM(item.GetEnd())
        edge_segs.append((a[0], a[1], b[0], b[1]))
        return
    except Exception:
        pass
    bb = item.GetBoundingBox()
    edge_segs.append((MM(bb.GetLeft()), MM(bb.GetTop()), MM(bb.GetRight()), MM(bb.GetTop())))
    edge_segs.append((MM(bb.GetRight()), MM(bb.GetTop()), MM(bb.GetRight()), MM(bb.GetBottom())))
    edge_segs.append((MM(bb.GetRight()), MM(bb.GetBottom()), MM(bb.GetLeft()), MM(bb.GetBottom())))
    edge_segs.append((MM(bb.GetLeft()), MM(bb.GetBottom()), MM(bb.GetLeft()), MM(bb.GetTop())))
for dr in board.GetDrawings():
    if dr.GetLayer() == pcbnew.Edge_Cuts:
        harvest_edge2(dr)
for fp in board.GetFootprints():
    for gi in fp.GraphicalItems():
        if gi.GetLayer() == pcbnew.Edge_Cuts:
            harvest_edge2(gi)
print(f'{len(edge_segs)} edge segments', flush=True)

def edge_clear(x0, y0, x1, y1):
    for (ax, ay, bx, by) in edge_segs:
        if seg_rect(ax, ay, bx, by, x0, y0, x1, y1) < GAP + 0.0:
            return False
    return True

silk_boxes = []
refmap = {}
for fp in board.GetFootprints():
    ref = fp.GetReference()
    refmap[ref] = fp
    for gi in fp.GraphicalItems():
        if gi.GetLayer() == pcbnew.F_SilkS:
            bb = gi.GetBoundingBox()
            silk_boxes.append([MM(bb.GetLeft()), MM(bb.GetTop()), MM(bb.GetRight()), MM(bb.GetBottom()), ref])
ref_boxes = {}
for fp in board.GetFootprints():
    bb = fp.Reference().GetBoundingBox()
    ref_boxes[fp.GetReference()] = [MM(bb.GetLeft()), MM(bb.GetTop()), MM(bb.GetRight()), MM(bb.GetBottom())]

def silk_clear(x0, y0, x1, y1, self_ref):
    for b in silk_boxes:
        if rect_rect(x0, y0, x1, y1, b[0], b[1], b[2], b[3]) < GAP:
            return False
    for r, b in ref_boxes.items():
        if r != self_ref and rect_rect(x0, y0, x1, y1, b[0], b[1], b[2], b[3]) < GAP:
            return False
    return True

moved, failed = 0, []
for ref in sorted(bad):
    fp = refmap.get(ref)
    if fp is None:
        failed.append((ref, 'no footprint')); continue
    txt = fp.Reference()
    orig_angle = txt.GetTextAngleDegrees()
    fx, fy = MM(fp.GetPosition().x), MM(fp.GetPosition().y)
    placed = False
    for angle in [orig_angle, 90.0 if abs(orig_angle) < 1 else 0.0]:
        txt.SetTextAngleDegrees(angle)
        px, py = MM(txt.GetPosition().x), MM(txt.GetPosition().y)
        bb = txt.GetBoundingBox()
        w, h = MM(bb.GetWidth()), MM(bb.GetHeight())
        offx, offy = MM(bb.GetCenter().x) - px, MM(bb.GetCenter().y) - py
        r = 0.0
        while r <= 25.0 and not placed:
            if r == 0:
                cands = [(fx, fy)]
            else:
                steps = max(8, int(2 * math.pi * r / 0.3))
                cands = [(fx + r * math.cos(2 * math.pi * s / steps), fy + r * math.sin(2 * math.pi * s / steps))
                         for s in range(steps)]
            for (ax, ay) in cands:
                x0, y0 = ax + offx - w / 2, ay + offy - h / 2
                x1, y1 = ax + offx + w / 2, ay + offy + h / 2
                if x0 < 0.6 or y0 < -29.4 or x1 > 99.4 or y1 > 79.4:
                    continue
                if copper_clear(x0, y0, x1, y1) and silk_clear(x0, y0, x1, y1, ref) and edge_clear(x0, y0, x1, y1):
                    txt.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(ax), pcbnew.FromMM(ay)))
                    ref_boxes[ref] = [x0, y0, x1, y1]
                    placed = True
                    break
            r += 0.25
        if placed:
            break
    if not placed:
        txt.SetTextAngleDegrees(orig_angle)
        failed.append((ref, 'no clear spot in 25mm'))
    else:
        moved += 1
print(f'moved {moved}, failed {len(failed)}: {failed}', flush=True)
board.Save(OUT)
print('saved', OUT)

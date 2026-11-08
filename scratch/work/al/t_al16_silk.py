"""Reference-designator reflow v2 (spatial buckets, exact distances).
Moves every ref named in the DRC silk violations to the nearest
anchor whose text bbox clears all F copper and F silk by >= GAP.
Usage: t_al16_silk.py board_in board_out drc_json"""
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
print(f'{len(bad)} refs to reflow', flush=True)

board = pcbnew.LoadBoard(SRC)
MM = pcbnew.ToMM
GAP = 0.06
CELL = 2.0

def bucket_add(buckets, x, y, obj):
    buckets.setdefault((int(x // CELL), int(y // CELL)), []).append(obj)

def bucket_near(buckets, x0, y0, x1, y1):
    out = []
    for cx in range(int(x0 // CELL), int(x1 // CELL) + 1):
        for cy in range(int(y0 // CELL), int(y1 // CELL) + 1):
            out.extend(buckets.get((cx, cy), []))
    return out

# --- copper obstacles, bucketed by item centre (pad=2 cells reach) ---
copper_b = {}
def add_copper(kind, data, cx, cy, reach):
    obj = (kind, data)
    for gx in range(int((cx - reach) // CELL), int((cx + reach) // CELL) + 1):
        for gy in range(int((cy - reach) // CELL), int((cy + reach) // CELL) + 1):
            copper_b.setdefault((gx, gy), []).append(obj)

for fp in board.GetFootprints():
    for pad in fp.Pads():
        if pad.IsOnLayer(pcbnew.F_Cu):
            x, y = MM(pad.GetPosition()); sx, sy = MM(pad.GetSize())
            data = (x, y, sx / 2, sy / 2, math.radians(pad.GetOrientationDegrees()))
            add_copper('pad', data, x, y, math.hypot(sx, sy) / 2 + 0.3)
for t in board.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        x, y = MM(t.GetPosition()); r = MM(t.GetWidth()) / 2
        add_copper('via', (x, y, r), x, y, r + 0.3)
    elif t.GetLayer() == pcbnew.F_Cu:
        a = MM(t.GetStart()); b = MM(t.GetEnd()); w = MM(t.GetWidth())
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        reach = math.hypot(a[0] - b[0], a[1] - b[1]) / 2 + w / 2 + 0.3
        add_copper('seg', (a[0], a[1], b[0], b[1], w / 2), mx, my, reach)

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
            cx, cy, hx, hy, rot = data
            if abs(rot) < 0.01:
                if rect_rect(x0, y0, x1, y1, cx - hx, cy - hy, cx + hx, cy + hy) < GAP:
                    return False
            else:
                # rotated pad: distance from rect to pad centre vs bounding circle (conservative)
                if pt_rect(cx, cy, x0, y0, x1, y1) - math.hypot(hx, hy) < GAP and \
                   rect_rect(x0, y0, x1, y1, cx - hx - 0.42, cy - hy - 0.42, cx + hx + 0.42, cy + hy + 0.42) < GAP:
                    # exact-ish: sample pad corners rotated
                    cs, sn = math.cos(rot), math.sin(rot)
                    okc = True
                    for (lx, ly) in [(hx, hy), (hx, -hy), (-hx, hy), (-hx, -hy)]:
                        px, py = cx + lx * cs - ly * sn, cy + lx * sn + ly * cs
                        if pt_rect(px, py, x0, y0, x1, y1) < GAP:
                            okc = False
                    if not okc:
                        return False
    return True

# --- silk obstacles ---
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
    ref = fp.GetReference()
    bb = fp.Reference().GetBoundingBox()
    ref_boxes[ref] = [MM(bb.GetLeft()), MM(bb.GetTop()), MM(bb.GetRight()), MM(bb.GetBottom())]

def silk_clear(x0, y0, x1, y1, self_ref):
    for b in silk_boxes:
        if b[4] != self_ref and rect_rect(x0, y0, x1, y1, b[0], b[1], b[2], b[3]) < GAP:
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
    px, py = MM(txt.GetPosition().x), MM(txt.GetPosition().y)
    bb = txt.GetBoundingBox()
    w, h = MM(bb.GetWidth()), MM(bb.GetHeight())
    offx, offy = MM(bb.GetCenter().x) - px, MM(bb.GetCenter().y) - py
    fx, fy = MM(fp.GetPosition().x), MM(fp.GetPosition().y)
    best = None
    r = 0.0
    while r <= 12.0 and best is None:
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
            if copper_clear(x0, y0, x1, y1) and silk_clear(x0, y0, x1, y1, ref):
                best = (ax, ay)
                break
        r += 0.25
    if best is None:
        failed.append((ref, 'no clear spot in 12mm'))
        continue
    txt.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(best[0]), pcbnew.FromMM(best[1])))
    ref_boxes[ref] = [best[0] + offx - w / 2, best[1] + offy - h / 2,
                      best[0] + offx + w / 2, best[1] + offy + h / 2]
    moved += 1
print(f'moved {moved}, failed {len(failed)}: {failed}', flush=True)
board.Save(OUT)
print('saved', OUT)

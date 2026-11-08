"""Reference-designator reflow: move every ref named in the DRC
silk violations to the nearest position whose text bbox clears all
F copper (pads/tracks/vias) and all F silk (other refs' bboxes +
footprint silk-shape bboxes). Exact referee = kicad-cli DRC after.
Usage: t_al15_silk.py board_in board_out drc_json"""
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
print(f'{len(bad)} refs to reflow')

board = pcbnew.LoadBoard(SRC)
MM = pcbnew.ToMM

# copper obstacles on F: (kind, data) pads rect / seg / via disc
copper = []
for fp in board.GetFootprints():
    for pad in fp.Pads():
        if pad.IsOnLayer(pcbnew.F_Cu):
            x, y = MM(pad.GetPosition()); sx, sy = MM(pad.GetSize())
            copper.append(('pad', (x, y, sx / 2, sy / 2, math.radians(pad.GetOrientationDegrees()))))
for t in board.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        x, y = MM(t.GetPosition())
        copper.append(('via', (x, y, MM(t.GetWidth()) / 2)))
    elif t.GetLayer() == pcbnew.F_Cu:
        a = MM(t.GetStart()); b = MM(t.GetEnd())
        copper.append(('seg', (a[0], a[1], b[0], b[1], MM(t.GetWidth()) / 2)))

sys.path.insert(0, 'hw')
from router import dist_to_item

def rect_hits(x0, y0, x1, y1, gap):
    """True if rect [x0,x1]x[y0,y1] comes within gap of any copper item
    (sampled: item distance to rect via closest-point clamp)."""
    for kind, data in copper:
        if kind == 'pad':
            cx, cy, hx, hy, rot = data
            if abs(rot) < 0.01:
                dx = max(x0 - (cx + hx), (cx - hx) - x1, 0)
                dy = max(y0 - (cy + hy), (cy - hy) - y1, 0)
                if math.hypot(dx, dy) < gap:
                    return True
            else:
                # rotated pad: test rect corners + pad centre via dist_to_item on corners/edges
                it = ('pad', '', data, 0.2)
                for px, py in [(x0, y0), (x1, y0), (x0, y1), (x1, y1)]:
                    if dist_to_item(it, px, py) < gap:
                        return True
                if x0 <= cx <= x1 and y0 <= cy <= y1:
                    return True
        elif kind == 'via':
            cx, cy, r = data
            dx = max(x0 - cx, cx - x1, 0); dy = max(y0 - cy, cy - y1, 0)
            if math.hypot(dx, dy) - r < gap:
                return True
        else:
            ax, ay, bx, by, hw = data
            # distance from segment to rect: sample endpoints + closest clamp
            it = ('seg', '', data, 0.2)
            dmin = 9e9
            for px, py in [(x0, y0), (x1, y0), (x0, y1), (x1, y1)]:
                dmin = min(dmin, dist_to_item(it, px, py))
            for px, py in [(ax, ay), (bx, by)]:
                dx = max(x0 - px, px - x1, 0); dy = max(y0 - py, py - y1, 0)
                dmin = min(dmin, math.hypot(dx, dy))
            if dmin - hw < gap:
                return True
    return False

# silk obstacles: bbox per graphical item + per ref (updated live)
silk_boxes = []   # (x0,y0,x1,y1, owner_ref)
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

def silk_hits(x0, y0, x1, y1, self_ref, gap):
    for b in silk_boxes:
        if b[4] == self_ref:
            continue
        if not (x1 + gap < b[0] or b[2] + gap < x0 or y1 + gap < b[1] or b[3] + gap < y0):
            return True
    for r, b in ref_boxes.items():
        if r == self_ref:
            continue
        if not (x1 + gap < b[0] or b[2] + gap < x0 or y1 + gap < b[1] or b[3] + gap < y0):
            return True
    return False

GAP = 0.06
moved, failed = 0, []
for ref in sorted(bad):
    fp = refmap.get(ref)
    if fp is None:
        failed.append((ref, 'no footprint')); continue
    txt = fp.Reference()
    pos = txt.GetPosition()
    px, py = MM(pos.x), MM(pos.y)
    bb = txt.GetBoundingBox()
    w = MM(bb.GetWidth()); h = MM(bb.GetHeight())
    cx, cy = MM(bb.GetCenter().x), MM(bb.GetCenter().y)
    offx, offy = cx - px, cy - py   # bbox centre offset from text anchor
    fpos = fp.GetPosition()
    fx, fy = MM(fpos.x), MM(fpos.y)
    best = None
    # candidate anchors: rings around footprint centre
    cands = []
    for r in [i * 0.25 for i in range(0, 41)]:
        if r == 0:
            cands.append((fx, fy))
            continue
        steps = max(8, int(2 * math.pi * r / 0.35))
        for s in range(steps):
            a = 2 * math.pi * s / steps
            cands.append((fx + r * math.cos(a), fy + r * math.sin(a)))
    for (ax, ay) in cands:
        x0, y0 = ax + offx - w / 2, ay + offy - h / 2
        x1, y1 = ax + offx + w / 2, ay + offy + h / 2
        if x0 < 0.6 or y0 < -29.4 or x1 > 99.4 or y1 > 79.4:
            continue
        if rect_hits(x0, y0, x1, y1, GAP):
            continue
        if silk_hits(x0, y0, x1, y1, ref, GAP):
            continue
        best = (ax, ay)
        break
    if best is None:
        failed.append((ref, 'no clear spot in 10mm'))
        continue
    txt.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(best[0]), pcbnew.FromMM(best[1])))
    ref_boxes[ref] = [best[0] + offx - w / 2, best[1] + offy - h / 2,
                      best[0] + offx + w / 2, best[1] + offy + h / 2]
    moved += 1
print(f'moved {moved}, failed {len(failed)}: {failed}')
board.Save(OUT)
print('saved', OUT)

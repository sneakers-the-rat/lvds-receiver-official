"""t_ai7: list GND zone fill islands on a layer within a box, with
the GND pads and GND vias each island touches. Usage:
  t_ai7_islands.py board LAYER(F|In1|B) x0 x1 y0 y1"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew

SRC, LAYN = sys.argv[1], sys.argv[2]
X0, X1, Y0, Y1 = map(float, sys.argv[3:7])
LAY = {'F': pcbnew.F_Cu, 'In1': pcbnew.In1_Cu,
       'In2': pcbnew.In2_Cu, 'B': pcbnew.B_Cu}[LAYN]
board = pcbnew.LoadBoard(SRC)

def in_box(x, y):
    return X0 <= x <= X1 and Y0 <= y <= Y1

def outlines(polyset):
    out = []
    for i in range(polyset.OutlineCount()):
        ch = polyset.Outline(i)
        pts = [(pcbnew.ToMM(ch.GetPoint(j).x),
                pcbnew.ToMM(ch.GetPoint(j).y))
               for j in range(ch.PointCount())]
        holes = []
        for h in range(polyset.HoleCount(i)):
            hc = polyset.Hole(i, h)
            holes.append([(pcbnew.ToMM(hc.GetPoint(j).x),
                           pcbnew.ToMM(hc.GetPoint(j).y))
                          for j in range(hc.PointCount())])
        out.append((pts, holes))
    return out

def inside(pt, poly):
    x, y = pt
    c = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            if x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                c = not c
    return c

def touches(pt, islands):
    hits = []
    for idx, (pts, holes) in enumerate(islands):
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        if not (min(xs) - 0.6 <= pt[0] <= max(xs) + 0.6 and
                min(ys) - 0.6 <= pt[1] <= max(ys) + 0.6):
            continue
        if inside(pt, pts) and not any(inside(pt, h) for h in holes):
            hits.append(idx)
    return hits

zones = [z for z in board.Zones() if z.GetNetname() == 'GND'
         and z.IsOnLayer(LAY)]
print(f'{len(zones)} GND zones on {LAYN}')
for zi, z in enumerate(zones):
    polys = z.GetFilledPolysList(LAY)
    isl = outlines(polys)
    # only islands intersecting the box
    keep = []
    for idx, (pts, holes) in enumerate(isl):
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        if max(xs) >= X0 and min(xs) <= X1 and \
                max(ys) >= Y0 and min(ys) <= Y1:
            keep.append(idx)
    print(f' zone{zi}: {len(isl)} islands total, {len(keep)} in box')
    members = {}
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname() != 'GND':
                continue
            p = pcbnew.ToMM(pad.GetPosition())
            if not in_box(*p):
                continue
            h = touches(p, isl)
            for idx in h:
                if idx in keep:
                    members.setdefault(idx, []).append(
                        f'{fp.GetReference()}.{pad.GetNumber()}')
    for t in board.GetTracks():
        if t.GetNetname() != 'GND' or \
                not isinstance(t, pcbnew.PCB_VIA):
            continue
        p = pcbnew.ToMM(t.GetPosition())
        if not in_box(*p):
            continue
        h = touches(p, isl)
        for idx in h:
            if idx in keep:
                members.setdefault(idx, []).append(
                    f'via@({p[0]:.2f},{p[1]:.2f})')
    for idx in keep:
        pts = isl[idx][0]
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        print(f'   island{idx}: bbox x[{min(xs):.2f},{max(xs):.2f}] '
              f'y[{min(ys):.2f},{max(ys):.2f}] members: '
              f'{sorted(members.get(idx, []))}')

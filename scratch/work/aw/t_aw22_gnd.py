"""t_aw22: GND F-zone fill islands on exp241 vs esc; XO anchor check;
stitch-via size survey."""
import wx
_app = wx.App(False)
import pcbnew


def islands(board_path):
    b = pcbnew.LoadBoard(board_path)
    F = pcbnew.F_Cu
    zone = None
    for z in b.Zones():
        if z.GetNetname() == 'GND' and z.IsOnLayer(F):
            zone = z
            break
    fps = zone.GetFilledPolysList(F)
    n = fps.OutlineCount()
    print(f'{board_path}: GND F zone outlines={n}', flush=True)
    # tying items: GND pads (F), GND vias (any), GND F track endpoints
    ties = []
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname() == 'GND':
                ties.append(pcbnew.ToMM(p.GetPosition()))
    for t in b.GetTracks():
        if t.GetNetname() != 'GND':
            continue
        if isinstance(t, pcbnew.PCB_VIA):
            ties.append(pcbnew.ToMM(t.GetPosition()))
        elif t.GetLayer() == F:
            ties.append(pcbnew.ToMM(t.GetStart()))
            ties.append(pcbnew.ToMM(t.GetEnd()))
    orphans = []
    for i in range(n):
        out = fps.Outline(i)
        pts = [(pcbnew.ToMM(out.CPoint(k).x),
                pcbnew.ToMM(out.CPoint(k).y))
               for k in range(out.PointCount())]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        # ray-casting point in polygon
        cnt = 0
        for (tx, ty) in ties:
            inside = False
            m = len(pts)
            for k in range(m):
                x1, y1 = pts[k]
                x2, y2 = pts[(k + 1) % m]
                if (y1 > ty) != (y2 > ty):
                    xin = (x2 - x1) * (ty - y1) / (y2 - y1) + x1
                    if tx < xin:
                        inside = not inside
            if inside:
                cnt += 1
        cx = sum(xs) / len(xs)
        cy = sum(ys) / len(ys)
        print(f'  island {i}: bbox x[{min(xs):.2f},{max(xs):.2f}] '
              f'y[{min(ys):.2f},{max(ys):.2f}] ties={cnt} '
              f'centroid=({cx:.2f},{cy:.2f})', flush=True)
        if cnt == 0:
            orphans.append((i, (round(min(xs), 2), round(max(xs), 2),
                                round(min(ys), 2), round(max(ys), 2))))
    print('  ORPHANS:', orphans, flush=True)
    return b


b241 = islands('hw/pdlvds_rx.exp241.kicad_pcb')
besc = islands('hw/pdlvds_rx.exp241esc.kicad_pcb')

print('--- XO anchor at (72.625,24.625) in esc ---', flush=True)
for t in besc.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        continue
    a = pcbnew.ToMM(t.GetStart())
    bb = pcbnew.ToMM(t.GetEnd())
    for (px, py) in (a, bb):
        if abs(px - 72.625) < 0.06 and abs(py - 24.625) < 0.06:
            print(f'   seg {t.GetNetname()} L{t.GetLayer()} '
                  f'({a[0]:.3f},{a[1]:.3f})->({bb[0]:.3f},{bb[1]:.3f}) '
                  f'w{pcbnew.ToMM(t.GetWidth()):.2f}', flush=True)
for t in besc.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        p = pcbnew.ToMM(t.GetPosition())
        if abs(p[0] - 72.625) < 0.5 and abs(p[1] - 24.625) < 0.5:
            print(f'   via {t.GetNetname()} ({p[0]:.3f},{p[1]:.3f}) '
                  f'd{pcbnew.ToMM(t.GetWidth()):.2f}', flush=True)
for fp in besc.GetFootprints():
    for p in fp.Pads():
        pp = pcbnew.ToMM(p.GetPosition())
        if abs(pp[0] - 72.625) < 0.8 and abs(pp[1] - 24.625) < 0.8:
            print(f'   pad {fp.GetReference()}.{p.GetNumber()} '
                  f'{p.GetNetname()} ({pp[0]:.3f},{pp[1]:.3f})', flush=True)

print('--- GND via size census (exp241) ---', flush=True)
from collections import Counter
c = Counter()
for t in b241.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == 'GND':
        c[(round(pcbnew.ToMM(t.GetWidth()), 2),
           round(pcbnew.ToMM(t.GetDrill()), 2))] += 1
print('  ', dict(c), flush=True)
print('T_AW22 COMPLETE', flush=True)

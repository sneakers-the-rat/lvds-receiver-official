import re, math
import wx
_app = wx.App(False)
import pcbnew

txt = open('hw/pdlvds_rx.exp272.kicad_pcb').read()
polys = []
for zm in re.finditer(r'\(zone\b', txt):
    block = txt[zm.start():zm.start() + 600000]
    nm = re.search(r'\(net_name "([^"]*)"\)', block[:2000])
    if not nm or nm.group(1) != 'GND':
        continue
    for fm in re.finditer(r'\(filled_polygon\s*\(layer "F\.Cu"\)\s*\(pts(.*?)\)\s*\)', block, re.S):
        pts = [(float(x), float(y)) for x, y in re.findall(r'\(xy (-?[\d.]+) (-?[\d.]+)\)', fm.group(1))]
        if len(pts) >= 3:
            polys.append(pts)

def seg_pt(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
    q = (ax + t * dx, ay + t * dy)
    return math.hypot(px - q[0], py - q[1]), q

def poly_dist(p1, p2):
    best = (9e9, None, None)
    for a, b in zip(p1, p1[1:] + p1[:1]):
        for c in p2:
            d, q = seg_pt(c, a, b)
            if d < best[0]: best = (d, q, c)
    return best

# C19 island: the one containing (82.03,11.85) bbox region
c19 = None
for p in polys:
    xs = [q[0] for q in p]; ys = [q[1] for q in p]
    if min(xs) > 80.5 and max(xs) < 83.0 and min(ys) > 9.5 and max(ys) < 13.5:
        c19 = p
assert c19 is not None
res = []
for p in polys:
    if p is c19: continue
    xs = [q[0] for q in p]; ys = [q[1] for q in p]
    if max(xs) < 79 or min(xs) > 84 or max(ys) < 8 or min(ys) > 14: continue
    d, q1, q2 = poly_dist(c19, p)
    res.append((d, q1, q2, (min(xs), max(xs), min(ys), max(ys))))
res.sort(key=lambda z: z[0])
for d, q1, q2, bb in res[:4]:
    print(f'gap {d:.3f} between C19 fill {q1} and other fill {q2} (other bbox x[{bb[0]:.2f},{bb[1]:.2f}] y[{bb[2]:.2f},{bb[3]:.2f}])')

gx = (res[0][1][0] + res[0][2][0]) / 2; gy = (res[0][1][1] + res[0][2][1]) / 2
print(f'gap midpoint: ({gx:.2f},{gy:.2f})')
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp272.kicad_pcb')
print('items within 0.6 of the gap midpoint:')
for t in b.GetTracks():
    a = t.GetStart(); e = t.GetEnd()
    d, q = seg_pt((gx, gy), (a.x/1e6, a.y/1e6), (e.x/1e6, e.y/1e6))
    if d < 0.6:
        kind = 'via' if t.Type() == pcbnew.PCB_VIA_T else 'trk'
        print(f'  {t.GetNetname()} {kind} {b.GetLayerName(t.GetLayer())} ({a.x/1e6:.2f},{a.y/1e6:.2f})->({e.x/1e6:.2f},{e.y/1e6:.2f}) w={t.GetWidth()/1e6:.2f} d={d:.3f}')
for fp in b.GetFootprints():
    for pad in fp.Pads():
        if not pad.IsOnLayer(pcbnew.F_Cu): continue
        p = pad.GetPosition()
        if abs(p.x/1e6 - gx) < 1.1 and abs(p.y/1e6 - gy) < 1.1:
            print(f'  PAD {fp.GetReference()}.{pad.GetNumber()} {pad.GetNetname()} at ({p.x/1e6:.2f},{p.y/1e6:.2f})')

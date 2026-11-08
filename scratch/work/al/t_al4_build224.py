"""t_al4: GND U6.38 island heal via +3V3D U6.39 dive re-lay.
Design (gated in t_al3_gate.py, all margins positive, exact model):
the island's south fence is +3V3D's F diagonal (74.25,3.662)->
(73.625,3.375). Rip it + the w0.2 landing + shorten the w0.6 trunk
to end at (72.875,3.375); U6.39 re-feeds via a dive at (74.25,3.50)
on its kept stub, an In2 jog (74.25,3.50)->(72.875,3.375) w0.25 and
a via at the new trunk end. The GND zone (clearance 0.25, min
thickness 0.2) then has a >=0.29 mm channel south down the pad
column. Usage: t_al4_build224.py in out"""
import sys
sys.path.insert(0, 'hw')
sys.path.insert(0, 'scratch/work/ai')
import wx
_app = wx.App(False)
import pcbnew
from t_ai_lib import load_items, pt_margin, seg_margin, in_box_pool, fmt_it

SRC, OUT = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(SRC)
items = load_items(board)

RIP = [((74.25, 3.662), (73.625, 3.375)),
       ((73.625, 3.375), (73.375, 3.375)),
       ((72.625, 3.375), (73.375, 3.375))]

def is_rip(it):
    if it[0] != 'seg' or it[1] != '+3V3D':
        return False
    d = it[2]
    a, b = (d[0], d[1]), (d[2], d[3])
    return any((abs(a[0]-r[0][0]) < 0.01 and abs(a[1]-r[0][1]) < 0.01
                and abs(b[0]-r[1][0]) < 0.01 and abs(b[1]-r[1][1]) < 0.01) or
               (abs(b[0]-r[0][0]) < 0.01 and abs(b[1]-r[0][1]) < 0.01
                and abs(a[0]-r[1][0]) < 0.01 and abs(a[1]-r[1][1]) < 0.01)
               for r in RIP)

statics = {li: [it for it in items[li] if not is_rip(it)] for li in range(3)}
pool = in_box_pool(statics, (70.0, 77.0, 0.5, 7.0), pad=1.2)
ok = True
for (x, y) in [(74.25, 3.50), (72.875, 3.375)]:
    for li in range(3):
        m, w = pt_margin(li, x, y, '+3V3D', 0.25, pool[li])
        print(f'  gate via ({x},{y}) L{li}: {m:+.3f} worst {fmt_it(w)}')
        ok &= m >= 0
for li, a, b, hw_ in [(1, (74.25, 3.50), (72.875, 3.375), 0.125),
                      (0, (72.625, 3.375), (72.875, 3.375), 0.30)]:
    m, w = seg_margin(li, a, b, '+3V3D', hw_, pool[li])
    print(f'  gate seg L{li} {a}->{b}: {m:+.3f} worst {fmt_it(w)}')
    ok &= m >= 0
if not ok:
    print('GATES FAIL -- no build')
    sys.exit(1)

codes = {}
for t in board.GetTracks():
    codes[t.GetNetname()] = t.GetNetCode()
for fp in board.GetFootprints():
    for p in fp.Pads():
        if p.GetNetname():
            codes[p.GetNetname()] = p.GetNetCode()

nrip = 0
for t in list(board.GetTracks()):
    if isinstance(t, pcbnew.PCB_VIA) or t.GetNetname() != '+3V3D':
        continue
    a = (round(pcbnew.ToMM(t.GetStart())[0], 3), round(pcbnew.ToMM(t.GetStart())[1], 3))
    b = (round(pcbnew.ToMM(t.GetEnd())[0], 3), round(pcbnew.ToMM(t.GetEnd())[1], 3))
    if any((a == r[0] and b == r[1]) or (a == r[1] and b == r[0]) for r in RIP):
        board.Remove(t)
        nrip += 1
print(f'ripped {nrip} (expect 3)')
assert nrip == 3

def add_seg(a, b, w, layer):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(a[0]), pcbnew.FromMM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(b[0]), pcbnew.FromMM(b[1])))
    t.SetWidth(pcbnew.FromMM(w))
    t.SetLayer(layer)
    t.SetNetCode(codes['+3V3D'])
    board.Add(t)

def add_via(x, y):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
    v.SetWidth(pcbnew.FromMM(0.5))
    v.SetDrill(pcbnew.FromMM(0.3))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNetCode(codes['+3V3D'])
    board.Add(v)

add_seg((72.625, 3.375), (72.875, 3.375), 0.6, pcbnew.F_Cu)
add_via(74.25, 3.50)
add_seg((74.25, 3.50), (72.875, 3.375), 0.25, pcbnew.In2_Cu)
add_via(72.875, 3.375)

filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(OUT)
print('saved', OUT)

# reload census + net-name verify + island test
b2 = pcbnew.LoadBoard(OUT)
from collections import Counter
c = Counter()
for t in b2.GetTracks():
    c[t.GetNetname()] += 1
print('reload census: +3V3D items', c['+3V3D'], ' GND items', c['GND'])
for z in b2.Zones():
    if z.GetNetname() == 'GND' and z.IsOnLayer(pcbnew.F_Cu):
        polys = z.GetFilledPolysList(pcbnew.F_Cu)
        print('GND F fill outlines after refill:', polys.OutlineCount())
        for i in range(polys.OutlineCount()):
            o = polys.Outline(i)
            pts = [(pcbnew.ToMM(o.GetPoint(i2).x), pcbnew.ToMM(o.GetPoint(i2).y))
                   for i2 in range(o.PointCount())]
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
            if min(xs) < 73.75 < max(xs) and min(ys) < 4.662 < max(ys):
                print(f'  outline{i} contains U6.38 pad centre: bbox x[{min(xs):.2f},{max(xs):.2f}] y[{min(ys):.2f},{max(ys):.2f}] npts={len(pts)}')

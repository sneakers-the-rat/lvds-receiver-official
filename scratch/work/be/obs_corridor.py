"""obs_corridor: census for the user's USB_RST design (dive at
U7.9 -> In2 near-straight run north -> surface beside U6.40).
Dumps: U7 pads (west+south rows), every In2 track intersecting
strip x[73.2,75.8] y[3.5,17.5], every via in x[72.8,76.2]
y[3.5,18.6], every F/B track in the dive pocket x[72.8,75.6]
y[15.2,19.6], and pads intersecting that pocket.
"""
import wx
wx.App(False)
import pcbnew

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp257.kicad_pcb')
LN = {pcbnew.F_Cu: 'F', pcbnew.In1_Cu: 'In1', pcbnew.In2_Cu: 'In2',
      pcbnew.B_Cu: 'B'}


def mm(v):
    return v / 1e6


def seg_hits_strip(a, c, x0, x1, y0, y1):
    # segment vs box intersection test (endpoint-in or crossing)
    if x0 <= a[0] <= x1 and y0 <= a[1] <= y1:
        return True
    if x0 <= c[0] <= x1 and y0 <= c[1] <= y1:
        return True
    # bounding-box overlap (sufficient for a census dump)
    return not (max(a[0], c[0]) < x0 or min(a[0], c[0]) > x1 or
                max(a[1], c[1]) < y0 or min(a[1], c[1]) > y1)


print('==== U7 pads ====')
for fp in b.GetFootprints():
    if fp.GetReference() == 'U7':
        for p in fp.Pads():
            bb = p.GetBoundingBox()
            print(f"U7.{p.GetNumber():>3s} {p.GetNetname():12s} "
                  f"rect x[{mm(bb.GetLeft()):.3f},{mm(bb.GetRight()):.3f}] "
                  f"y[{mm(bb.GetTop()):.3f},{mm(bb.GetBottom()):.3f}]")

print('==== In2 tracks hitting strip x[73.2,75.8] y[3.5,17.5] ====')
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T or t.GetLayer() != pcbnew.In2_Cu:
        continue
    s, e = t.GetStart(), t.GetEnd()
    a, c = (mm(s.x), mm(s.y)), (mm(e.x), mm(e.y))
    if seg_hits_strip(a, c, 73.2, 75.8, 3.5, 17.5):
        print(f"{t.GetNetname():12s} In2 ({a[0]:.3f},{a[1]:.3f})"
              f"->({c[0]:.3f},{c[1]:.3f}) w={mm(t.GetWidth()):.3f}")

print('==== vias in x[72.8,76.2] y[3.5,18.6] ====')
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        p = t.GetPosition()
        x, y = mm(p.x), mm(p.y)
        if 72.8 <= x <= 76.2 and 3.5 <= y <= 18.6:
            print(f"{t.GetNetname():12s} VIA ({x:.3f},{y:.3f}) "
                  f"dia={mm(t.GetWidth()):.2f}")

print('==== F/B tracks in dive pocket x[72.8,75.6] y[15.2,19.6] ====')
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        continue
    if LN[t.GetLayer()] not in ('F', 'B'):
        continue
    s, e = t.GetStart(), t.GetEnd()
    a, c = (mm(s.x), mm(s.y)), (mm(e.x), mm(e.y))
    if seg_hits_strip(a, c, 72.8, 75.6, 15.2, 19.6):
        print(f"{t.GetNetname():12s} {LN[t.GetLayer()]:2s} "
              f"({a[0]:.3f},{a[1]:.3f})->({c[0]:.3f},{c[1]:.3f}) "
              f"w={mm(t.GetWidth()):.3f}")

print('==== pads in dive pocket ====')
for fp in b.GetFootprints():
    for p in fp.Pads():
        bb = p.GetBoundingBox()
        r = (mm(bb.GetLeft()), mm(bb.GetTop()),
             mm(bb.GetRight()), mm(bb.GetBottom()))
        if r[0] <= 75.6 and r[2] >= 72.8 and r[1] <= 19.6 and r[3] >= 15.2:
            print(f"{fp.GetReference()}.{p.GetNumber():>3s} "
                  f"{p.GetNetname():12s} rect x[{r[0]:.3f},{r[2]:.3f}] "
                  f"y[{r[1]:.3f},{r[3]:.3f}]")

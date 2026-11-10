"""t_ba46: BUILD exp253 v3.
Changes vs v2 (t_ba44):
- C22 -> (77.17,9.95) (+0.02 east: XO pad clearance was
  0.190-0.197, needs >=0.200).
- C22 refdes/value: absolute positions + angle restored
  from exp252 after the move (silk state proven clean).
- STP rip v3 = v2 rules + corridor rule: B segs with
  centre cy in (-1.45,0.7) and cx >= 74.925 (the old
  southern chain east of the (74.90,-1.30) T-join, which
  the new runs[4] lands on). Expect 287 + ~65 = ~352.
Everything else as t_ba44 (tail rip 2, STP7 emission with
runs[0] first point trimmed, hop, GND stub+via, refill)."""
import pcbnew, json

SRC = 'hw/pdlvds_rx.exp252.kicad_pcb'
OUT = 'hw/pdlvds_rx.exp253.kicad_pcb'
MM = pcbnew.ToMM
NM = 1000000.0
F, I2, Bk = pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu
LAY = {0: F, 1: I2, 2: Bk}
GNDV = (76.975, 9.6)
ST7 = json.load(open('scratch/work/ba/design_stp_south7.json'))


def census(b):
    c = {}
    for t in b.GetTracks():
        n = t.GetNetname()
        c[n] = c.get(n, 0) + 1
    return c


b = pcbnew.LoadBoard(SRC)
before = census(b)
codes = {n: b.GetNetcodeFromNetname(n)
         for n in ('ULPI_STP', 'PHY_1V8', 'GND')}

for fp in b.GetFootprints():
    if fp.GetReference() == 'C22':
        ref_pos = fp.Reference().GetPosition()
        val_pos = fp.Value().GetPosition()
        fp.SetPosition(pcbnew.VECTOR2I(int(77.17 * NM), int(9.95 * NM)))
        fp.SetOrientationDegrees(90)
        pads = {}
        for p in fp.Pads():
            pads[p.GetNetname()] = (MM(p.GetPosition().x),
                                    MM(p.GetPosition().y))
        print('C22 pads:', pads)
        assert abs(pads['PHY_1V8'][0] - 77.17) < 0.02
        assert abs(pads['PHY_1V8'][1] - 10.43) < 0.02
        assert abs(pads['GND'][1] - 9.47) < 0.02
        _a0 = pcbnew.EDA_ANGLE(0, pcbnew.DEGREES_T)
        fp.Reference().SetPosition(ref_pos)
        fp.Reference().SetTextAngle(_a0)
        fp.Value().SetPosition(val_pos)
        fp.Value().SetTextAngle(_a0)
        break

tracks = list(b.GetTracks())


def centre(t):
    if t.Type() == pcbnew.PCB_VIA_T:
        return (MM(t.GetPosition().x), MM(t.GetPosition().y))
    return ((MM(t.GetStart().x) + MM(t.GetEnd().x)) / 2,
            (MM(t.GetStart().y) + MM(t.GetEnd().y)) / 2)


victims = []
for t in tracks:
    if t.GetNetname() != 'ULPI_STP':
        continue
    cx, cy = centre(t)
    if 75.5 <= cx <= 78.5 and 7.0 <= cy <= 14.0 \
            and not (cy > 13.55 and cx < 76.0):
        victims.append(t)
    elif 0.65 < cy < 7.5 and cx > 72.0:
        victims.append(t)
    elif t.Type() == pcbnew.PCB_TRACE_T and t.GetLayer() == Bk \
            and -1.45 < cy < 0.7 and cx >= 74.925:
        victims.append(t)
print('STP rip victims:', len(victims))
assert 345 <= len(victims) <= 360, len(victims)
for t in victims:
    b.Remove(t)


def find_seg(layer, net, a, bp):
    out = []
    for t in tracks:
        if t.Type() != pcbnew.PCB_TRACE_T:
            continue
        if t.GetNetname() != net or t.GetLayer() != layer:
            continue
        s = (MM(t.GetStart().x), MM(t.GetStart().y))
        e = (MM(t.GetEnd().x), MM(t.GetEnd().y))
        if (abs(s[0] - a[0]) < 0.01 and abs(s[1] - a[1]) < 0.01
                and abs(e[0] - bp[0]) < 0.01 and abs(e[1] - bp[1]) < 0.01) \
           or (abs(s[0] - bp[0]) < 0.01 and abs(s[1] - bp[1]) < 0.01
               and abs(e[0] - a[0]) < 0.01 and abs(e[1] - a[1]) < 0.01):
            out.append(t)
    return out


tail = []
for a, bp in [((71.375, 17.625), (71.725, 17.75)),
              ((71.725, 17.75), (71.725, 18.0))]:
    v = find_seg(F, 'PHY_1V8', a, bp)
    assert len(v) == 1, (a, bp, len(v))
    tail += v
for t in tail:
    b.Remove(t)
print('PHY tail victims:', len(tail))


def add_seg(net, layer, a, bp, w=0.20):
    t = pcbnew.PCB_TRACK(b)
    t.SetNetCode(codes[net])
    t.SetLayer(layer)
    t.SetStart(pcbnew.VECTOR2I(int(round(a[0] * NM)),
                               int(round(a[1] * NM))))
    t.SetEnd(pcbnew.VECTOR2I(int(round(bp[0] * NM)),
                             int(round(bp[1] * NM))))
    t.SetWidth(int(round(w * NM)))
    b.Add(t)


def add_via(net, x, y):
    v = pcbnew.PCB_VIA(b)
    v.SetNetCode(codes[net])
    v.SetPosition(pcbnew.VECTOR2I(int(round(x * NM)),
                                  int(round(y * NM))))
    v.SetWidth(int(0.5 * NM))
    v.SetDrill(int(0.3 * NM))
    v.SetLayerPair(F, Bk)
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    b.Add(v)


for vx, vy in ST7['vias']:
    add_via('ULPI_STP', vx, vy)
nseg = 0
for ri, run in enumerate(ST7['runs']):
    lay = LAY[run['layer']]
    pts = [tuple(p) for p in run['pts']]
    if ri == 0:
        pts = pts[1:]
    for a, bp in zip(pts, pts[1:]):
        if abs(a[0] - bp[0]) < 1e-9 and abs(a[1] - bp[1]) < 1e-9:
            continue
        add_seg('ULPI_STP', lay, a, bp)
        nseg += 1
print('STP7 segs added:', nseg, 'vias:', len(ST7['vias']))

add_seg('PHY_1V8', F, (77.17, 10.43), (77.90, 10.08))
add_seg('GND', F, (77.17, 9.47), GNDV)
add_via('GND', GNDV[0], GNDV[1])
print('hop + GND tie added')

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(OUT)
b2 = pcbnew.LoadBoard(OUT)
after = census(b2)
for n in sorted(set(before) | set(after)):
    if before.get(n, 0) != after.get(n, 0):
        print(f'census diff {n}: {before.get(n, 0)} -> {after.get(n, 0)}')
print('saved', OUT)

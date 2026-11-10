"""t_az44: BUILD exp252 = exp251 + PHY_1V8A notch re-lay v2 only.
Rip: via (75.7375,10.75); F seg (75.72,11.0)->(75.7375,10.75);
B seg (75.7375,10.75)->(75.30,11.35).
Add: via (75.30,10.30) (same d/drill as ripped via);
F segs (75.72,11.0)->(75.48,10.68)->(75.30,10.30);
B segs (75.30,10.30)->(75.05,10.95)->(74.90,11.75)
(widths copied from the ripped segs). Zone refill, save,
reload + per-net item census diff vs exp251.
"""
import pcbnew

SRC = 'hw/pdlvds_rx.exp251.kicad_pcb'
OUT = 'hw/pdlvds_rx.exp252.kicad_pcb'
MM = pcbnew.ToMM
NM = 1000000.0


def census(b):
    c = {}
    for t in b.GetTracks():
        n = t.GetNetname()
        c[n] = c.get(n, 0) + 1
    return c


b = pcbnew.LoadBoard(SRC)
before = census(b)
codes = {}
for name in ('PHY_1V8A',):
    codes[name] = b.GetNetcodeFromNetname(name)
print('netcodes:', codes)

tracks = list(b.GetTracks())


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


def find_via(net, x, y):
    out = []
    for t in tracks:
        if t.Type() != pcbnew.PCB_VIA_T:
            continue
        if t.GetNetname() != net:
            continue
        p = (MM(t.GetPosition().x), MM(t.GetPosition().y))
        if abs(p[0] - x) < 0.01 and abs(p[1] - y) < 0.01:
            out.append(t)
    return out


F = pcbnew.F_Cu
Bk = pcbnew.B_Cu
vias = find_via('PHY_1V8A', 75.7375, 10.75)
assert len(vias) == 1, f'notch via count {len(vias)}'
old_via = vias[0]
vd = MM(old_via.GetWidth())
vdrill = MM(old_via.GetDrillValue().x) if hasattr(
    old_via.GetDrillValue(), 'x') else MM(old_via.GetDrill())
print(f'old via d={vd} drill={vdrill}')
s1 = find_seg(F, 'PHY_1V8A', (75.72, 11.0), (75.7375, 10.75))
s2 = find_seg(Bk, 'PHY_1V8A', (75.7375, 10.75), (75.30, 11.35))
s3 = find_seg(Bk, 'PHY_1V8A', (75.30, 11.35), (74.90, 11.75))
assert len(s1) == 1 and len(s2) == 1 and len(s3) == 1, \
    (len(s1), len(s2), len(s3))
wF = MM(s1[0].GetWidth())
wB = MM(s2[0].GetWidth())
print(f'stub widths F={wF} B={wB}')
for t in vias + s1 + s2 + s3:
    b.Remove(t)


def add_seg(net, layer, a, bp, w):
    t = pcbnew.PCB_TRACK(b)
    t.SetNetCode(codes[net])
    t.SetLayer(layer)
    t.SetStart(pcbnew.VECTOR2I(int(a[0] * NM), int(a[1] * NM)))
    t.SetEnd(pcbnew.VECTOR2I(int(bp[0] * NM), int(bp[1] * NM)))
    t.SetWidth(int(w * NM))
    b.Add(t)


def add_via(net, x, y):
    v = pcbnew.PCB_VIA(b)
    v.SetNetCode(codes[net])
    v.SetPosition(pcbnew.VECTOR2I(int(x * NM), int(y * NM)))
    v.SetWidth(int(vd * NM))
    v.SetDrill(int(vdrill * NM))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    b.Add(v)


add_via('PHY_1V8A', 75.30, 10.30)
add_seg('PHY_1V8A', F, (75.72, 11.0), (75.48, 10.68), wF)
add_seg('PHY_1V8A', F, (75.48, 10.68), (75.30, 10.30), wF)
add_seg('PHY_1V8A', Bk, (75.30, 10.30), (75.05, 10.95), wB)
add_seg('PHY_1V8A', Bk, (75.05, 10.95), (74.90, 11.75), wB)

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(OUT)
print('saved', OUT)

b2 = pcbnew.LoadBoard(OUT)
after = census(b2)
diff = {n: (before.get(n, 0), after.get(n, 0))
        for n in set(before) | set(after)
        if before.get(n, 0) != after.get(n, 0)}
print('census diff (net: before->after):', diff)
exp = {'PHY_1V8A': (before['PHY_1V8A'], before['PHY_1V8A'] + 2)}
print('expected PHY_1V8A delta (+3 added -3 ripped +... via same):',
      'before', before['PHY_1V8A'], 'after', after['PHY_1V8A'])
print('=== done ===')

"""t_bb13: BUILD pass 218 candidate exp254 -> exp255 (XI design v7).
Moves A (STP B descent east), B (CK In2 jog west), C (1V8A notch v3
via (74.99,10.28)), D (ULPI_DIR B re-lay), XI pocket via (75.80,10.28)
+ F leg to U7.28 centre + B ride via x74.25 / y13.1 / x75.7.
Victim counts asserted per move; widths read from victims;
zone refill; save; reload netname/count census."""
import wx
_app = wx.App(False)
import pcbnew

SRC = 'hw/pdlvds_rx.exp254.kicad_pcb'
DST = 'hw/pdlvds_rx.exp255.kicad_pcb'
b = pcbnew.LoadBoard(SRC)
MM = pcbnew.FromMM

def mm(v):
    return v / 1e6

NETS = ('ULPI_STP', 'ULPI_CK', 'PHY_1V8A', 'ULPI_DIR', 'XI')
NC = {n: b.GetNetcodeFromNetname(n) for n in NETS}
print('netcodes:', NC)

def census(tag):
    out = {}
    for t in b.GetTracks():
        n = t.GetNetname()
        if n in NETS:
            kind = 'via' if t.Type() == pcbnew.PCB_VIA_T else 'trk'
            out[(n, kind)] = out.get((n, kind), 0) + 1
    print(tag, out)
    return out

base = census('base:')

def find_tracks(net, layer, pred):
    nc = NC[net]
    return [t for t in list(b.GetTracks())
            if t.GetNetCode() == nc and t.Type() == pcbnew.PCB_TRACE_T
            and t.GetLayer() == layer and pred(t)]

def ends(t):
    s, e = t.GetStart(), t.GetEnd()
    return (mm(s.x), mm(s.y)), (mm(e.x), mm(e.y))

def near(p, q, tol=0.03):
    return abs(p[0] - q[0]) < tol and abs(p[1] - q[1]) < tol

def seg_between(net, layer, a, bb, tol=0.03):
    def pred(t):
        s, e = ends(t)
        return (near(s, a, tol) and near(e, bb, tol)) or \
               (near(s, bb, tol) and near(e, a, tol))
    return find_tracks(net, layer, pred)

def add_track(net, layer, a, bb, width):
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(MM(bb[0]), MM(bb[1])))
    t.SetWidth(MM(width))
    t.SetLayer(layer)
    t.SetNetCode(NC[net])
    b.Add(t)
    return t

def add_via(net, x, y, dia=0.5, drill=0.3):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    v.SetWidth(MM(dia))
    v.SetDrill(MM(drill))
    v.SetNetCode(NC[net])
    b.Add(v)
    return v

F, IN2, B = pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu

# ---- Move A: STP B descent east ----
def predA(t):
    s, e = ends(t)
    cx, cy = (s[0] + e[0]) / 2, (s[1] + e[1]) / 2
    return 75.9 <= cx <= 76.5 and 9.2 <= cy <= 13.5
vA = find_tracks('ULPI_STP', B, predA)
print(f'Move A victims: {len(vA)} (model expect 60)')
assert len(vA) == 60, 'Move A victim count mismatch — STOP'
wA = mm(vA[0].GetWidth())
for t in vA:
    b.Remove(t)
add_track('ULPI_STP', B, (76.44, 9.03), (76.45, 12.90), wA)
add_track('ULPI_STP', B, (76.45, 12.90), (76.05, 13.45), wA)

# ---- Move B: CK In2 vertical -> jog ----
vB = seg_between('ULPI_CK', IN2, (74.625, 13.5), (74.625, 6.375), tol=0.05)
print(f'Move B victims: {len(vB)} (expect 1)')
assert len(vB) == 1, 'Move B victim mismatch — STOP'
wB = mm(vB[0].GetWidth())
b.Remove(vB[0])
for a, bb in (((74.625, 6.375), (74.625, 9.40)), ((74.625, 9.40), (74.32, 10.20)),
              ((74.32, 10.20), (74.625, 11.00)), ((74.625, 11.00), (74.625, 13.50))):
    add_track('ULPI_CK', IN2, a, bb, wB)

# ---- Move C: 1V8A notch v3 ----
vC1 = seg_between('PHY_1V8A', F, (75.72, 11.0), (75.45, 10.6))
vC2 = [t for t in find_tracks('PHY_1V8A', B, lambda t: near(ends(t)[0], (75.45, 10.6)) or near(ends(t)[1], (75.45, 10.6)))]
vC3 = [t for t in list(b.GetTracks())
       if t.GetNetCode() == NC['PHY_1V8A'] and t.Type() == pcbnew.PCB_VIA_T
       and near((mm(t.GetPosition().x), mm(t.GetPosition().y)), (75.45, 10.6))]
print(f'Move C victims: stub {len(vC1)}, head {len(vC2)}, via {len(vC3)} (expect 1/1/1)')
assert len(vC1) == 1 and len(vC2) == 1 and len(vC3) == 1, 'Move C mismatch — STOP'
wCF, wCB = mm(vC1[0].GetWidth()), mm(vC2[0].GetWidth())
for t in vC1 + vC2 + vC3:
    b.Remove(t)
add_via('PHY_1V8A', 74.99, 10.28)
add_track('PHY_1V8A', F, (75.72, 11.0), (74.99, 10.28), wCF)
add_track('PHY_1V8A', B, (74.99, 10.28), (75.00, 11.50), wCB)

# ---- Move D: ULPI_DIR B re-lay ----
vD = seg_between('ULPI_DIR', B, (75.5, 17.521), (71.375, 19.125), tol=0.05)
print(f'Move D victims: {len(vD)} (expect 1)')
assert len(vD) == 1, 'Move D victim mismatch — STOP'
wD = mm(vD[0].GetWidth())
b.Remove(vD[0])
add_track('ULPI_DIR', B, (75.5, 17.521), (74.6, 18.1), wD)
add_track('ULPI_DIR', B, (74.6, 18.1), (71.375, 19.125), wD)

# ---- XI: pocket via + F leg + B ride ----
xiB = [t for t in list(b.GetTracks())
       if t.GetNetCode() == NC['XI'] and t.Type() == pcbnew.PCB_TRACE_T
       and t.GetLayer() == B]
wXI = mm(xiB[0].GetWidth())
xiF = [t for t in list(b.GetTracks())
       if t.GetNetCode() == NC['XI'] and t.Type() == pcbnew.PCB_TRACE_T
       and t.GetLayer() == F]
wXIF = mm(xiF[0].GetWidth()) if xiF else wXI
print(f'XI widths: B {wXI}, F {wXIF}')
PV = (75.80, 10.28)
add_via('XI', PV[0], PV[1])
add_track('XI', F, PV, (76.18, 10.70), wXIF)
add_track('XI', F, (76.18, 10.70), (76.25, 11.5625), wXIF)
for a, bb in (((75.625, 18.625), (74.25, 18.62)), ((74.25, 18.62), (74.25, 13.10)),
              ((74.25, 13.10), (75.70, 13.10)), ((75.70, 13.10), (75.70, 11.20)),
              ((75.70, 11.20), PV)):
    add_track('XI', B, a, bb, wXI)

filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())
b.Save(DST)
print('saved', DST)

b2 = pcbnew.LoadBoard(DST)
def census2(tag):
    out = {}
    for t in b2.GetTracks():
        n = t.GetNetname()
        if n in NETS:
            kind = 'via' if t.Type() == pcbnew.PCB_VIA_T else 'trk'
            out[(n, kind)] = out.get((n, kind), 0) + 1
    print(tag, out)
    return out
now = census2('after:')
for k in sorted(set(base) | set(now)):
    if base.get(k) != now.get(k):
        print(f'  delta {k}: {base.get(k)} -> {now.get(k)}')

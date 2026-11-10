"""t_bb24: BUILD exp254 -> exp256 (XI pocket moves only, design v10
pocket half): A3 STP descent v3, B CK In2 jog, C notch v3,
XO final re-lay v3, XI pocket via (75.82,10.30) + F leg v3.
No DIR change, no XI ride (groute searches that next)."""
import wx
_app = wx.App(False)
import pcbnew

SRC = 'hw/pdlvds_rx.exp254.kicad_pcb'
DST = 'hw/pdlvds_rx.exp256.kicad_pcb'
b = pcbnew.LoadBoard(SRC)
MM = pcbnew.FromMM

def mm(v):
    return v / 1e6

NETS = ('ULPI_STP', 'ULPI_CK', 'PHY_1V8A', 'ULPI_DIR', 'XO', 'XI')
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

# ---- Move A3: STP B descent v3 ----
def predA(t):
    s, e = ends(t)
    cx, cy = (s[0] + e[0]) / 2, (s[1] + e[1]) / 2
    return 75.9 <= cx <= 76.5 and 9.2 <= cy <= 13.5
vA = find_tracks('ULPI_STP', B, predA)
print(f'Move A victims: {len(vA)} (expect 60)')
assert len(vA) == 60, 'Move A victim count mismatch'
wA = mm(vA[0].GetWidth())
for t in vA:
    b.Remove(t)
add_track('ULPI_STP', B, (76.44, 9.03), (76.42, 9.50), wA)
add_track('ULPI_STP', B, (76.42, 9.50), (76.425, 12.90), wA)
add_track('ULPI_STP', B, (76.425, 12.90), (76.05, 13.45), wA)

# ---- Move B: CK In2 jog ----
vB = seg_between('ULPI_CK', IN2, (74.625, 13.5), (74.625, 6.375), tol=0.05)
print(f'Move B victims: {len(vB)} (expect 1)')
assert len(vB) == 1, 'Move B victim mismatch'
wB = mm(vB[0].GetWidth())
b.Remove(vB[0])
for a, bb in (((74.625, 6.375), (74.625, 9.40)), ((74.625, 9.40), (74.32, 10.20)),
              ((74.32, 10.20), (74.625, 11.00)), ((74.625, 11.00), (74.625, 13.50))):
    add_track('ULPI_CK', IN2, a, bb, wB)

# ---- Move C: notch v3 ----
vC1 = seg_between('PHY_1V8A', F, (75.72, 11.0), (75.45, 10.6))
vC2 = [t for t in find_tracks('PHY_1V8A', B, lambda t: near(ends(t)[0], (75.45, 10.6)) or near(ends(t)[1], (75.45, 10.6)))]
vC3 = [t for t in list(b.GetTracks())
       if t.GetNetCode() == NC['PHY_1V8A'] and t.Type() == pcbnew.PCB_VIA_T
       and near((mm(t.GetPosition().x), mm(t.GetPosition().y)), (75.45, 10.6))]
print(f'Move C victims: stub {len(vC1)}, head {len(vC2)}, via {len(vC3)} (expect 1/1/1)')
assert len(vC1) == 1 and len(vC2) == 1 and len(vC3) == 1, 'Move C mismatch'
wCF, wCB = mm(vC1[0].GetWidth()), mm(vC2[0].GetWidth())
for t in vC1 + vC2 + vC3:
    b.Remove(t)
add_via('PHY_1V8A', 74.99, 10.28)
add_track('PHY_1V8A', F, (75.72, 11.0), (74.99, 10.28), wCF)
add_track('PHY_1V8A', B, (74.99, 10.28), (75.00, 11.50), wCB)

# ---- XO re-lay v3 ----
def predX(t):
    s, e = ends(t)
    for p in (s, e):
        if abs(p[0] - 76.55) < 0.03 and p[1] >= 10.44:
            return True
    return near(s, (76.5, 10.75)) or near(e, (76.5, 10.75))
vX = find_tracks('XO', F, predX)
print(f'XO victims: {len(vX)} (expect 8)')
assert len(vX) == 8, 'XO victim mismatch'
wX = mm(vX[0].GetWidth())
for t in vX:
    b.Remove(t)
add_track('XO', F, (76.55, 10.40), (76.56, 10.80), wX)
add_track('XO', F, (76.56, 10.80), (76.725, 11.15), wX)

# ---- XI pocket via + F leg v3 ----
xiF = [t for t in list(b.GetTracks())
       if t.GetNetCode() == NC['XI'] and t.Type() == pcbnew.PCB_TRACE_T
       and t.GetLayer() == F]
wXIF = mm(xiF[0].GetWidth())
PV = (75.82, 10.30)
add_via('XI', PV[0], PV[1])
add_track('XI', F, PV, (76.18, 10.94), wXIF)
add_track('XI', F, (76.18, 10.94), (76.25, 11.5625), wXIF)

filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())
b.Save(DST)
print('saved', DST)

b2 = pcbnew.LoadBoard(DST)
now = {}
for t in b2.GetTracks():
    n = t.GetNetname()
    if n in NETS:
        kind = 'via' if t.Type() == pcbnew.PCB_VIA_T else 'trk'
        now[(n, kind)] = now.get((n, kind), 0) + 1
print('after:', now)
for k in sorted(set(base) | set(now)):
    if base.get(k) != now.get(k):
        print(f'  delta {k}: {base.get(k)} -> {now.get(k)}')

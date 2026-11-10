"""t_ba3: BUILD prep252a = exp252 + az PHY design placed on-board
(x77.15 loop + design_phy_astar4 journey + F tail rip), with ALL
ULPI_STP tracks/vias ripped (groute will re-plan U7.13->U6.26).
Asserts victim counts on the board itself. Zone refill, save,
reload + per-net census diff vs exp252 (save-rename guard)."""
import pcbnew, json

SRC = 'hw/pdlvds_rx.exp252.kicad_pcb'
OUT = 'scratch/work/ba/prep252a.kicad_pcb'
MM = pcbnew.ToMM
NM = 1000000.0
F, I2, Bk = pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu
LAY = {0: F, 1: I2, 2: Bk}


def census(b):
    c = {}
    for t in b.GetTracks():
        n = t.GetNetname()
        c[n] = c.get(n, 0) + 1
    return c


b = pcbnew.LoadBoard(SRC)
before = census(b)
codes = {n: b.GetNetcodeFromNetname(n)
         for n in ('ULPI_STP', 'PHY_1V8')}
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


# ---- rip ALL ULPI_STP tracks + vias ----
stp = [t for t in tracks if t.GetNetname() == 'ULPI_STP']
nstp_seg = sum(1 for t in stp if t.Type() == pcbnew.PCB_TRACE_T)
nstp_via = sum(1 for t in stp if t.Type() == pcbnew.PCB_VIA_T)
print(f'STP victims: {len(stp)} ({nstp_seg} segs, {nstp_via} vias)')
for t in stp:
    b.Remove(t)

# ---- rip PHY B loop (4) + F tail (2) ----
rips = []
for a, bp in [((77.90, 10.08), (77.45, 10.10)),
              ((77.45, 10.10), (76.95, 11.05)),
              ((76.95, 11.05), (76.95, 14.988)),
              ((76.95, 14.988), (77.80, 16.20))]:
    v = find_seg(Bk, 'PHY_1V8', a, bp)
    assert len(v) == 1, (a, bp, len(v))
    rips += v
for a, bp in [((71.375, 17.625), (71.725, 17.75)),
              ((71.725, 17.75), (71.725, 18.0))]:
    v = find_seg(F, 'PHY_1V8', a, bp)
    assert len(v) == 1, (a, bp, len(v))
    rips += v
print('PHY rip victims:', len(rips))
for t in rips:
    b.Remove(t)


def add_seg(net, layer, a, bp, w):
    t = pcbnew.PCB_TRACK(b)
    t.SetNetCode(codes[net])
    t.SetLayer(layer)
    t.SetStart(pcbnew.VECTOR2I(int(round(a[0] * NM)), int(round(a[1] * NM))))
    t.SetEnd(pcbnew.VECTOR2I(int(round(bp[0] * NM)), int(round(bp[1] * NM))))
    t.SetWidth(int(round(w * NM)))
    b.Add(t)


def add_via(net, x, y):
    v = pcbnew.PCB_VIA(b)
    v.SetNetCode(codes[net])
    v.SetPosition(pcbnew.VECTOR2I(int(round(x * NM)), int(round(y * NM))))
    v.SetWidth(int(0.5 * NM))
    v.SetDrill(int(0.3 * NM))
    v.SetLayerPair(F, Bk)
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    b.Add(v)


# ---- PHY x77.15 loop (widths = 2*hw from az37 N4) ----
LOOP = [((77.90, 10.08), (77.50, 10.25), 0.30),
        ((77.50, 10.25), (77.28, 10.80), 0.20),
        ((77.28, 10.80), (77.15, 11.30), 0.20),
        ((77.15, 11.30), (77.15, 13.00), 0.30),
        ((77.15, 13.00), (77.15, 15.10), 0.30),
        ((77.15, 15.10), (77.80, 16.20), 0.30)]
for a, bp, w in LOOP:
    add_seg('PHY_1V8', Bk, a, bp, w)

# ---- PHY journey from design_phy_astar4.json ----
J = json.load(open('scratch/work/az/design_phy_astar4.json'))
for vx, vy in J['vias']:
    add_via('PHY_1V8', vx, vy)
nseg = 0
for run in J['runs']:
    lay = LAY[run['layer']]
    pts = [tuple(p) for p in run['pts']]
    for a, bp in zip(pts, pts[1:]):
        if abs(a[0] - bp[0]) < 1e-9 and abs(a[1] - bp[1]) < 1e-9:
            continue
        add_seg('PHY_1V8', lay, a, bp, 0.20)
        nseg += 1
print('journey segs added:', nseg, 'vias:', len(J['vias']))

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(OUT)

b2 = pcbnew.LoadBoard(OUT)
after = census(b2)
for n in sorted(set(before) | set(after)):
    if before.get(n, 0) != after.get(n, 0):
        print(f'census diff {n}: {before.get(n, 0)} -> {after.get(n, 0)}')
print('saved', OUT)

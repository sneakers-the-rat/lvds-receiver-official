"""t_aa2: U7 south-row surgery v3 on exp211 -> trial board.

Field planned against DRC's hard 0.200 mm clearance (t_aa1 referee
report): every via/track/pad gap >= 0.20 by construction.

1. ULPI_CK: rip F escape (pad -> via (74.625,19.125)). Re-lay: dive in
   its own column, via (76.70,17.02) d0.5; In2 north run
   (76.70,17.02)->(76.70,13.50)->(74.625,13.50) joining CK's In2
   vertical (kept). The southern In2 join is walled by the GND via at
   (77.25,18.38); the northern join crosses nothing.
2. PHY_1V8: rip F tail (77.25,17.188)->via(78.375,17.375) and the B
   run at y17.375 + B vertical tail. Re-lay: F stub
   (77.25,17.188)->(78.10,17.50), via (78.10,17.50) d0.6; B seg to a
   new B run at y16.2 (band 15.9-16.5, clears every south-row via's B
   disc by >=0.2), west to (72.125,17.625) via (kept); B vertical tail
   from U7.26's web rejoins the run at (77.875,16.2).
3. Trio mouths at U7 (staggered, pairwise >=0.7 centres, >=0.2 gaps):
   NXT via (75.25,17.00) d0.4/drill0.2, stub straight south;
   DIR via (75.70,17.50) d0.5; STP via (76.60,17.80) d0.5 with a west
   jog in its stub to thread between DIR and CK vias.
4. USB_RST mouth at U7: DM_PHY's diagonal + C22.2's pad + RBIAS's In2
   diagonal wall the south-west; take the long eastern path under the
   trio field to via (75.90,19.70) d0.5.
5. Trio mouths at U6 west face: NXT (69.30,-0.65), DIR (69.30,-1.45),
   STP (69.20,-2.15), all d0.5 (PG_3V3 B vertical x68.625 and the
   HV_SHDN In2 braid clear by >=0.2).
Method: netcodes first; ONE scan collects rip targets; all Removes;
all Adds; never GetTracks after a Remove. Reload count check.
"""
import wx
_app = wx.App(False)
import pcbnew
SRC = 'hw/pdlvds_rx.exp211.kicad_pcb'; OUT = 'scratch/work/t_aa2.kicad_pcb'
b = pcbnew.LoadBoard(SRC)
M = pcbnew.FromMM; MM = pcbnew.ToMM
V = lambda x, y: pcbnew.VECTOR2I(M(x), M(y))
NETS = ('ULPI_CK', 'PHY_1V8', 'ULPI_NXT', 'ULPI_DIR', 'ULPI_STP', 'USB_RST')
CODE = {n: b.GetNetcodeFromNetname(n) for n in NETS}
assert all(c > 0 for c in CODE.values()), CODE
LAY = {'F': pcbnew.F_Cu, 'In1': pcbnew.In1_Cu, 'In2': pcbnew.In2_Cu, 'B': pcbnew.B_Cu}
LAYNAME = {pcbnew.F_Cu: 'F', pcbnew.In1_Cu: 'In1', pcbnew.In2_Cu: 'In2', pcbnew.B_Cu: 'B'}

RIP_SEGS = [
    ('ULPI_CK', 'F', (76.750,16.438), (76.750,16.688)),
    ('ULPI_CK', 'F', (76.750,16.688), (76.625,17.125)),
    ('ULPI_CK', 'F', (76.625,17.125), (76.375,17.375)),
    ('ULPI_CK', 'F', (76.375,17.375), (75.625,17.375)),
    ('ULPI_CK', 'F', (75.625,17.375), (75.375,17.375)),
    ('ULPI_CK', 'F', (75.375,17.375), (75.125,17.625)),
    ('ULPI_CK', 'F', (75.125,17.625), (74.875,17.875)),
    ('ULPI_CK', 'F', (74.875,17.875), (74.875,18.875)),
    ('ULPI_CK', 'F', (74.875,18.875), (74.625,19.125)),
    ('PHY_1V8', 'F', (77.250,17.188), (77.875,17.375)),
    ('PHY_1V8', 'F', (77.875,17.375), (78.375,17.375)),
    ('PHY_1V8', 'B', (78.375,17.375), (76.125,17.375)),
    ('PHY_1V8', 'B', (76.125,17.375), (73.125,17.375)),
    ('PHY_1V8', 'B', (73.125,17.375), (72.375,17.375)),
    ('PHY_1V8', 'B', (72.375,17.375), (72.125,17.625)),
    ('PHY_1V8', 'B', (77.875,15.125), (77.875,17.375)),
]
RIP_VIAS = [('ULPI_CK', (74.625, 19.125)), ('PHY_1V8', (78.375, 17.375))]

def key_seg(net, lay, a, bb):
    return (net, lay, frozenset(((round(a[0], 3), round(a[1], 3)),
                                 (round(bb[0], 3), round(bb[1], 3)))))

want = {}
for net, lay, a, bb in RIP_SEGS:
    want[key_seg(net, lay, a, bb)] = None
want_via = {(n, (round(p[0], 3), round(p[1], 3))): None for n, p in RIP_VIAS}

for t in list(b.GetTracks()):
    if t.Type() == pcbnew.PCB_VIA_T:
        q = t.GetPosition()
        k = (t.GetNetname(), (round(MM(q.x), 3), round(MM(q.y), 3)))
        if k in want_via: want_via[k] = t
    else:
        s, e = t.GetStart(), t.GetEnd()
        k = key_seg(t.GetNetname(), LAYNAME[t.GetLayer()],
                    (MM(s.x), MM(s.y)), (MM(e.x), MM(e.y)))
        if k in want: want[k] = t
missing = [k for k, v in want.items() if v is None] + \
          [k for k, v in want_via.items() if v is None]
assert not missing, f"rip targets not found: {missing}"
for t in list(want.values()) + list(want_via.values()):
    b.Remove(t)
print(f"ripped {len(want)} segs + {len(want_via)} vias")

def trk(net, a, bb, w=0.2, lay='F'):
    t = pcbnew.PCB_TRACK(b); t.SetNetCode(CODE[net])
    t.SetStart(V(*a)); t.SetEnd(V(*bb)); t.SetWidth(M(w)); t.SetLayer(LAY[lay]); b.Add(t)

def via(net, p, d=0.5, drill=0.3):
    v = pcbnew.PCB_VIA(b); v.SetNetCode(CODE[net])
    v.SetPosition(V(*p)); v.SetWidth(M(d)); v.SetDrill(M(drill))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v)

# 1. CK re-lay: own-column dive + northern In2 join
trk('ULPI_CK', (76.750,16.438), (76.700,17.020))
via('ULPI_CK', (76.700, 17.020))
trk('ULPI_CK', (76.700,17.020), (76.700,13.500), w=0.25, lay='In2')
trk('ULPI_CK', (76.700,13.500), (74.625,13.500), w=0.25, lay='In2')
# 2. PHY_1V8 re-lay: F stub east, B run at y16.2
trk('PHY_1V8', (77.250,17.188), (78.100,17.500))
via('PHY_1V8', (78.100, 17.500), d=0.6)
trk('PHY_1V8', (78.100,17.500), (77.950,16.500), w=0.2, lay='B')
trk('PHY_1V8', (77.950,16.200), (72.600,16.200), w=0.6, lay='B')
trk('PHY_1V8', (77.950,16.500), (77.950,16.200), w=0.2, lay='B')
trk('PHY_1V8', (77.875,15.125), (77.875,16.200), w=0.2, lay='B')
trk('PHY_1V8', (72.600,16.200), (72.125,16.800), w=0.2, lay='B')
trk('PHY_1V8', (72.125,16.800), (72.125,17.625), w=0.2, lay='B')
# 3. Trio mouths at U7
trk('ULPI_NXT', (75.250,16.438), (75.250,17.000)); via('ULPI_NXT', (75.250, 17.000), d=0.4, drill=0.2)
trk('ULPI_DIR', (75.750,16.438), (75.700,17.500)); via('ULPI_DIR', (75.700, 17.500))
trk('ULPI_STP', (76.250,16.438), (76.100,17.200))
trk('ULPI_STP', (76.100,17.200), (76.600,17.800)); via('ULPI_STP', (76.600, 17.800))
# 4. USB_RST mouth at U7: eastern path
for a, bb in [((74.250,16.438),(74.300,17.000)), ((74.300,17.000),(74.800,17.700)),
              ((74.800,17.700),(74.950,18.000)), ((74.950,18.000),(74.950,19.600)),
              ((74.950,19.600),(75.900,19.700))]:
    trk('USB_RST', a, bb)
via('USB_RST', (75.900, 19.700))
# 5. Trio mouths at U6 west face
trk('ULPI_NXT', (70.600,-0.750), (69.300,-0.650)); via('ULPI_NXT', (69.300, -0.650))
trk('ULPI_DIR', (70.600,-1.250), (69.300,-1.450)); via('ULPI_DIR', (69.300, -1.450))
trk('ULPI_STP', (70.600,-2.250), (69.200,-2.150)); via('ULPI_STP', (69.200, -2.150))

zr = pcbnew.ZONE_FILLER(b); zr.Fill(b.Zones())
b.Save(OUT); print("saved", OUT)
b2 = pcbnew.LoadBoard(OUT)
for n in NETS:
    c = sum(1 for t in b2.GetTracks() if t.GetNetname() == n)
    print(f"reload {n}: {c} items")

"""t_aa3: U7 south-row surgery v5 on exp211 -> trial board.

Built from t_aa1/t_aa2 DRC referee reports (hard 0.200 clearance,
min via d0.5/drill0.3). Changes vs exp211:

CK: rip F escape (9 segs + via (74.625,19.125)); stub dives east:
(76.75,16.438)->(76.75,17.30)->via (77.60,18.15) d0.5; In2 join north:
(77.60,18.15)->(76.90,17.60)->(76.90,13.50)->(74.625,13.50); trim the
CK In2 vertical's dangling south end (74.625,19.125) to (74.625,13.50).
PHY_1V8: rip F tail (2 segs + via (78.375,17.375) d0.8) and B run at
y17.375 (5 segs) + B vertical (2 segs). Re-lay: F (77.25,17.188)->
(78.10,17.50), via d0.6; B run at y16.2 (w0.6) x73.4..77.8 with w0.2
joiners to the via, to U7.26's B tail (diag from (77.875,12.875)), and
west down to via (72.125,17.625) (kept, clear of DP_PHY's via corner).
Trio mouths U7: NXT via (75.32,17.00); DIR via (75.60,17.70) with an
east-jog stub threading STP pad corner (0.3) and NXT via (0.55);
STP via (76.45,18.00), stub in the [76.175,76.45] corridor.
USB_RST mouth U7: eastern path south, then west of CDR_SQUELCH's
vertical x75.125, via (74.50,20.30).
C20: move +0.6y to (76.5,19.1); its XI via (75.625,18.625)->
(75.625,19.225) with a B extension seg; GND via (77.25,18.38)->
(77.25,18.98). Opens the y18.0 via strip for STP/CK.
Trio mouths U6 west face: NXT (69.30,-0.65), DIR (69.35,-1.40),
STP (69.30,-2.15), d0.5.
Method: netcodes first; ONE scan collects rip targets + objects to
move; all Removes; moves; all Adds; never GetTracks after a Remove.
Reload count check (save-rename guard).
"""
import wx
_app = wx.App(False)
import pcbnew
SRC = 'hw/pdlvds_rx.exp211.kicad_pcb'; OUT = 'scratch/work/t_aa3.kicad_pcb'
b = pcbnew.LoadBoard(SRC)
M = pcbnew.FromMM; MM = pcbnew.ToMM
V = lambda x, y: pcbnew.VECTOR2I(M(x), M(y))
NETS = ('ULPI_CK', 'PHY_1V8', 'ULPI_NXT', 'ULPI_DIR', 'ULPI_STP', 'USB_RST', 'XI', 'GND')
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
    ('PHY_1V8', 'B', (77.875,12.875), (77.875,15.125)),
    ('PHY_1V8', 'B', (77.875,15.125), (77.875,17.375)),
]
RIP_VIAS = [('ULPI_CK', (74.625, 19.125)), ('PHY_1V8', (78.375, 17.375))]
MOVE_VIAS = {('XI', (75.625, 18.625)): (75.625, 19.225),
             ('GND', (77.250, 18.380)): (77.250, 18.980)}

def key_seg(net, lay, a, bb):
    return (net, lay, frozenset(((round(a[0], 3), round(a[1], 3)),
                                 (round(bb[0], 3), round(bb[1], 3)))))

want = {}
for net, lay, a, bb in RIP_SEGS:
    want[key_seg(net, lay, a, bb)] = None
want_via = {(n, (round(p[0], 3), round(p[1], 3))): None for n, p in RIP_VIAS}
move_via = {k: None for k in MOVE_VIAS}
ck_vert = None
for t in list(b.GetTracks()):
    if t.Type() == pcbnew.PCB_VIA_T:
        q = t.GetPosition()
        k = (t.GetNetname(), (round(MM(q.x), 3), round(MM(q.y), 3)))
        if k in want_via: want_via[k] = t
        if k in move_via: move_via[k] = t
    else:
        s, e = t.GetStart(), t.GetEnd()
        sp, ep = (MM(s.x), MM(s.y)), (MM(e.x), MM(e.y))
        if t.GetNetname() == 'ULPI_CK' and LAYNAME[t.GetLayer()] == 'In2' and \
           {round(sp[0], 3), round(ep[0], 3)} == {74.625} and \
           {round(sp[1], 3), round(ep[1], 3)} == {6.375, 19.125}:
            ck_vert = t
        k = key_seg(t.GetNetname(), LAYNAME[t.GetLayer()], sp, ep)
        if k in want: want[k] = t
missing = [k for k, v in want.items() if v is None] + \
          [k for k, v in want_via.items() if v is None] + \
          [k for k, v in move_via.items() if v is None]
assert not missing, f"targets not found: {missing}"
assert ck_vert is not None, "CK In2 vertical not found"
for t in list(want.values()) + list(want_via.values()):
    b.Remove(t)
print(f"ripped {len(want)} segs + {len(want_via)} vias")
# Trim CK In2 vertical south end to (74.625,13.5)
s, e = ck_vert.GetStart(), ck_vert.GetEnd()
if abs(MM(s.y) - 19.125) < 0.01:
    ck_vert.SetStart(V(74.625, 13.500))
else:
    ck_vert.SetEnd(V(74.625, 13.500))
# Move C20 + its vias
for fp in b.GetFootprints():
    if fp.GetReference() == 'C20':
        fp.SetPosition(V(76.500, 19.100))
for k, obj in move_via.items():
    obj.SetPosition(V(*MOVE_VIAS[k]))
print("moved C20 + 2 vias")

def trk(net, a, bb, w=0.2, lay='F'):
    t = pcbnew.PCB_TRACK(b); t.SetNetCode(CODE[net])
    t.SetStart(V(*a)); t.SetEnd(V(*bb)); t.SetWidth(M(w)); t.SetLayer(LAY[lay]); b.Add(t)

def via(net, p, d=0.5, drill=0.3):
    v = pcbnew.PCB_VIA(b); v.SetNetCode(CODE[net])
    v.SetPosition(V(*p)); v.SetWidth(M(d)); v.SetDrill(M(drill))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v)

# CK re-lay
trk('ULPI_CK', (76.750,16.438), (76.750,17.300))
trk('ULPI_CK', (76.750,17.300), (77.600,18.150))
via('ULPI_CK', (77.600, 18.150))
trk('ULPI_CK', (77.600,18.150), (76.900,17.600), w=0.25, lay='In2')
trk('ULPI_CK', (76.900,17.600), (76.900,13.500), w=0.25, lay='In2')
trk('ULPI_CK', (76.900,13.500), (74.625,13.500), w=0.25, lay='In2')
# PHY_1V8 re-lay
trk('PHY_1V8', (77.250,17.188), (78.100,17.500))
via('PHY_1V8', (78.100, 17.500), d=0.6)
trk('PHY_1V8', (78.100,17.500), (77.800,16.200), w=0.2, lay='B')
trk('PHY_1V8', (77.800,16.200), (73.400,16.200), w=0.6, lay='B')
trk('PHY_1V8', (77.875,12.875), (77.800,16.200), w=0.2, lay='B')
trk('PHY_1V8', (73.400,16.200), (72.900,16.900), w=0.2, lay='B')
trk('PHY_1V8', (72.900,16.900), (72.125,17.625), w=0.2, lay='B')
# XI B extension for moved C20 via
trk('XI', (75.625,18.625), (75.625,19.225), w=0.2, lay='B')
# Trio mouths at U7
trk('ULPI_NXT', (75.250,16.438), (75.320,17.000)); via('ULPI_NXT', (75.320, 17.000))
for a, bb in [((75.750,16.438),(75.800,16.900)), ((75.800,16.900),(75.830,17.350)),
              ((75.830,17.350),(75.600,17.700))]:
    trk('ULPI_DIR', a, bb)
via('ULPI_DIR', (75.600, 17.700))
trk('ULPI_STP', (76.250,16.438), (76.300,17.200))
trk('ULPI_STP', (76.300,17.200), (76.450,18.000)); via('ULPI_STP', (76.450, 18.000))
# USB_RST mouth at U7: eastern path, then west of SQUELCH vertical
for a, bb in [((74.250,16.438),(74.350,17.000)), ((74.350,17.000),(74.850,17.700)),
              ((74.850,17.700),(74.950,18.000)), ((74.950,18.000),(74.850,19.300)),
              ((74.850,19.300),(74.500,20.300))]:
    trk('USB_RST', a, bb)
via('USB_RST', (74.500, 20.300))
# Trio mouths at U6 west face
trk('ULPI_NXT', (70.600,-0.750), (69.300,-0.650)); via('ULPI_NXT', (69.300, -0.650))
trk('ULPI_DIR', (70.600,-1.250), (69.350,-1.400)); via('ULPI_DIR', (69.350, -1.400))
trk('ULPI_STP', (70.600,-2.250), (69.300,-2.150)); via('ULPI_STP', (69.300, -2.150))

zr = pcbnew.ZONE_FILLER(b); zr.Fill(b.Zones())
b.Save(OUT); print("saved", OUT)
b2 = pcbnew.LoadBoard(OUT)
for n in NETS:
    c = sum(1 for t in b2.GetTracks() if t.GetNetname() == n)
    print(f"reload {n}: {c} items")

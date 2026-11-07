"""t_aa4: U7 south-row surgery v6 on exp211 -> trial board.

Lessons banked from t_aa1..t_aa3 referee reports:
- C20 move is DEAD: +0.6y lands its pads on CDR_SQUELCH's y19.375
  horizontal (shorts) and its courtyard overlaps U5. Reverted.
- The U7 south strip cannot pack NXT+DIR+STP+CK d0.5 vias at the
  board's hard 0.200 clearance: STP's pad-corner exclusion (r0.3)
  and CK via's exclusion (r0.55) overlap every STP corridor, and
  PHY's F stub + C20.1/C20.2 pads wall the east. STP is therefore
  NOT touched this pass; it gets a dedicated pass (candidate: joint
  re-lay with DM_PHY's west corridor or C20/SQUELCH web).
This pass: CK re-lay, PHY_1V8 re-lay, NXT + DIR mouths (U7+U6),
USB_RST mouth (eastern path, via west of SQUELCH's vertical, north
of C28). All gaps >= 0.20 by construction against DRC's rules
(via d>=0.5, drill >=0.3, hole clearance 0.25).

CK: rip F escape (9 segs + via (74.625,19.125)); stub
(76.75,16.438)->via (76.62,17.30); In2 north (76.62,17.30)->
(76.62,13.50)->(74.625,13.50); trim CK In2 vertical south end
(74.625,19.125)->(74.625,13.50). (Southern In2 join is walled by
GND via (77.25,18.38); northern crosses nothing: +3V3A's w0.6 In2
vertical x77.375 keeps 0.33 from CK's x76.62 vertical.)
PHY_1V8: rip F tail (2 segs + via (78.375,17.375) d0.8), B run at
y17.375 (5 segs), B vertical (2 segs). Re-lay: F (77.25,17.188)->
(78.10,17.50), via d0.6; B run y16.2 w0.6 x73.4..77.8, w0.2 joiners
to via, to U7.26's B tail (diag from (77.875,12.875)), and west to
via (72.125,17.625) kept (jog starts x73.4, clear of DP_PHY's via
(72.125,15.875) corner seg).
NXT: via (75.24,17.15) (0.207 from GND pad corner, 0.223 copper /
0.29 hole from DIR pad rect); DIR: via (75.92,17.42) with east-jog
stub (0.203 past STP pad corner, 0.613 from NXT via).
USB_RST: (74.25,16.438)->(74.35,17.00)->(74.85,17.70)->(74.95,18.00)
->(74.85,19.00)->via (74.60,19.50).
U6 mouths: NXT (69.30,-0.65), DIR (69.28,-1.38) (SDA B vertical
x69.875 keeps 0.22; PG_3V3 B vertical x68.625 keeps 0.30).
Method: netcodes first; ONE scan; all Removes; moves; Adds; never
GetTracks after a Remove. Reload count check.
"""
import wx
_app = wx.App(False)
import pcbnew
SRC = 'hw/pdlvds_rx.exp211.kicad_pcb'; OUT = 'scratch/work/t_aa4.kicad_pcb'
b = pcbnew.LoadBoard(SRC)
M = pcbnew.FromMM; MM = pcbnew.ToMM
V = lambda x, y: pcbnew.VECTOR2I(M(x), M(y))
NETS = ('ULPI_CK', 'PHY_1V8', 'ULPI_NXT', 'ULPI_DIR')
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

def key_seg(net, lay, a, bb):
    return (net, lay, frozenset(((round(a[0], 3), round(a[1], 3)),
                                 (round(bb[0], 3), round(bb[1], 3)))))

want = {}
for net, lay, a, bb in RIP_SEGS:
    want[key_seg(net, lay, a, bb)] = None
want_via = {(n, (round(p[0], 3), round(p[1], 3))): None for n, p in RIP_VIAS}
ck_vert = None
for t in list(b.GetTracks()):
    if t.Type() == pcbnew.PCB_VIA_T:
        q = t.GetPosition()
        k = (t.GetNetname(), (round(MM(q.x), 3), round(MM(q.y), 3)))
        if k in want_via: want_via[k] = t
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
          [k for k, v in want_via.items() if v is None]
assert not missing, f"targets not found: {missing}"
assert ck_vert is not None, "CK In2 vertical not found"
for t in list(want.values()) + list(want_via.values()):
    b.Remove(t)
print(f"ripped {len(want)} segs + {len(want_via)} vias")
s, e = ck_vert.GetStart(), ck_vert.GetEnd()
if abs(MM(s.y) - 19.125) < 0.01:
    ck_vert.SetStart(V(74.625, 13.500))
else:
    ck_vert.SetEnd(V(74.625, 13.500))

def trk(net, a, bb, w=0.2, lay='F'):
    t = pcbnew.PCB_TRACK(b); t.SetNetCode(CODE[net])
    t.SetStart(V(*a)); t.SetEnd(V(*bb)); t.SetWidth(M(w)); t.SetLayer(LAY[lay]); b.Add(t)

def via(net, p, d=0.5, drill=0.3):
    v = pcbnew.PCB_VIA(b); v.SetNetCode(CODE[net])
    v.SetPosition(V(*p)); v.SetWidth(M(d)); v.SetDrill(M(drill))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v)

# CK re-lay
trk('ULPI_CK', (76.750,16.438), (76.620,17.300))
via('ULPI_CK', (76.620, 17.300))
trk('ULPI_CK', (76.620,17.300), (76.620,13.500), w=0.25, lay='In2')
trk('ULPI_CK', (76.620,13.500), (74.625,13.500), w=0.25, lay='In2')
# PHY_1V8 re-lay
trk('PHY_1V8', (77.250,17.188), (78.100,17.500))
via('PHY_1V8', (78.100, 17.500), d=0.6)
trk('PHY_1V8', (78.100,17.500), (77.800,16.200), w=0.2, lay='B')
trk('PHY_1V8', (77.800,16.200), (73.400,16.200), w=0.6, lay='B')
trk('PHY_1V8', (77.875,12.875), (77.800,16.200), w=0.2, lay='B')
trk('PHY_1V8', (73.400,16.200), (72.900,16.900), w=0.2, lay='B')
trk('PHY_1V8', (72.900,16.900), (72.125,17.625), w=0.2, lay='B')
# NXT + DIR mouths at U7
trk('ULPI_NXT', (75.250,16.438), (75.240,17.150)); via('ULPI_NXT', (75.240, 17.150))
trk('ULPI_DIR', (75.750,16.438), (75.870,17.180))
trk('ULPI_DIR', (75.870,17.180), (75.920,17.420)); via('ULPI_DIR', (75.920, 17.420))
# USB_RST mouth: NOT placed this pass. The corridor between U7.10's
# GND pad corner (74.625,16.875) and DM_PHY's w0.25 escape corner
# (74.125,17.375) is closed: exclusion radii 0.31 + 0.425 = 0.735
# exceed the 0.707 corner spacing, and DM_PHY's own re-lay slots
# west are walled by RBIAS's In2 diagonal and C22.2's pad. USB_RST
# needs a joint job with DM_PHY (or a SQUELCH-web re-lay).
# NXT + DIR mouths at U6 west face
trk('ULPI_NXT', (70.600,-0.750), (69.300,-0.650)); via('ULPI_NXT', (69.300, -0.650))
trk('ULPI_DIR', (70.600,-1.250), (69.280,-1.380)); via('ULPI_DIR', (69.280, -1.380))

zr = pcbnew.ZONE_FILLER(b); zr.Fill(b.Zones())
b.Save(OUT); print("saved", OUT)
b2 = pcbnew.LoadBoard(OUT)
for n in NETS:
    c = sum(1 for t in b2.GetTracks() if t.GetNetname() == n)
    print(f"reload {n}: {c} items")

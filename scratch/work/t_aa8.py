"""t_aa8: U7 south-row surgery v7 on exp211 -> trial board.

Diagnosis chain (t_aa1..t_aa7, probe_dir/probe_field/probe_dir2):
- KiCad DRC (flat 0.200) and router6's model (w0.25 tracks, d0.6
  via discs, per-net clearances up to 0.25) are DIFFERENT gates.
  Mouth vias for heal must satisfy the router model or astar's
  goal fanout is empty (heal visited 445k cells board-wide yet
  never terminated: the goal via was model-illegal by -0.018).
- Router-model via scan of the U7 south strip: NXT has a legal
  pocket at (74.95,17.50) vm +0.117; DIR and STP have ZERO legal
  points in the strip (blockers: CK via, PHY_1V8 stub/via at clr
  0.25, C20.1/C20.2 pads, GND via (77.25,18.38)).
- DIR's only model-legal pocket in the whole south-west is
  (74.65,19.25) vm +0.153 (west of SQUELCH's vertical, north of
  C28). DIR reaches it by a hand In2 run from its DRC-legal first
  via (75.92,17.42): In2 at y17.4-19.3 x74.6-75.9 is open (XI via
  (75.625,18.625) keeps 0.72 from the run).
- STP has no DRC-legal first dive anywhere south of its pad while
  CK's via and PHY's stub stand where they are; STP is deferred
  to a dedicated pass (joint CK+PHY+STP re-lay). NOT touched here.
- USB_RST deferred (corridor between U7.10 GND pad corner and
  DM_PHY's w0.25 escape corner is closed: 0.31+0.425 > 0.707).
This pass: CK re-lay + PHY_1V8 re-lay (as t_aa4, DRC-verified
158 = 154 + 4 dangling with the old mouths), NXT mouth at the
model pocket, DIR mouth + hand In2 run to the west pocket.
Then heal_nets ULPI_NXT ULPI_DIR does the hauls to U6.
Method: netcodes first; ONE scan; all Removes; moves; Adds.
"""
import wx
_app = wx.App(False)
import pcbnew
SRC = 'hw/pdlvds_rx.exp211.kicad_pcb'; OUT = 'scratch/work/t_aa8.kicad_pcb'
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
# NXT mouth at the router-model pocket (74.95,17.50)
trk('ULPI_NXT', (75.250,16.438), (75.250,17.300))
trk('ULPI_NXT', (75.250,17.300), (74.950,17.500))
via('ULPI_NXT', (74.950, 17.500))
# DIR mouth + hand In2 run to the west pocket (74.65,19.25)
trk('ULPI_DIR', (75.750,16.438), (75.870,17.180))
trk('ULPI_DIR', (75.870,17.180), (75.920,17.420))
via('ULPI_DIR', (75.920, 17.420))
trk('ULPI_DIR', (75.920,17.420), (74.900,18.300), lay='In2')
trk('ULPI_DIR', (74.900,18.300), (74.650,19.250), lay='In2')
via('ULPI_DIR', (74.650, 19.250))

zr = pcbnew.ZONE_FILLER(b); zr.Fill(b.Zones())
b.Save(OUT); print("saved", OUT)
b2 = pcbnew.LoadBoard(OUT)
for n in NETS:
    c = sum(1 for t in b2.GetTracks() if t.GetNetname() == n)
    print(f"reload {n}: {c} items")

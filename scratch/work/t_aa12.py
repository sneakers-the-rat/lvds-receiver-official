"""t_aa12: district prep pass on exp211 - CK + PHY_1V8 re-lays ONLY.

This is the bankable first half of the U7 south-row district job
(queue item 1's prescribed "rip + re-lay the CK web"), refereed
clean. The trio/USB_RST terminations are NOT in this pass; the
session's full evidence for why is in t_aa1..t_aa11 + probes:
- STP: no DRC-legal first dive exists south of U7.13 while CK's
  via and PHY's stub stand (packing proof, t_aa3 analysis).
- USB_RST: the F corridor between U7.10's GND pad corner
  (74.625,16.875) and DM_PHY's w0.25 escape corner (74.125,17.375)
  is closed (exclusions 0.31+0.425 > 0.707 corner spacing).
- NXT/DIR hauls: heal/astar6 cannot cross the district ring in
  its model in either direction (flood from U6.28 visits 445,790
  cells, all 18 goal cells unvisited; reversed search exhausts in
  3 s). Hand-weave first cut (t_aa11) hit 55 fault pairs in the
  western via/pad fields (RBIAS/XO In2 verticals, C21/C22/C23/C47
  pads, SDA via (69.32,2.14), SCL via (69.375,1.375)) - the hauls
  are a dedicated hand-routing job for the next run, starting
  from this re-laid state. Anchor design (model pockets
  (74.95,17.50) NXT / (74.65,19.25) DIR-via-In2) is in t_aa8.

CK re-lay: rip the F escape that sealed the trio's pad columns
(9 segs + via (74.625,19.125)); new stub (76.75,16.438)->via
(76.62,17.30); In2 joins the CK trunk at the NORTH end
((76.62,13.50)->(74.625,13.50); CK In2 vertical trimmed to end
(74.625,13.50)) - the southern In2 join is walled by GND via
(77.25,18.38). PHY_1V8 re-lay: rip F tail + d0.8 via + B run at
y17.375 (which shadowed every B via slot south of the row) + B
vertical; new F (77.25,17.188)->via (78.10,17.50) d0.6; B run at
y16.20 (w0.6, x73.4..77.8) with w0.2 joiners to the via, to
U7.26's B tail at (77.875,12.875), and west to C22.1's via
(72.125,17.625). Both nets stay connected; expected DRC delta
zero (154 violations / 21 unconnected, class table unchanged).
Method: netcodes first; ONE scan; all Removes; moves; Adds;
reload netname check (save-rename guard).
"""
import wx
_app = wx.App(False)
import pcbnew
SRC = 'hw/pdlvds_rx.exp211.kicad_pcb'; OUT = 'scratch/work/t_aa12.kicad_pcb'
b = pcbnew.LoadBoard(SRC)
M = pcbnew.FromMM; MM = pcbnew.ToMM
V = lambda x, y: pcbnew.VECTOR2I(M(x), M(y))
NETS = ('ULPI_CK', 'PHY_1V8')
CODE = {n: b.GetNetcodeFromNetname(n) for n in NETS}
assert all(c > 0 for c in CODE.values()), CODE
LAY = {'F': pcbnew.F_Cu, 'In2': pcbnew.In2_Cu, 'B': pcbnew.B_Cu}
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

zr = pcbnew.ZONE_FILLER(b); zr.Fill(b.Zones())
b.Save(OUT); print("saved", OUT)
b2 = pcbnew.LoadBoard(OUT)
for n in NETS:
    c = sum(1 for t in b2.GetTracks() if t.GetNetname() == n)
    print(f"reload {n}: {c} items")

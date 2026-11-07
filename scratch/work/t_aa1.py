"""t_aa1: U7 south-row surgery on exp211 -> trial board.

1. Rip ULPI_CK's F escape (pad -> via (74.625,19.125)); re-lay CK as an
   immediate dive at (76.90,17.50) + In2 run at y18.0 joining CK's In2
   vertical x74.625 (kept). Frees the F strip south of the south row.
2. Rip PHY_1V8's B run at y17.375 (shadows every via slot south of the
   row on B) + its F tail/via (78.375,17.375); re-lay: F stub to via
   (77.60,16.85) d0.5, B run at y16.6 west to (72.125,17.625) via.
3. Mouths (F stub + d0.5 via) for ULPI_NXT/DIR/STP at U7 (staggered
   field y17.25/17.50/17.30) and at U6 west face ((69.15,-0.65),
   (69.20,-1.50), (69.15,-2.35) -- prior computed field shifted east
   0.3 where PG_3V3's B vertical x68.625 shadows it), and for USB_RST
   at U7 ((73.90,17.50)). Hauls left to heal_nets.
Method: capture netcodes first; ONE scan collects every rip target;
all Removes; all Adds; never GetTracks after a Remove (the board's
track container wrapper dies -- same family as the net-map law).
Reload-verifies per-net item counts (save-rename check).
"""
import wx
_app = wx.App(False)
import pcbnew
SRC = 'hw/pdlvds_rx.exp211.kicad_pcb'; OUT = 'scratch/work/t_aa1.kicad_pcb'
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

def via(net, p, d=0.5):
    v = pcbnew.PCB_VIA(b); v.SetNetCode(CODE[net])
    v.SetPosition(V(*p)); v.SetWidth(M(d)); v.SetDrill(M(0.3))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v)

# CK re-lay
trk('ULPI_CK', (76.750,16.438), (76.900,17.500))
via('ULPI_CK', (76.900, 17.500))
trk('ULPI_CK', (76.900,17.500), (76.900,18.000), w=0.25, lay='In2')
trk('ULPI_CK', (76.900,18.000), (74.625,18.000), w=0.25, lay='In2')
# PHY_1V8 re-lay
trk('PHY_1V8', (77.250,17.188), (77.600,16.850))
via('PHY_1V8', (77.600, 16.850))
trk('PHY_1V8', (77.875,15.125), (77.875,16.600), w=0.2, lay='B')
trk('PHY_1V8', (77.875,16.600), (72.600,16.600), w=0.6, lay='B')
trk('PHY_1V8', (72.600,16.600), (72.125,17.150), w=0.2, lay='B')
trk('PHY_1V8', (72.125,17.150), (72.125,17.625), w=0.2, lay='B')
# Trio + USB_RST mouths at U7
trk('ULPI_NXT', (75.250,16.438), (75.200,17.250)); via('ULPI_NXT', (75.200, 17.250))
trk('ULPI_DIR', (75.750,16.438), (75.800,17.500)); via('ULPI_DIR', (75.800, 17.500))
trk('ULPI_STP', (76.250,16.438), (76.350,17.300)); via('ULPI_STP', (76.350, 17.300))
trk('USB_RST', (74.250,16.438), (73.950,16.950))
trk('USB_RST', (73.950,16.950), (73.900,17.500)); via('USB_RST', (73.900, 17.500))
# Trio mouths at U6 west face
trk('ULPI_NXT', (70.600,-0.750), (69.150,-0.650)); via('ULPI_NXT', (69.150, -0.650))
trk('ULPI_DIR', (70.600,-1.250), (69.200,-1.500)); via('ULPI_DIR', (69.200, -1.500))
trk('ULPI_STP', (70.600,-2.250), (69.150,-2.350)); via('ULPI_STP', (69.150, -2.350))

zr = pcbnew.ZONE_FILLER(b); zr.Fill(b.Zones())
b.Save(OUT); print("saved", OUT)
b2 = pcbnew.LoadBoard(OUT)
for n in NETS:
    c = sum(1 for t in b2.GetTracks() if t.GetNetname() == n)
    print(f"reload {n}: {c} items")

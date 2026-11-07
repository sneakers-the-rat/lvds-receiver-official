"""t_aa11: t_aa8 + U6 mouths + hand-woven ULPI_NXT haul (B/In2).

heal/astar6 cannot cross the U7 district ring in its model in
either direction (flood from U6 visits 445,790 cells, goal cells
all unvisited; reversed search from the U7 group exhausts in 3 s -
the anchor cells sit in model pockets). So the hauls are hand
routes under KiCad DRC rules (w0.2, via d0.5), refereed by
kicad-cli DRC. NXT first; DIR follows in t_aa12.

NXT path (anchor via (74.95,17.50) already on t_aa8):
 B : via -> (74.20,18.70) -> dive (72.30,18.70)
 In2: -> (72.30,14.60) dive        [+5V y13.625 stays north]
 B : -> (72.30,12.90) dive         [SCL B horiz y11.625 north]
 In2: -> (71.90,11.20) -> dive (71.60,10.40)   [south of BIST]
 B : -> dive (70.20,10.80)         [crosses BIST on B]
 In2: -> (70.20,6.90) -> dive (71.10,4.90)     [north of BIST,
        east of DAC_VREF's web]
 B : -> (70.50,3.40) -> (69.45,2.20) dive
 B : -> (69.45,-0.50) -> mouth via (69.30,-0.65) -> F stub -> U6.29
DIR gets only its U6 mouth here (F stub + via (69.28,-1.38));
its haul is t_aa12.
Reload netname check at end (save-rename guard).
"""
import wx
_app = wx.App(False)
import pcbnew
SRC = 'scratch/work/t_aa8.kicad_pcb'; OUT = 'scratch/work/t_aa11.kicad_pcb'
b = pcbnew.LoadBoard(SRC)
M = pcbnew.FromMM; MM = pcbnew.ToMM
V = lambda x, y: pcbnew.VECTOR2I(M(x), M(y))
NETS = ('ULPI_NXT', 'ULPI_DIR')
CODE = {n: b.GetNetcodeFromNetname(n) for n in NETS}
assert all(c > 0 for c in CODE.values()), CODE
LAY = {'F': pcbnew.F_Cu, 'In2': pcbnew.In2_Cu, 'B': pcbnew.B_Cu}

def trk(net, a, bb, w=0.2, lay='F'):
    t = pcbnew.PCB_TRACK(b); t.SetNetCode(CODE[net])
    t.SetStart(V(*a)); t.SetEnd(V(*bb)); t.SetWidth(M(w)); t.SetLayer(LAY[lay]); b.Add(t)

def via(net, p, d=0.5, drill=0.3):
    v = pcbnew.PCB_VIA(b); v.SetNetCode(CODE[net])
    v.SetPosition(V(*p)); v.SetWidth(M(d)); v.SetDrill(M(drill))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); b.Add(v)

# U6 mouths (F stubs + vias) for both nets
trk('ULPI_NXT', (70.600,-0.750), (69.300,-0.650)); via('ULPI_NXT', (69.300, -0.650))
trk('ULPI_DIR', (70.600,-1.250), (69.280,-1.380)); via('ULPI_DIR', (69.280, -1.380))

# NXT haul
B = 'B'; I = 'In2'
for a, bb in [((74.950,17.500),(74.200,18.700)), ((74.200,18.700),(72.300,18.700))]:
    trk('ULPI_NXT', a, bb, lay=B)
via('ULPI_NXT', (72.300, 18.700))
trk('ULPI_NXT', (72.300,18.700), (72.300,14.600), lay=I)
via('ULPI_NXT', (72.300, 14.600))
trk('ULPI_NXT', (72.300,14.600), (72.300,12.900), lay=B)
via('ULPI_NXT', (72.300, 12.900))
trk('ULPI_NXT', (72.300,12.900), (71.900,11.200), lay=I)
trk('ULPI_NXT', (71.900,11.200), (71.600,10.400), lay=I)
via('ULPI_NXT', (71.600, 10.400))
trk('ULPI_NXT', (71.600,10.400), (70.200,10.800), lay=B)
via('ULPI_NXT', (70.200, 10.800))
trk('ULPI_NXT', (70.200,10.800), (70.200,6.900), lay=I)
trk('ULPI_NXT', (70.200,6.900), (71.100,4.900), lay=I)
via('ULPI_NXT', (71.100, 4.900))
trk('ULPI_NXT', (71.100,4.900), (70.500,3.400), lay=B)
trk('ULPI_NXT', (70.500,3.400), (69.450,2.200), lay=B)
via('ULPI_NXT', (69.450, 2.200))
trk('ULPI_NXT', (69.450,2.200), (69.450,-0.500), lay=B)
trk('ULPI_NXT', (69.450,-0.500), (69.300,-0.650), lay=B)

zr = pcbnew.ZONE_FILLER(b); zr.Fill(b.Zones())
b.Save(OUT); print("saved", OUT)
b2 = pcbnew.LoadBoard(OUT)
for n in NETS:
    c = sum(1 for t in b2.GetTracks() if t.GetNetname() == n)
    print(f"reload {n}: {c} items")

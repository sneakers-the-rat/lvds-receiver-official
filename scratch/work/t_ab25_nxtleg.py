"""t_ab25: hand-routed ULPI_NXT on the DIR-routed board (t_ab23).

DIR (routed by t_ab2 with NXT's column + mouth corridor blocked)
partitions the pocket for any second A* run: its B diagonal
splits the lobe and its B seg2b walls the REFCLK window's north
half. This NXT route was designed against full dumps:
  F stub to dive via (74.75,18.6) - south of DIR's B seg1 line,
    clear of C20.1 (+0.525), XI via, DM vertical (+0.50)
  B east-lobe run staying east/south of DIR's B tracks, west of
    XO's B web, down to (68.8,32.3)
  B channel approach from the south: (66.4,32.5)->(66.6,30.0)
    via - the y30.0 sliver in the DM<->REFCLK channel (margins
    +0.02 DM / +0.01 REFCLK / +0.05 DIR via by hand geometry)
  F exit west, via (65.9,26.0), B west run south-offset from
    DIR's B west track, via (61.7,13.3), In2 east paralleling
    DIR's In2 (+0.6..0.9), via (68.9,0.2), F into U6.29.
All tracks w0.2, vias d0.5/drill0.3. Refill + reload count.
"""
import wx
_app = wx.App(False)
import pcbnew

SRC = 'scratch/work/t_ab23.kicad_pcb'
OUT = 'scratch/work/t_ab25.kicad_pcb'
b = pcbnew.LoadBoard(SRC)
M = pcbnew.FromMM; MM = pcbnew.ToMM
V = lambda x, y: pcbnew.VECTOR2I(M(x), M(y))
CODE = b.GetNetcodeFromNetname('ULPI_NXT')
assert CODE > 0
F, I2, B = pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu

LEGS = [
    (F, [(75.25, 16.438), (75.25, 17.2), (74.9, 17.9),
         (74.75, 18.6)]),
    (B, [(74.75, 18.6), (71.5, 20.0), (70.5, 26.5), (69.8, 29.5),
         (68.8, 32.3), (66.4, 32.5), (66.6, 30.0)]),
    (F, [(66.6, 30.0), (65.9, 28.6), (65.9, 26.0)]),
    (B, [(65.9, 26.0), (64.8, 25.5), (63.0, 22.5), (61.3, 14.8),
         (61.7, 13.3)]),
    (I2, [(61.7, 13.3), (60.4, 9.2), (60.5, 8.7), (68.9, 0.2)]),
    (F, [(68.9, 0.2), (70.5, -0.75), (71.0, -0.75)]),
]
VIAS = [(74.75, 18.6), (66.6, 30.0), (65.9, 26.0), (61.7, 13.3),
        (68.9, 0.2)]

def trk(a, bb, layer):
    t = pcbnew.PCB_TRACK(b); t.SetNetCode(CODE)
    t.SetStart(V(*a)); t.SetEnd(V(*bb)); t.SetWidth(M(0.2))
    t.SetLayer(layer); b.Add(t)

n = 0
for layer, pts in LEGS:
    for a, bb in zip(pts, pts[1:]):
        trk(a, bb, layer); n += 1
for (x, y) in VIAS:
    v = pcbnew.PCB_VIA(b); v.SetPosition(V(x, y))
    v.SetWidth(M(0.5)); v.SetDrill(M(0.3))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetNetCode(CODE)
    b.Add(v)
print(f'emitted {n} segs, {len(VIAS)} vias')

zr = pcbnew.ZONE_FILLER(b); zr.Fill(b.Zones())
b.Save(OUT); print('saved', OUT)
b2 = pcbnew.LoadBoard(OUT)
c = sum(1 for t in b2.GetTracks() if t.GetNetname() == 'ULPI_NXT')
print(f'reload ULPI_NXT: {c} items (expect {n + len(VIAS)})')

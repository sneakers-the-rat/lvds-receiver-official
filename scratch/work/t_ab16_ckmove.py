"""t_ab16: ULPI_CK dive-via relocation (trial on t_ab10 board).

Pass 182's packing proof: no DRC-legal first dive exists south
of U7.13 (ULPI_STP) while CK's via stands at (76.62,17.30).
Move CK's via east to (76.90,18.10):
  - +3V3A via (77.875,17.75) d0.8: centre dist 1.036 >= 0.90
  - PHY_1V8 pad SW corner (77.125,16.878): stub edge +0.035
  - PHY stub / SQUELCH / XI via: all >= 1.0 away
Rip: CK F stub (76.75,16.438)->(76.62,17.30), the via, and the
In2 southern leg (76.62,17.30)->(76.62,13.50).
Re-lay: F stub (76.75,16.438)->(76.90,18.10), via d0.6 (as the
original), In2 (76.90,18.10)->(76.90,13.50)->(76.62,13.50)
joining the standing trunk westward. CK stays connected;
expected audited delta ZERO. Opens STP's dive field around
(76.35,17.55) (0.778 from the new CK via).
"""
import wx
_app = wx.App(False)
import pcbnew

SRC = 'scratch/work/t_ab10.kicad_pcb'
OUT = 'scratch/work/t_ab16.kicad_pcb'
b = pcbnew.LoadBoard(SRC)
M = pcbnew.FromMM; MM = pcbnew.ToMM
V = lambda x, y: pcbnew.VECTOR2I(M(x), M(y))
CODE = b.GetNetcodeFromNetname('ULPI_CK')
assert CODE > 0

def key(a, bb):
    return frozenset(((round(a[0], 3), round(a[1], 3)),
                      (round(bb[0], 3), round(bb[1], 3))))

rip_segs = {key((76.75, 16.438), (76.62, 17.30)),
            key((76.62, 17.30), (76.62, 13.50))}
n_rip = 0
for t in list(b.GetTracks()):
    if t.GetNetname() != 'ULPI_CK':
        continue
    if isinstance(t, pcbnew.PCB_VIA):
        p = MM(t.GetPosition())
        if abs(p[0] - 76.62) < 0.01 and abs(p[1] - 17.30) < 0.01:
            b.Remove(t); n_rip += 1
        continue
    s, e = t.GetStart(), t.GetEnd()
    if key((MM(s.x), MM(s.y)), (MM(e.x), MM(e.y))) in rip_segs:
        b.Remove(t); n_rip += 1
print(f'ripped {n_rip} CK items (expect 3)')
assert n_rip == 3

def trk(a, bb, layer, w=0.2):
    t = pcbnew.PCB_TRACK(b); t.SetNetCode(CODE)
    t.SetStart(V(*a)); t.SetEnd(V(*bb)); t.SetWidth(M(w))
    t.SetLayer(layer); b.Add(t)

trk((76.75, 16.438), (76.90, 18.10), pcbnew.F_Cu)
v = pcbnew.PCB_VIA(b); v.SetPosition(V(76.90, 18.10))
v.SetWidth(M(0.6)); v.SetDrill(M(0.3))
v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetNetCode(CODE); b.Add(v)
trk((76.90, 18.10), (76.90, 13.50), pcbnew.In2_Cu, 0.25)
trk((76.90, 13.50), (76.62, 13.50), pcbnew.In2_Cu, 0.25)
print('laid CK re-lay: F stub, via (76.90,18.10), In2 leg')

zr = pcbnew.ZONE_FILLER(b); zr.Fill(b.Zones())
b.Save(OUT); print('saved', OUT)
b2 = pcbnew.LoadBoard(OUT)
c = sum(1 for t in b2.GetTracks() if t.GetNetname() == 'ULPI_CK')
print(f'reload ULPI_CK: {c} items')

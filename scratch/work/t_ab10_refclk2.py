"""t_ab10: REFCLK In2 window re-lay v2 (trial on exp212).

Same stretch as t_ab9 ((68.875,27.875)->(66.375,31.625)) but a
GROWING east shift: +0.50 at the first step, +0.06 per step, to
+1.04 at the south vertical. The XO In2 vertical (x69.625,
y27.125..31.625) caps only the northernmost step (centerline
gap >= 0.45); points further south sit further from it, so the
shift can grow. DM<->REFCLK channel widens from ~1.25 (north)
to ~1.66 (south) mm, giving via bands with real margin under
the DRC-rule model (via needs >=0.579 from each centerline).
REFCLK stays connected; expected audited delta ZERO.
"""
import wx
_app = wx.App(False)
import pcbnew

SRC = 'hw/pdlvds_rx.exp212.kicad_pcb'
OUT = 'scratch/work/t_ab10.kicad_pcb'
b = pcbnew.LoadBoard(SRC)
M = pcbnew.FromMM; MM = pcbnew.ToMM
V = lambda x, y: pcbnew.VECTOR2I(M(x), M(y))
CODE = b.GetNetcodeFromNetname('REFCLK')
assert CODE > 0

OLD = [(68.875, 27.875), (68.625, 28.125), (68.375, 28.375),
       (68.125, 28.625), (67.875, 28.875), (67.625, 29.125),
       (67.375, 29.375), (67.125, 29.625), (66.875, 29.875),
       (66.625, 30.125), (66.375, 30.375), (66.375, 31.625)]
SH = [0.0, 0.50, 0.56, 0.62, 0.68, 0.74, 0.80, 0.86, 0.92, 0.98,
      1.04, 1.04]
NEW = [(x + s, y) for (x, y), s in zip(OLD, SH)] + [OLD[-1]]

def key(a, bb):
    return frozenset(((round(a[0], 3), round(a[1], 3)),
                      (round(bb[0], 3), round(bb[1], 3))))

want = {key(a, bb): None for a, bb in zip(OLD, OLD[1:])}
for t in list(b.GetTracks()):
    if isinstance(t, pcbnew.PCB_VIA) or t.GetNetname() != 'REFCLK':
        continue
    if t.GetLayer() != pcbnew.In2_Cu:
        continue
    s, e = t.GetStart(), t.GetEnd()
    k = key((MM(s.x), MM(s.y)), (MM(e.x), MM(e.y)))
    if k in want:
        want[k] = t
missing = [k for k, v in want.items() if v is None]
assert not missing, f'rip targets not found: {missing}'
for t in want.values():
    b.Remove(t)
print(f'ripped {len(want)} REFCLK In2 segs')

def trk(a, bb):
    t = pcbnew.PCB_TRACK(b); t.SetNetCode(CODE)
    t.SetStart(V(*a)); t.SetEnd(V(*bb)); t.SetWidth(M(0.25))
    t.SetLayer(pcbnew.In2_Cu); b.Add(t)

for a, bb in zip(NEW, NEW[1:]):
    trk(a, bb)
print(f'laid {len(NEW) - 1} segs')

zr = pcbnew.ZONE_FILLER(b); zr.Fill(b.Zones())
b.Save(OUT); print('saved', OUT)
b2 = pcbnew.LoadBoard(OUT)
c = sum(1 for t in b2.GetTracks() if t.GetNetname() == 'REFCLK')
print(f'reload REFCLK: {c} items (exp212: 53)')

"""t_ab9: REFCLK In2 window re-lay (trial on exp212).

Re-lays REFCLK's In2 staircase stretch from (68.875,27.875) to
(66.375,31.625) east by +0.50 mm. The stretch runs ~0.75 mm east
of DM_PHY's In2 wall; the trio (ULPI_NXT/DIR/STP) is sealed in
the U7 pocket and this DM<->REFCLK channel in the southern run
(DM x~66-68.4 In2, DP converged onto the same line on B) is the
cheapest wall crossing: widening it to ~1.25 mm makes via
centres legal (need >=0.579 from each centerline). East bound:
XO's In2 vertical x69.625 (REFCLK centerline must stay <=69.175
for 0.45 centerline gap; +0.50 shift puts the top step at
69.125, gap 0.50). REFCLK stays connected end-to-end; expected
audited delta ZERO. Refill + reload netname/count check.
"""
import wx
_app = wx.App(False)
import pcbnew

SRC = 'hw/pdlvds_rx.exp212.kicad_pcb'
OUT = 'scratch/work/t_ab9.kicad_pcb'
b = pcbnew.LoadBoard(SRC)
M = pcbnew.FromMM; MM = pcbnew.ToMM
V = lambda x, y: pcbnew.VECTOR2I(M(x), M(y))
CODE = b.GetNetcodeFromNetname('REFCLK')
assert CODE > 0

OLD = [(68.875, 27.875), (68.625, 28.125), (68.375, 28.375),
       (68.125, 28.625), (67.875, 28.875), (67.625, 29.125),
       (67.375, 29.375), (67.125, 29.625), (66.875, 29.875),
       (66.625, 30.125), (66.375, 30.375), (66.375, 31.625)]
NEW = [(68.875, 27.875), (69.125, 28.125), (68.875, 28.375),
       (68.625, 28.625), (68.375, 28.875), (68.125, 29.125),
       (67.875, 29.375), (67.625, 29.625), (67.375, 29.875),
       (67.125, 30.125), (66.875, 30.375), (66.875, 31.625),
       (66.375, 31.625)]

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
print(f'reload REFCLK: {c} items')

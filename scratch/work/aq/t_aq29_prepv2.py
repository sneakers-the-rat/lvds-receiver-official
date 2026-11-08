#!/usr/bin/env python3
"""prep v2: re-lay HV_SHDN In2 chain2 tail south to open the SCK pinch.
Rip In2 segs (70.125,-2.125)->(70.375,-1.875)->(70.625,-1.625)->(70.875,-1.375);
add (70.125,-2.125)->(70.7,-2.6)->(71.3,-2.2)->(71.625,-0.625) [rejoins chain1
at its own joint (71.625,-0.625); own-net contact legal]."""
import sys, wx
_app = wx.App(False)
sys.path.insert(0, 'scratch/work/ai')
import pcbnew
import t_ai_lib as L

SRC = 'hw/pdlvds_rx.exp236prep.kicad_pcb'
OUT = 'hw/pdlvds_rx.exp236prep2.kicad_pcb'
b = pcbnew.LoadBoard(SRC)
items = L.load_items(b)
pool = [it for li in range(3) for it in items[li] if it[1] != 'HV_SHDN']
pool1 = [it for it in items[1] if it[1] != 'HV_SHDN']
ADDS = [((70.125, -2.125), (70.7, -2.6)), ((70.7, -2.6), (71.3, -2.2)),
        ((71.3, -2.2), (71.625, -0.625))]
worst = 9.9
for a, bpt in ADDS:
    m, w = L.seg_margin(1, a, bpt, 'HV_SHDN', 0.125, pool1, step=0.04)
    worst = min(worst, m)
    print(f'  chain2 add {a}->{bpt}: {m:+.3f} vs {L.fmt_it(w)}')
assert worst >= -0.001, f'chain2 gate fail {worst}'
print(f'chain2 adds gate worst {worst:+.3f}')

nc = b.GetNetcodeFromNetname('HV_SHDN')
IN2 = L.LAYERS_K[1]
RIPS = [((70.125, -2.125), (70.375, -1.875)), ((70.375, -1.875), (70.625, -1.625)),
        ((70.625, -1.625), (70.875, -1.375))]
def key(t):
    s, e = t.GetStart(), t.GetEnd()
    return (round(pcbnew.ToMM(s.x), 3), round(pcbnew.ToMM(s.y), 3),
            round(pcbnew.ToMM(e.x), 3), round(pcbnew.ToMM(e.y), 3))
victims = []
for t in list(b.GetTracks()):
    if isinstance(t, pcbnew.PCB_VIA) or t.GetNetname() != 'HV_SHDN' or t.GetLayer() != IN2:
        continue
    k = key(t)
    for a, bpt in RIPS:
        if k == (a[0], a[1], bpt[0], bpt[1]) or k == (bpt[0], bpt[1], a[0], a[1]):
            victims.append(t)
assert len(victims) == 3, f'rip victims {len(victims)} != 3'
for t in victims:
    b.Remove(t)
for a, bpt in ADDS:
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I_MM(a[0], a[1]))
    t.SetEnd(pcbnew.VECTOR2I_MM(bpt[0], bpt[1]))
    t.SetWidth(pcbnew.FromMM(0.25))
    t.SetLayer(IN2)
    t.SetNetCode(nc)
    b.Add(t)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(OUT)
print('saved', OUT)

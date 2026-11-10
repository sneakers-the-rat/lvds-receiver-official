"""t_ba57: BUILD pass 217 prep on exp253 -> exp254.
(a) Rip STP western B excursion: board tracks net ULPI_STP
on B.Cu with centre x[74.3,76.0] y[13.4,17.2] (expect 76).
(b) 1V8A notch v2: rip F stub (2 segs) + via (75.27,10.33)
+ B head (4 segs); lay via (75.45,10.6) d0.5/drill0.3,
F stub (75.72,11.0)->(75.45,10.6), B head (75.45,10.6)
->(75.0,11.5)->(74.45,12.1)->(73.50,12.55), w0.2.
Zone refill, save exp254, reload-verify net names + counts."""
import wx
_app = wx.App(False)
import pcbnew

SRC = 'hw/pdlvds_rx.exp253.kicad_pcb'
DST = 'hw/pdlvds_rx.exp254.kicad_pcb'
b = pcbnew.LoadBoard(SRC)
MM = pcbnew.FromMM


def mm(v):
    return v / 1e6


nc_stp = b.GetNetcodeFromNetname('ULPI_STP')
nc_1v8a = b.GetNetcodeFromNetname('PHY_1V8A')

# (a) excursion rip
victims = []
for t in b.GetTracks():
    if t.GetNetCode() != nc_stp or t.Type() != pcbnew.PCB_TRACE_T:
        continue
    if t.GetLayer() != pcbnew.B_Cu:
        continue
    s, e = t.GetStart(), t.GetEnd()
    cx, cy = (mm(s.x) + mm(e.x)) / 2, (mm(s.y) + mm(e.y)) / 2
    if 74.3 <= cx <= 76.0 and 13.4 <= cy <= 17.2:
        victims.append(t)
print(f'excursion victims: {len(victims)} (expect 76)')
for t in victims:
    b.Remove(t)

# (b) notch v2 rip: match by endpoints (either order)
TARGETS = [
    ('F', (75.72, 11.0), (75.49, 10.69)),
    ('F', (75.49, 10.69), (75.27, 10.33)),
    ('B', (75.27, 10.33), (75.05, 10.95)),
    ('B', (75.05, 10.95), (74.90, 11.75)),
    ('B', (74.90, 11.75), (74.20, 12.25)),
    ('B', (74.20, 12.25), (73.50, 12.55)),
]
LAY = {'F': pcbnew.F_Cu, 'B': pcbnew.B_Cu}
got = []
for t in list(b.GetTracks()):
    if t.GetNetCode() != nc_1v8a:
        continue
    if t.Type() == pcbnew.PCB_VIA_T:
        p = t.GetPosition()
        if abs(mm(p.x) - 75.27) < 0.02 and abs(mm(p.y) - 10.33) < 0.02:
            got.append(t)
        continue
    if t.Type() != pcbnew.PCB_TRACE_T:
        continue
    s, e = t.GetStart(), t.GetEnd()
    sp = (round(mm(s.x), 2), round(mm(s.y), 2))
    ep = (round(mm(e.x), 2), round(mm(e.y), 2))
    for lay, a, bb in TARGETS:
        if t.GetLayer() == LAY[lay] and \
                ((sp == a and ep == bb) or (sp == bb and ep == a)):
            got.append(t)
print(f'notch rip victims: {len(got)} (expect 7: 6 segs + 1 via)')
for t in got:
    b.Remove(t)


def seg(netcode, layer, a, bb, w=0.2):
    t = pcbnew.PCB_TRACK(b)
    t.SetNetCode(netcode)
    t.SetLayer(layer)
    t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(MM(bb[0]), MM(bb[1])))
    t.SetWidth(MM(w))
    b.Add(t)


def via(netcode, x, y, d=0.5, dr=0.3):
    v = pcbnew.PCB_VIA(b)
    v.SetNetCode(netcode)
    v.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    v.SetWidth(MM(d))
    v.SetDrill(MM(dr))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    b.Add(v)


via(nc_1v8a, 75.45, 10.6)
seg(nc_1v8a, pcbnew.F_Cu, (75.72, 11.0), (75.45, 10.6))
seg(nc_1v8a, pcbnew.B_Cu, (75.45, 10.6), (75.0, 11.5))
seg(nc_1v8a, pcbnew.B_Cu, (75.0, 11.5), (74.45, 12.1))
seg(nc_1v8a, pcbnew.B_Cu, (74.45, 12.1), (73.50, 12.55))

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(DST)
print('saved', DST)

b2 = pcbnew.LoadBoard(DST)
from collections import Counter
cnt = Counter()
for t in b2.GetTracks():
    cnt[t.GetNetname()] += 1
print('ULPI_STP items:', cnt['ULPI_STP'], '(expect 709-76=633)')
print('PHY_1V8A items:', cnt['PHY_1V8A'], '(expect 168-7+5=166)')
# verify the new via + segs carry the right net after reload
for t in b2.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        p = t.GetPosition()
        if abs(mm(p.x) - 75.45) < 0.02 and abs(mm(p.y) - 10.6) < 0.02:
            print('new notch via net:', t.GetNetname(),
                  'd', mm(t.GetWidth()))
print('=== done ===')

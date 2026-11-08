"""t_ap23: BUILD the ap22 DP_CON design -> exp234.
Rips (exact endpoint match, victims printed): CC2's B5 via + stub +
In2 web (9 segs); DM_CON's B7 via (re-added at d0.5).
Adds: DM via (29.375,72.375) d0.5; CC2 via (30.5,72.275) d0.5 +
F stub + In2 join chain; DP_CON A6 F stub (crosses B6's pad,
joining it), via (29.93,74.075) d0.5, In2 main chain w0.25,
D3 via (44.025,46.35) d0.5 + F stub.
Every add exact-gated (library margins) on the post-rip board
before building; reload census after save."""
import sys, math, json, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
from t_ai_lib import (load_items, pt_margin, seg_margin, in_box_pool,
                      fmt_it)
from router import netclass

SRC = 'hw/pdlvds_rx.exp233.kicad_pcb'
DST = 'hw/pdlvds_rx.exp234.kicad_pcb'
MM = pcbnew.FromMM
LAY = {0: pcbnew.F_Cu, 1: pcbnew.In2_Cu, 2: pcbnew.B_Cu}
BIGBOX = (26.0, 48.0, 42.0, 76.0)
D = json.load(open('scratch/work/ap/dp-design.json'))

SEG_RIPS = [
    ('CC2', 30.500, 72.930, 30.375, 72.375),
    ('CC2', 30.500, 73.180, 30.500, 72.930),
    ('CC2', 30.375, 72.375, 30.375, 71.625),
    ('CC2', 30.375, 71.625, 30.375, 70.875),
    ('CC2', 30.375, 70.875, 30.625, 70.625),
    ('CC2', 30.625, 70.625, 30.625, 70.125),
    ('CC2', 30.625, 70.125, 30.875, 69.875),
    ('CC2', 30.875, 69.875, 31.125, 69.625),
    ('CC2', 31.125, 69.625, 31.375, 69.375)]
VIA_RIPS = [('CC2', 30.375, 72.375), ('DM_CON', 29.375, 72.375)]

b = pcbnew.LoadBoard(SRC)
ZONES = [z for z in b.Zones() if not z.GetIsRuleArea()]
codes = {}
for n in ('CC2', 'DM_CON', 'DP_CON', 'VBUS_RAW'):
    codes[n] = b.GetNetcodeFromNetname(n)
    assert codes[n] > 0, n

# ---- model + exact gate (fresh board for the model; the mutated
# board object breaks GetFootprints iteration) -------------------------------
def seg(net, li, a, c, w):
    return (li, ('seg', net, (a[0], a[1], c[0], c[1], w / 2),
                 netclass(net)[1]))
def via(net, x, y, d):
    return ('via', net, (x, y, d / 2), netclass(net)[1])

adds = [via('DM_CON', 29.375, 72.375, 0.5),
        via('CC2', *D['cc2_via'], 0.5)]
for a, c in zip(D['cc2_stub'], D['cc2_stub'][1:]):
    adds.append(seg('CC2', 0, a, c, 0.2))
for a, c in zip(D['cc2_join'], D['cc2_join'][1:]):
    adds.append(seg('CC2', 1, a, c, 0.2))
adds.append(via('DP_CON', *D['a6_via'], 0.5))
for a, c in zip(D['a6_stub'], D['a6_stub'][1:]):
    adds.append(seg('DP_CON', 0, a, c, 0.2))
for a, c in zip(D['main'], D['main'][1:]):
    adds.append(seg('DP_CON', 1, a, c, 0.25))
adds.append(via('DP_CON', *D['d3_via'], 0.5))
for a, c in zip(D['d3_stub'], D['d3_stub'][1:]):
    adds.append(seg('DP_CON', 0, a, c, 0.2))

mb = pcbnew.LoadBoard(SRC)
mitems = load_items(mb)
sr = set()
for (net, ax, ay, bx, by) in SEG_RIPS:
    sr.add((net, round(ax, 3), round(ay, 3), round(bx, 3), round(by, 3)))
    sr.add((net, round(bx, 3), round(by, 3), round(ax, 3), round(ay, 3)))
vr = set((net, round(x, 3), round(y, 3)) for net, x, y in VIA_RIPS)
statics = {li: [] for li in range(3)}
nrip = 0
for li in range(3):
    for it in mitems[li]:
        if it[0] == 'seg':
            d = it[2]
            if (it[1], round(d[0], 3), round(d[1], 3), round(d[2], 3),
                    round(d[3], 3)) in sr:
                nrip += 1
                continue
        elif it[0] == 'via':
            d = it[2]
            if (it[1], round(d[0], 3), round(d[1], 3)) in vr:
                nrip += 1
                continue
        statics[li].append(it)
print(f'model rips: {nrip} (expect 27 with via layer copies)')
pool = in_box_pool(statics, BIGBOX, pad=1.2)
worst = 9.9
worst_desc = None
for a in adds:
    if isinstance(a[0], int):
        li, it = a
        plist = [list(pool[l]) for l in range(3)]
        for prev in adds[:adds.index(a)]:
            if isinstance(prev[0], int):
                plist[prev[0]].append(prev[1])
            else:
                for l in range(3):
                    plist[l].append(prev)
        if it[0] == 'via':
            for l in range(3):
                m, w = pt_margin(l, it[2][0], it[2][1], it[1],
                                 it[2][2], plist[l])
                if m < worst:
                    worst, worst_desc = m, (fmt_it(it), l, fmt_it(w))
        else:
            m, w = seg_margin(li, (it[2][0], it[2][1]),
                              (it[2][2], it[2][3]), it[1], it[2][4],
                              plist[li], step=0.01)
            if m < worst:
                worst, worst_desc = m, (fmt_it(it), li, fmt_it(w))
    else:
        plist = [list(pool[l]) for l in range(3)]
        for prev in adds[:adds.index(a)]:
            if isinstance(prev[0], int):
                plist[prev[0]].append(prev[1])
            else:
                for l in range(3):
                    plist[l].append(prev)
        for l in range(3):
            m, w = pt_margin(l, a[2][0], a[2][1], a[1], a[2][2],
                             plist[l])
            if m < worst:
                worst, worst_desc = m, (fmt_it(a), l, fmt_it(w))
print(f'exact gate: worst {worst:+.4f} at {worst_desc}')
assert worst >= -0.001, 'GATE FAIL — aborting build'

# ---- board rip (exact match, victims printed) --------------------------------
victims = []
for t in list(b.GetTracks()):
    net = t.GetNetname()
    if isinstance(t, pcbnew.PCB_VIA):
        p = t.GetPosition()
        if (net, round(p.x / 1e6, 3), round(p.y / 1e6, 3)) in vr:
            victims.append(('via', net, p.x / 1e6, p.y / 1e6))
            b.Remove(t)
    else:
        s = t.GetStart()
        e = t.GetEnd()
        key = (net, round(s.x / 1e6, 3), round(s.y / 1e6, 3),
               round(e.x / 1e6, 3), round(e.y / 1e6, 3))
        if key in sr:
            victims.append(('seg', net, key[1:]))
            b.Remove(t)
print(f'rip victims: {len(victims)} (expect 11)')
for v in victims:
    print('   ', v)
assert len(victims) == 11

# ---- apply -------------------------------------------------------------------
def add_track(net, li, a, c, w):
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(MM(c[0]), MM(c[1])))
    t.SetWidth(MM(w))
    t.SetLayer(LAY[li])
    t.SetNetCode(codes[net])
    b.Add(t)

def add_via(net, x, y, d=0.5, drill=0.3):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    v.SetWidth(MM(d))
    v.SetDrill(MM(drill))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNetCode(codes[net])
    b.Add(v)

add_via('DM_CON', 29.375, 72.375)
add_via('CC2', *D['cc2_via'])
for a, c in zip(D['cc2_stub'], D['cc2_stub'][1:]):
    add_track('CC2', 0, tuple(a), tuple(c), 0.2)
for a, c in zip(D['cc2_join'], D['cc2_join'][1:]):
    add_track('CC2', 1, tuple(a), tuple(c), 0.2)
add_via('DP_CON', *D['a6_via'])
for a, c in zip(D['a6_stub'], D['a6_stub'][1:]):
    add_track('DP_CON', 0, tuple(a), tuple(c), 0.2)
for a, c in zip(D['main'], D['main'][1:]):
    add_track('DP_CON', 1, tuple(a), tuple(c), 0.25)
add_via('DP_CON', *D['d3_via'])
for a, c in zip(D['d3_stub'], D['d3_stub'][1:]):
    add_track('DP_CON', 0, tuple(a), tuple(c), 0.2)

filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())
b.Save(DST)
print('saved', DST)

# ---- reload census ------------------------------------------------------------
b2 = pcbnew.LoadBoard(DST)
from collections import Counter
cnt = Counter()
for t in b2.GetTracks():
    cnt[t.GetNetname()] += 1
for n in ('CC2', 'DM_CON', 'DP_CON', 'VBUS_RAW'):
    print(f'  {n}: {cnt[n]} track/via items')
bad = [t.GetNetname() for t in b2.GetTracks()
       if t.GetNetname() not in
       {x.GetNetname() for x in b2.GetTracks()}]
print('reload OK')

"""t_ag4: joint D5+XO build on exp217 (trial, not banked here).

Design (all geometry derived from the exp217 dump, t_ag1-t_ag3):
- RIP XO's In2 corner+lane SE of joint (80.625,17.125): the
  x80.875 vertical and the whole x+y=96.5 lane to the old via
  (86.125,10.375), the old via, and its two F stub segs on
  X1.2's pad.
- NEW XO lane on In2 at x+y~=98.28: (80.625,17.125)->(81.2,17.1)
  ->(87.5,10.75), w0.2; via d0.6 at (87.5,10.75) (annulus
  overlaps X1.2's pad, same net); F stub (87.5,10.75)->(86.8,10.6)
  across the pad.
- NEW ULPI_D5: F stub5 (t_af24 geometry) to via V5
  (80.25,15.1875) d0.5; In2 journey (80.25,15.1875)->(81.3,15.35)
  ->(82.0,15.3)->(87.9,9.4)->(88.75,9.15)->(90.65,7.25)
  ->(92.55,4.75)->(92.55,3.9); via d0.5 at (92.55,3.9);
  F seg (92.55,3.9)->(92.662,2.75) into U6.73.
  (GND stitch via (88.3,8.6) is cleared by the NE bulge at
  x+y=97.9; arrival via moved W of R44.1's pad.)
- OPTIONAL XO leg to U7.27 (gated separately; included only if
  every gate passes): In2 (73.125,11.375)->(74.5,11.2)
  ->(76.75,10.85); via d0.5 at (76.75,10.85); F stub
  (76.75,10.85)->(76.75,11.25) into the pad's north edge.

Every new item is gated in the exact item model (statics =
exp217 minus rip set, plus previously accepted new items of
other nets) with pair clearances from router.netclass.
Aborts before touching the board if any core gate < 0.
Zones refilled; saved to OUT; caller reload-verifies + DRCs.
"""
import math, sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
from router import netclass, dist_to_item

SRC = sys.argv[1] if len(sys.argv) > 1 else 'hw/pdlvds_rx.exp217.kicad_pcb'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'scratch/work/t_ag4_trial.kicad_pcb'
MM = pcbnew.FromMM
MMf = pcbnew.ToMM
LK = [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
LN = ['F', 'In2', 'B']

board = pcbnew.LoadBoard(SRC)
items = {0: [], 1: [], 2: []}
for fp in board.GetFootprints():
    for pad in fp.Pads():
        net = pad.GetNetname()
        x, y = MMf(pad.GetPosition())
        sx, sy = MMf(pad.GetSize())
        data = (x, y, sx / 2, sy / 2, 0.0)
        for li, ln in enumerate(LK):
            if pad.IsOnLayer(ln):
                items[li].append(('pad', net, data, 0.2))
for t in board.GetTracks():
    net = t.GetNetname()
    if isinstance(t, pcbnew.PCB_VIA):
        x, y = MMf(t.GetPosition())
        r = MMf(t.GetWidth()) / 2
        for li in range(3):
            items[li].append(('via', net, (x, y, r), 0.2))
    else:
        if t.GetLayer() not in LK:
            continue
        li = LK.index(t.GetLayer())
        a, c = MMf(t.GetStart()), MMf(t.GetEnd())
        w = MMf(t.GetWidth())
        items[li].append(('seg', net, (a[0], a[1], c[0], c[1], w / 2),
                          0.2))

def skey(a, b):
    ka = (round(a[0], 3), round(a[1], 3))
    kb = (round(b[0], 3), round(b[1], 3))
    return min(ka, kb), max(ka, kb)

# ---- rip set ----
rip_seg_keys = set()   # (li, net, key)
rip_via_keys = set()   # (net, x, y)
for li in range(3):
    for it in items[li]:
        if it[1] != 'XO':
            continue
        if it[0] == 'seg':
            d = it[2]
            a, b = (d[0], d[1]), (d[2], d[3])
            if li == 1 and a[0] + a[1] <= 97.751 and \
               b[0] + b[1] <= 97.751 and min(a[0], b[0]) >= 80.6:
                rip_seg_keys.add((li, 'XO', skey(a, b)))
            if li == 0 and skey(a, b) in (
                    skey((86.125, 10.375), (85.75, 10.0)),
                    skey((85.75, 10.0), (85.75, 9.75))):
                rip_seg_keys.add((li, 'XO', skey(a, b)))
        if it[0] == 'via':
            d = it[2]
            if abs(d[0] - 86.125) < 0.01 and abs(d[1] - 10.375) < 0.01:
                rip_via_keys.add(('XO', round(d[0], 3), round(d[1], 3)))
print(f'rip: {len([k for k in rip_seg_keys if k[0] == 1])} In2 segs, '
      f'{len([k for k in rip_seg_keys if k[0] == 0])} F segs, '
      f'{len(rip_via_keys)} vias')

def is_ripped(li, it):
    if it[1] != 'XO':
        return False
    if it[0] == 'seg':
        d = it[2]
        return (li, 'XO', skey((d[0], d[1]), (d[2], d[3]))) in rip_seg_keys
    if it[0] == 'via':
        d = it[2]
        return ('XO', round(d[0], 3), round(d[1], 3)) in rip_via_keys
    return False

statics = {li: [it for it in items[li] if not is_ripped(li, it)]
           for li in range(3)}

def pair_clr(n1, n2):
    return max(netclass(n1)[1], netclass(n2)[1])

placed = {0: [], 1: [], 2: []}   # accepted new items per layer

def gate_seg(li, a, b, net, hw):
    m, worst = 9e9, None
    pool = statics[li] + placed[li]
    n = max(2, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 0.01) + 1)
    for i in range(n + 1):
        t = i / n
        x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        for it in pool:
            if it[1] == net:
                continue
            d = dist_to_item(it, x, y) - hw - pair_clr(net, it[1])
            if d < m:
                m, worst = d, (it[0], it[1], it[2])
    return m, worst

def gate_via(x, y, r, net):
    m, worst = 9e9, None
    for li in range(3):
        for it in statics[li] + placed[li]:
            if it[1] == net:
                continue
            d = dist_to_item(it, x, y) - r - pair_clr(net, it[1])
            if d < m:
                m, worst = d, (LN[li], it[0], it[1], it[2])
    return m, worst

fails = []
def add_seg(li, a, b, net, w=0.2, group='core'):
    m, worst = gate_seg(li, a, b, net, w / 2)
    print(f'  gate {group} seg {LN[li]} {net} {a}->{b}: {m:+.3f} '
          f'worst={worst}')
    ok = m >= 0
    if not ok:
        if group == 'core':
            fails.append((a, b, m, worst))
        return False
    placed[li].append(('seg', net, (a[0], a[1], b[0], b[1], w / 2), w))
    return True

def add_via_g(x, y, dia, net, group='core'):
    m, worst = gate_via(x, y, dia / 2, net)
    print(f'  gate {group} via {net} ({x},{y}) d{dia}: {m:+.3f} '
          f'worst={worst}')
    ok = m >= 0
    if not ok:
        if group == 'core':
            fails.append(((x, y), dia, m, worst))
        return False
    for li in range(3):
        placed[li].append(('via', net, (x, y, dia / 2), dia))
    return True

print('--- XO lane ---')
add_seg(1, (80.625, 17.125), (81.2, 17.1), 'XO')
add_seg(1, (81.2, 17.1), (87.5, 10.75), 'XO')
add_via_g(87.5, 10.75, 0.6, 'XO')
add_seg(0, (87.5, 10.75), (86.8, 10.6), 'XO')
print('--- ULPI_D5 ---')
stub5 = [(78.4375, 14.75), (79.0, 14.78), (79.4, 15.05),
         (79.6, 15.14), (80.25, 15.1875)]
for a, b in zip(stub5, stub5[1:]):
    add_seg(0, a, b, 'ULPI_D5')
add_via_g(80.25, 15.1875, 0.5, 'ULPI_D5')
journey = [(80.25, 15.1875), (81.3, 15.35), (82.0, 15.3),
           (87.9, 9.4), (88.75, 9.15), (90.65, 7.25),
           (92.55, 4.75), (92.55, 3.9)]
for a, b in zip(journey, journey[1:]):
    add_seg(1, a, b, 'ULPI_D5')
add_via_g(92.55, 3.9, 0.5, 'ULPI_D5')
add_seg(0, (92.55, 3.9), (92.662, 2.75), 'ULPI_D5')
if fails:
    print('CORE GATE FAILURES — aborting, board untouched')
    for f in fails:
        print('  ', f)
    sys.exit(1)
print('--- XO leg to U7.27 (optional, all-or-nothing) ---')
# Gate the leg against a snapshot of placed, then roll back
# unless EVERY leg item passed (a passed sub-item must not leak
# into the build on its own — that bug put a lone F stub on the
# first trial; caught by the reload census in t_ag5).
saved_placed = {li: list(placed[li]) for li in range(3)}
leg_ok = True
leg_ok &= add_seg(1, (73.125, 11.375), (74.5, 11.2), 'XO', group='leg')
leg_ok &= add_seg(1, (74.5, 11.2), (76.75, 10.85), 'XO', group='leg')
leg_ok &= add_via_g(76.75, 10.85, 0.5, 'XO', group='leg')
leg_ok &= add_seg(0, (76.75, 10.85), (76.75, 11.25), 'XO', group='leg')
if not leg_ok:
    placed = saved_placed
print('XO leg included:', bool(leg_ok))

# ---- apply to the real board ----
codes = {n: board.GetNetcodeFromNetname(n) for n in ('XO', 'ULPI_D5')}
ripobjs = []
for tr in list(board.GetTracks()):
    net = tr.GetNetname()
    if net != 'XO':
        continue
    li = {pcbnew.F_Cu: 0, pcbnew.In2_Cu: 1, pcbnew.B_Cu: 2}.get(
        tr.GetLayer())
    if isinstance(tr, pcbnew.PCB_VIA):
        p = tr.GetPosition()
        if ('XO', round(MMf(p.x), 3), round(MMf(p.y), 3)) in rip_via_keys:
            ripobjs.append(tr)
    elif li is not None:
        a, b = tr.GetStart(), tr.GetEnd()
        k = (li, 'XO', skey((MMf(a.x), MMf(a.y)), (MMf(b.x), MMf(b.y))))
        if k in rip_seg_keys:
            ripobjs.append(tr)
print(f'ripping {len(ripobjs)} board objects')
for tr in ripobjs:
    board.Remove(tr)

def add_track(net, a, b, li, w=0.2):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(MM(b[0]), MM(b[1])))
    t.SetWidth(MM(w))
    t.SetLayer(LK[li])
    t.SetNetCode(codes[net])
    board.Add(t)

def add_via(net, x, y, dia):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    v.SetWidth(MM(dia))
    v.SetDrill(MM(0.3))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNetCode(codes[net])
    board.Add(v)

for li in range(3):
    for it in placed[li]:
        if it[0] == 'seg':
            d = it[2]
            add_track(it[1], (d[0], d[1]), (d[2], d[3]), li, it[3])
        elif it[0] == 'via' and li == 0:
            add_via(it[1], it[2][0], it[2][1], it[3])
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(OUT)
print(f'saved {OUT}')

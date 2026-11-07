"""t_af18: build the D5-district trial board (candidate
exp217) from the af16 skeleton v3, with stub4 switched to
the direct diagonal (af16's jointed stub4 bound D5's stub
at -0.062; the direct seg (79.125,14.375)->V4 clears D3's
via by +0.107 and D5's stub by ~+0.09).

In-model gates before any copper is laid: all stub statics,
all F pairwise, both In2 connector segs (dense seg_margin
vs statics + sibling items). Aborts if any margin < 0.

Rip set = the af9 rip-3 set (23 items). New copper:
 D4 stub [(78.4375,14.25),(78.6875,14.25),(79.125,14.375),
     (79.96875,14.53125)] F w0.2; via d0.5/0.3 at V4;
     In2 seg V4 -> (80.625,13.875) (joint on kept staircase)
 D5 stub [(78.4375,14.75),(79.0,14.78),(79.4,15.05),
     (79.6,15.14),(80.25,15.1875)] F w0.2; via d0.5 at V5
 D6 stub [(78.4375,15.25),(78.6875,15.25),(79.125,15.375),
     (79.375,15.625),(79.875,15.625),(80.0,15.75),
     (80.875,15.75),(80.75,14.625)] F w0.2; via d0.6 at V6;
     In2 seg V6 -> (81.625,13.875)
D5's onward journey is left to t_ab2_groute on the output.
Zones refilled; saved; caller reload-verifies.
"""
import math, sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import repair
from router import dist_to_item

SRC = sys.argv[1] if len(sys.argv) > 1 else 'hw/pdlvds_rx.exp216.kicad_pcb'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'scratch/work/exp217cand2.kicad_pcb'
MM = pcbnew.FromMM
LAY = {'F': pcbnew.F_Cu, 'In2': pcbnew.In2_Cu, 'B': pcbnew.B_Cu}
LAYIDX = {'F': 0, 'In2': 1, 'B': 2}

board = pcbnew.LoadBoard(SRC)
# plain item lists, same construction as t_af9 (repair.build_items
# returns a bucketed Items registry, not plain lists)
from router import netclass as _nc
LAYERS_K = [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
items = {0: [], 1: [], 2: []}
for fp in board.GetFootprints():
    for pad in fp.Pads():
        net = pad.GetNetname()
        x, y = pcbnew.ToMM(pad.GetPosition())
        sx, sy = pcbnew.ToMM(pad.GetSize())
        data = (x, y, sx / 2, sy / 2,
                math.radians(pad.GetOrientationDegrees()))
        clr = _nc(net)[1] if net else 0.2
        for li, ln in enumerate(LAYERS_K):
            if pad.IsOnLayer(ln):
                items[li].append(('pad', net, data, clr))
for t in board.GetTracks():
    net = t.GetNetname()
    clr = _nc(net)[1] if net else 0.2
    if isinstance(t, pcbnew.PCB_VIA):
        x, y = pcbnew.ToMM(t.GetPosition())
        r = pcbnew.ToMM(t.GetWidth()) / 2
        for li in range(3):
            items[li].append(('via', net, (x, y, r), clr))
    else:
        if t.GetLayer() not in LAYERS_K:
            continue
        li = LAYERS_K.index(t.GetLayer())
        a = pcbnew.ToMM(t.GetStart()); b = pcbnew.ToMM(t.GetEnd())
        w = pcbnew.ToMM(t.GetWidth())
        items[li].append(('seg', net,
                          (a[0], a[1], b[0], b[1], w / 2), clr))
NETS = ('ULPI_D4', 'ULPI_D5', 'ULPI_D6')
PAD = {'ULPI_D4': (78.4375, 14.25), 'ULPI_D5': (78.4375, 14.75),
       'ULPI_D6': (78.4375, 15.25)}
A4 = (80.375, 14.125); A6 = (81.375, 14.125)
V4 = (79.96875, 14.53125); V5 = (80.25, 15.1875); V6 = (80.75, 14.625)
R = {'ULPI_D4': 0.25, 'ULPI_D5': 0.25, 'ULPI_D6': 0.30}
stub4 = [PAD['ULPI_D4'], (78.6875, 14.25), (79.125, 14.375), V4]
stub5 = [PAD['ULPI_D5'], (79.0, 14.78), (79.4, 15.05),
         (79.6, 15.14), V5]
stub6 = [PAD['ULPI_D6'], (78.6875, 15.25), (79.125, 15.375),
         (79.375, 15.625), (79.875, 15.625), (80.0, 15.75),
         (80.875, 15.75), V6]

# ---- rip set (same construction as t_af9) ----
RIPKEYS = set()
for net, nseg in (('ULPI_D4', 3), ('ULPI_D6', 3)):
    own = [(li, it) for li in range(3) for it in items[li]
           if it[1] == net]
    vias = [it for li, it in own if it[0] == 'via']
    vias = [min(vias, key=lambda it: math.hypot(
        it[2][0] - PAD[net][0], it[2][1] - PAD[net][1]))]
    vx, vy = vias[0][2][0], vias[0][2][1]
    for li in range(3):
        RIPKEYS.add((li, 'via', net,
                     (round(vx, 3), round(vy, 3),
                      round(vias[0][2][2], 3))))
    for layname, li in (('F', 0), ('In2', 1)):
        segs = [it[2] for it in items[li]
                if it[1] == net and it[0] == 'seg']
        chain, cur = [], (vx, vy)
        pool = list(segs)
        while pool:
            nxt = None
            for s in pool:
                a = (s[0], s[1]); b = (s[2], s[3])
                if math.hypot(a[0]-cur[0], a[1]-cur[1]) < 0.01:
                    nxt = (s, b); break
                if math.hypot(b[0]-cur[0], b[1]-cur[1]) < 0.01:
                    nxt = (s, a); break
            if nxt is None:
                break
            chain.append(nxt[0]); cur = nxt[1]; pool.remove(nxt[0])
        take = chain if layname == 'F' else chain[:nseg]
        for s in take:
            RIPKEYS.add((li, 'seg', net,
                         (round(s[0], 3), round(s[1], 3),
                          round(s[2], 3), round(s[3], 3),
                          round(s[4], 3))))

def key_of(li, it):
    if it[0] == 'via':
        return (li, 'via', it[1], (round(it[2][0], 3),
                round(it[2][1], 3), round(it[2][2], 3)))
    if it[0] == 'seg':
        return (li, 'seg', it[1], tuple(round(v, 3) for v in it[2]))
    return None

static = {li: [it for it in items[li]
               if key_of(li, it) not in RIPKEYS] for li in range(3)}
n_rip_model = sum(1 for li in range(3) for it in items[li]
                  if key_of(li, it) in RIPKEYS)
print(f'model rip count: {n_rip_model} (expect 23 entries '
      f'x layers present)')

from router import netclass
def pair_clr(na, nb):
    return max(netclass(na)[1], netclass(nb)[1])

def seg_margin(li, a, b, net, hw, pool, step=0.01):
    m = 9e9
    n = max(2, int(math.hypot(b[0]-a[0], b[1]-a[1]) / step) + 1)
    for i in range(n + 1):
        t = i / n
        x, y = a[0] + (b[0]-a[0])*t, a[1] + (b[1]-a[1])*t
        for it in pool:
            if it[1] == net:
                continue
            d = dist_to_item(it, x, y) - hw - pair_clr(net, it[1])
            if d < m:
                m = d
    return m

def poly_items(net, pts):
    return [('seg', net, (a[0], a[1], b[0], b[1], 0.1), 0.2)
            for a, b in zip(pts, pts[1:])]

def item_pair_margin(a, b):
    ka, kb = a[0], b[0]
    na, nb = a[1], b[1]
    clr = pair_clr(na, nb)
    da, db = a[2], b[2]
    if ka == 'via' and kb == 'via':
        return math.hypot(da[0]-db[0], da[1]-db[1]) - da[2] - db[2] - clr
    if ka == 'via' and kb == 'seg':
        s = ('seg', nb, db, b[3])
        return dist_to_item(s, da[0], da[1]) - da[2] - clr
    if ka == 'seg' and kb == 'via':
        return item_pair_margin(b, a)
    m = 9e9
    n = max(2, int(math.hypot(da[2]-da[0], da[3]-da[1]) / 0.01) + 1)
    sb = ('seg', nb, db, b[3])
    for i in range(n + 1):
        t = i / n
        x, y = da[0] + (da[2]-da[0])*t, da[1] + (da[3]-da[1])*t
        d = dist_to_item(sb, x, y) - 0.1 - clr
        if d < m:
            m = d
    return m

# ---- gates ----
fails = []
for net, sp in (('ULPI_D4', stub4), ('ULPI_D5', stub5),
                ('ULPI_D6', stub6)):
    for a, b in zip(sp, sp[1:]):
        m = seg_margin(0, a, b, net, 0.1, static[0])
        if m < 0:
            fails.append(f'{net} stub seg {a}->{b} statics {m:+.3f}')
def F_items(net, sp, V):
    return poly_items(net, sp) + [('via', net, (V[0], V[1], R[net]), 0.2)]
I4, I5, I6 = (F_items('ULPI_D4', stub4, V4), F_items('ULPI_D5', stub5, V5),
              F_items('ULPI_D6', stub6, V6))
for A, B, tag in ((I4, I5, 'D4-D5'), (I4, I6, 'D4-D6'), (I5, I6, 'D5-D6')):
    m = min(item_pair_margin(a, b) for a in A for b in B)
    print(f'F pairwise {tag}: {m:+.3f}')
    if m < 0:
        fails.append(f'F pairwise {tag} {m:+.3f}')
via4 = ('via', 'ULPI_D4', (V4[0], V4[1], R['ULPI_D4']), 0.2)
via5 = ('via', 'ULPI_D5', (V5[0], V5[1], R['ULPI_D5']), 0.2)
via6 = ('via', 'ULPI_D6', (V6[0], V6[1], R['ULPI_D6']), 0.2)
m = seg_margin(1, V4, A4, 'ULPI_D4', 0.1, static[1] + [via5, via6])
print(f'D4 In2 connector: {m:+.3f}')
if m < 0:
    fails.append(f'D4 In2 connector {m:+.3f}')
i4in2 = poly_items('ULPI_D4', [V4, A4])
m = seg_margin(1, V6, A6, 'ULPI_D6', 0.1,
               static[1] + [via4, via5] + i4in2)
print(f'D6 In2 connector: {m:+.3f}')
if m < 0:
    fails.append(f'D6 In2 connector {m:+.3f}')
for net, V in (('ULPI_D4', V4), ('ULPI_D5', V5), ('ULPI_D6', V6)):
    for li in range(3):
        mp = 9e9
        for it in static[li]:
            if it[1] == net:
                continue
            d = dist_to_item(it, V[0], V[1]) - R[net] - pair_clr(net, it[1])
            mp = min(mp, d)
        if mp < 0:
            fails.append(f'{net} via statics layer {li}: {mp:+.3f}')
if fails:
    print('GATE FAILURES:')
    for f in fails:
        print('  ', f)
    sys.exit(1)
print('all in-model gates pass')

# ---- rip on the real board ----
codes = {n: board.GetNetcodeFromNetname(n) for n in
         ('ULPI_D4', 'ULPI_D5', 'ULPI_D6')}
ripobjs = []
for tr in list(board.GetTracks()):
    net = tr.GetNetname()
    if net not in NETS:
        continue
    li = {pcbnew.F_Cu: 0, pcbnew.In2_Cu: 1, pcbnew.B_Cu: 2}.get(
        tr.GetLayer())
    if li is None:
        continue
    if isinstance(tr, pcbnew.PCB_VIA):
        p = tr.GetPosition()
        k = (li, 'via', net, (round(pcbnew.ToMM(p.x), 3),
             round(pcbnew.ToMM(p.y), 3),
             round(pcbnew.ToMM(tr.GetWidth()) / 2, 3)))
    else:
        a, b = tr.GetStart(), tr.GetEnd()
        k = (li, 'seg', net, (round(pcbnew.ToMM(a.x), 3),
             round(pcbnew.ToMM(a.y), 3), round(pcbnew.ToMM(b.x), 3),
             round(pcbnew.ToMM(b.y), 3),
             round(pcbnew.ToMM(tr.GetWidth()) / 2, 3)))
        k2 = (li, 'seg', net, (k[3][2], k[3][3], k[3][0], k[3][1],
              k[3][4]))
        if k in RIPKEYS or k2 in RIPKEYS:
            ripobjs.append(tr)
        continue
    if k in RIPKEYS:
        ripobjs.append(tr)
print(f'ripping {len(ripobjs)} board objects')
for tr in ripobjs:
    board.Remove(tr)

def add_track(net, a, b, layname, w=0.2):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(MM(b[0]), MM(b[1])))
    t.SetWidth(MM(w))
    t.SetLayer(LAY[layname])
    t.SetNetCode(codes[net])
    board.Add(t)

def add_via(net, V, dia):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(MM(V[0]), MM(V[1])))
    v.SetWidth(MM(dia))
    v.SetDrill(MM(0.3))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNetCode(codes[net])
    board.Add(v)

for net, sp in (('ULPI_D4', stub4), ('ULPI_D6', stub6)):
    for a, b in zip(sp, sp[1:]):
        add_track(net, a, b, 'F')
add_via('ULPI_D4', V4, 0.5)
add_via('ULPI_D6', V6, 0.6)
add_track('ULPI_D4', V4, A4, 'In2')
add_track('ULPI_D6', V6, A6, 'In2')

filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(OUT)
print(f'saved {OUT}')

"""t_an2: build the t_an1c winning HV design on a trial board.
Usage: t_an2_build.py in.kicad_pcb out.kicad_pcb
Reads scratch/work/an/hv-design.json (variant definitions identical
to t_an1c_hvopt3.py). Rips SHDN + +5V NE/SE re-fan pieces (+ run seg2
for V3), emits the design, zone-refills, saves, reload-census +
netname-verify of every emitted item. All adds gated in-model
(library-exact) vs statics+adds before anything is emitted; any
gate failure -> exit 1, nothing written."""
import sys, json, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
from t_ai_lib import (load_items, pt_margin, seg_margin, in_box_pool,
                      apply_rip, fmt_it)
from router import netclass

SRC, OUT = sys.argv[1], sys.argv[2]
D = json.load(open('scratch/work/an/hv-design.json'))
LAY = {'F': pcbnew.F_Cu, 'In2': pcbnew.In2_Cu, 'B': pcbnew.B_Cu}
LINAME = {0: 'F', 1: 'In2', 2: 'B'}
BOX = (29.0, 34.6, -6.4, 1.5)
A0 = (30.375, -3.0)
R0 = (30.775, -0.5)

def seg(net, li, a, c, w):
    return (li, ('seg', net, (a[0], a[1], c[0], c[1], w / 2),
                 netclass(net)[1]))
def via(net, x, y, d):
    return ('via', net, (x, y, d / 2), netclass(net)[1])

RIP_SHDN = [('via', 'HV_SHDN', 30.875, -2.875),
            ('seg', 'HV_SHDN', 30.625, -3.375),
            ('seg', 'HV_SHDN', 30.875, -3.125),
            ('seg', 'HV_SHDN', 30.875, -2.875)]
RIP_NE = [('seg', '+5V', 30.400, -4.000), ('seg', '+5V', 31.125, -3.875),
          ('seg', '+5V', 31.375, -3.625), ('seg', '+5V', 31.625, -3.375)]
RIP_SE = [('seg', '+5V', 31.625, -4.375), ('seg', '+5V', 31.375, -4.750)]
RIP_RUN2 = [('seg', '+5V', 29.650, -4.000)]
SE_OPTS = [((31.95, -4.20), (31.70, -5.10)),
           ((32.10, -4.35), (31.80, -5.05)),
           ((31.80, -4.10), (31.60, -5.15))]

def ne_refan():
    return [seg('+5V', 0, (31.150, -4.000), (31.550, -4.350), 0.6),
            seg('+5V', 0, (31.550, -4.350), (32.000, -3.900), 0.6),
            seg('+5V', 0, (32.000, -3.900), (31.950, -3.350), 0.6),
            seg('+5V', 0, (31.950, -3.350), (31.875, -3.125), 0.6)]

def se_refan(e1, e2):
    return [seg('+5V', 0, (31.150, -4.000), e1, 0.6),
            seg('+5V', 0, e1, e2, 0.6),
            seg('+5V', 0, e2, (31.375, -5.500), 0.6)]

def shdn_adds(sx, sy, sd, cx):
    adds = [via('HV_SHDN', sx, sy, sd),
            seg('HV_SHDN', 0, (30.375, -3.500), (sx, sy), 0.2)]
    if cx is None:
        adds.append(seg('HV_SHDN', 1, (sx, sy), (31.900, -2.875), 0.25))
        cx = 31.900
    else:
        adds.append(seg('HV_SHDN', 1, (sx, sy), (cx, sy), 0.25))
        adds.append(seg('HV_SHDN', 1, (cx, sy), (cx + 0.75, -2.875),
                        0.25))
        cx = cx + 0.75
    adds.append(seg('HV_SHDN', 1, (cx, -2.875), (43.375, -2.875), 0.25))
    return adds

def p5v_v3_adds(dx, in2y, rx):
    return [seg('+5V', 0, (29.650, -4.000), (dx, in2y), 0.2),
            via('+5V', dx, in2y, 0.6),
            seg('+5V', 1, (dx, in2y), (rx, in2y), 0.6),
            via('+5V', rx, in2y, 0.6),
            seg('+5V', 0, (rx, in2y), (31.150, -4.000), 0.2),
            seg('+5V', 0, (rx, in2y), (31.125, -3.875), 0.2)]

RIPS = list(RIP_SHDN + RIP_NE + RIP_SE)
adds = []
parts = D['variant'].split()
sei = int(parts[-1][2:])
if parts[0] == 'V3':
    RIPS += RIP_RUN2
    dx = float(parts[1][2:]); in2y = float(parts[2][1:])
    rx = float(parts[3][2:])
    adds += p5v_v3_adds(dx, in2y, rx)
adds += ne_refan() + se_refan(*SE_OPTS[sei])
sh = D['shdn']
adds += shdn_adds(sh['x'], sh['y'], sh['d'], sh['cx'])
Dv = tuple(D['dive']); Rv = tuple(D['rise']); L = D['journey_layer']
ch = [tuple(p) for p in D['journey']]
adds.append(via('HV_INTVCC', Dv[0], Dv[1], 0.5))
adds.append(seg('HV_INTVCC', 0, A0, Dv, 0.2))
for a_, b_ in zip(ch, ch[1:]):
    if a_ == b_:
        continue
    adds.append(seg('HV_INTVCC', L, a_, b_, 0.2))
adds.append(via('HV_INTVCC', Rv[0], Rv[1], 0.5))
adds.append(seg('HV_INTVCC', 0, Rv, R0, 0.2))

board0 = pcbnew.LoadBoard(SRC)
items = load_items(board0)
statics, nrip = apply_rip(items, RIPS)
print(f'model rips: {nrip}')
it2 = {li: list(statics[li]) for li in range(3)}
for ad in adds:
    if isinstance(ad[0], int):
        it2[ad[0]].append(ad[1])
    else:
        for li in range(3):
            it2[li].append(ad)
pool = in_box_pool(it2, BOX, pad=1.2)
fails = []
worst = []
for ad in adds:
    if isinstance(ad[0], int):
        li, o = ad
        if o[0] == 'seg':
            m, w = seg_margin(li, (o[2][0], o[2][1]), (o[2][2], o[2][3]),
                              o[1], o[2][4], pool[li])
        else:
            m, w = pt_margin(li, o[2][0], o[2][1], o[1], o[2][2],
                             pool[li])
        worst.append((m, o))
        if m < 0:
            fails.append((o, li, m, w))
    else:
        for li in range(3):
            m, w = pt_margin(li, ad[2][0], ad[2][1], ad[1], ad[2][2],
                             pool[li])
            worst.append((m, ad))
            if m < 0:
                fails.append((ad, li, m, w))
worst.sort(key=lambda t: t[0])
print('worst 8 in-model gates:')
for m, o in worst[:8]:
    print(f'   {m:+.3f} {o[1]} {o[0]} {o[2]}')
if fails:
    print('GATE FAILURES:')
    for o, li, m, w in fails:
        print(f'   {o[1]} {o[0]} {o[2]} L{li}: {m:+.3f} vs {fmt_it(w)}')
    sys.exit(1)
print('all in-model gates pass')

codes = {n: board0.GetNetcodeFromNetname(n)
         for n in ('HV_SHDN', '+5V', 'HV_INTVCC')}

def hit(t, spec):
    kind, net, x, y = spec
    if t.GetNetname() != net:
        return False
    if kind == 'via':
        if not isinstance(t, pcbnew.PCB_VIA):
            return False
        p = pcbnew.ToMM(t.GetPosition())
        return abs(p[0] - x) < 0.01 and abs(p[1] - y) < 0.01
    if isinstance(t, pcbnew.PCB_VIA):
        return False
    a_ = pcbnew.ToMM(t.GetStart()); b_ = pcbnew.ToMM(t.GetEnd())
    return (abs(a_[0] - x) < 0.01 and abs(a_[1] - y) < 0.01) or \
           (abs(b_[0] - x) < 0.01 and abs(b_[1] - y) < 0.01)

victims = [t for t in board0.GetTracks()
           if any(hit(t, s) for s in RIPS)]
print(f'ripping {len(victims)} board objects')
for t in victims:
    board0.Remove(t)

def add_track(net, a_, b_, layer, w):
    t = pcbnew.PCB_TRACK(board0)
    t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(a_[0]),
                               pcbnew.FromMM(a_[1])))
    t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(b_[0]),
                             pcbnew.FromMM(b_[1])))
    t.SetWidth(pcbnew.FromMM(w))
    t.SetLayer(LAY[layer])
    t.SetNetCode(codes[net])
    board0.Add(t)

def add_via(net, pt, dia, drill=0.3):
    v = pcbnew.PCB_VIA(board0)
    v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(pt[0]),
                                  pcbnew.FromMM(pt[1])))
    v.SetWidth(pcbnew.FromMM(dia))
    v.SetDrill(pcbnew.FromMM(drill))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNetCode(codes[net])
    board0.Add(v)

from collections import Counter
before = Counter(t.GetNetname() for t in board0.GetTracks())
for ad in adds:
    if isinstance(ad[0], int):
        li, o = ad
        add_track(o[1], (o[2][0], o[2][1]), (o[2][2], o[2][3]),
                  LINAME[li], o[2][4] * 2)
    else:
        add_via(ad[1], (ad[2][0], ad[2][1]), ad[2][2] * 2)
filler = pcbnew.ZONE_FILLER(board0)
filler.Fill(board0.Zones())
board0.Save(OUT)
print('saved', OUT)

b2 = pcbnew.LoadBoard(OUT)
after = Counter(t.GetNetname() for t in b2.GetTracks())
for net in ('HV_SHDN', '+5V', 'HV_INTVCC'):
    print(f'reload {net}: pre-build {before[net]} now {after[net]}')
ok = True
for ad in adds:
    if isinstance(ad[0], int):
        li, o = ad
        found = False
        for t in b2.GetTracks():
            if isinstance(t, pcbnew.PCB_VIA) or t.GetNetname() != o[1]:
                continue
            a_ = pcbnew.ToMM(t.GetStart()); b_ = pcbnew.ToMM(t.GetEnd())
            if abs(a_[0] - o[2][0]) < 0.01 and abs(a_[1] - o[2][1]) < 0.01 \
               and abs(b_[0] - o[2][2]) < 0.01 \
               and abs(b_[1] - o[2][3]) < 0.01 \
               and t.GetLayer() == LAY[LINAME[li]]:
                found = True
        if not found:
            print(f'  MISSING after save: {o[1]} seg {o[2]} L{li}')
            ok = False
    else:
        found = any(isinstance(t, pcbnew.PCB_VIA)
                    and t.GetNetname() == ad[1]
                    and abs(pcbnew.ToMM(t.GetPosition())[0] - ad[2][0])
                    < 0.01
                    and abs(pcbnew.ToMM(t.GetPosition())[1] - ad[2][1])
                    < 0.01
                    for t in b2.GetTracks())
        if not found:
            print(f'  MISSING after save: {ad[1]} via {ad[2]}')
            ok = False
print('reload census:', 'OK' if ok else 'MISMATCH')
sys.exit(0 if ok else 2)

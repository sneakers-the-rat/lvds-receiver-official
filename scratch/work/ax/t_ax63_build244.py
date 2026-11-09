"""t_ax54: build exp242 from exp241 per manifest_ax51.
- rip stub (F x2, In2 x4, via x1) + feed (A x1, B x2 twins, D x1),
  victim counts asserted per target (unordered rounded endpoints)
- move R20 -> (68.5,-1.75) rot 0
- add +3V3D re-join C', SCL F journey segs, +3V3D journey segs+vias
  (from manifest news; via d0.5/drill copied from staircase via)
- zone refill, save exp242, reload + census-verify netnames"""
import sys, json
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa

SRC = BOARD
DST = 'hw/pdlvds_rx.exp244.kicad_pcb'
LAY = {0: pcbnew.F_Cu, 1: pcbnew.In2_Cu, 2: pcbnew.B_Cu}
man = json.load(open('scratch/work/ax/manifest_ax62.json'))
b = pcbnew.LoadBoard(SRC)
nc = {n: b.GetNetcodeFromNetname(n) for n in ('I2C_SCL', '+3V3D', 'GND')}
print('netcodes:', nc, flush=True)
# layer sanity: the stub W chain track must be In2_Cu
for t in b.GetTracks():
    s = t.GetStart()
    if abs(s.x / 1e6 - 65.25) < 0.01 and abs(s.y / 1e6 - 8.5) < 0.01:
        print(f'W chain track layer: {t.GetLayerName()}', flush=True)
        break

RIPS = [  # (net, layer, p1, p2, expected victims)
    ('I2C_SCL', 0, (69.675, 12.75), (69.625, 12.625), 1),
    ('I2C_SCL', 0, (69.425, 12.75), (69.675, 12.75), 1),
    ('I2C_SCL', 1, (69.625, 12.625), (65.0, 12.5), 1),
    ('I2C_SCL', 1, (65.0, 12.5), (64.75, 12.0), 1),
    ('I2C_SCL', 1, (64.75, 12.0), (65.25, 8.5), 1),
    ('I2C_SCL', 1, (65.25, 8.5), (66.875, 6.75), 1),
    ('+3V3D', 0, (70.875, 12.625), (70.825, 12.75), 1),
    ('+3V3D', 0, (70.825, 12.75), (71.075, 12.75), 2),
    ('+3V3D', 0, (70.825, 12.75), (70.625, 12.375), 1),
]
ok = True
targets = {}
for (net, lay, p1, p2, exp) in RIPS:
    targets[(net, lay, frozenset((p1, p2)))] = []
stub_via = []
tmpl_holder = []
for t in b.GetTracks():
    tn = type(t).__name__
    if tn == 'PCB_TRACK':
        key = (t.GetNetname(), None, None)
        s, e = t.GetStart(), t.GetEnd()
        sp = (round(s.x / 1e6, 3), round(s.y / 1e6, 3))
        ep = (round(e.x / 1e6, 3), round(e.y / 1e6, 3))
        for (net, lay, pair), lst in targets.items():
            if t.GetNetname() == net and t.GetLayer() == LAY[lay] \
                    and frozenset((sp, ep)) == pair:
                lst.append(t)
    elif tn == 'PCB_VIA':
        px, py = t.GetPosition().x / 1e6, t.GetPosition().y / 1e6
        if t.GetNetname() == 'I2C_SCL' and abs(px - 69.625) < 0.01 \
                and abs(py - 12.625) < 0.01:
            stub_via.append(t)
        if abs(px - 72.875) < 0.01 and abs(py - 3.375) < 0.01:
            tmpl_holder.append(t)
for (net, lay, p1, p2, exp) in RIPS:
    got = len(targets[(net, lay, frozenset((p1, p2)))])
    print(f'rip {net} L{lay} {p1}->{p2}: {got} (expect {exp})',
          flush=True)
    if got != exp:
        ok = False
print(f'stub via victims: {len(stub_via)} (expect 1)', flush=True)
if len(stub_via) != 1:
    ok = False
if not ok:
    raise SystemExit('RIP COUNT MISMATCH - not saving')
for lst in targets.values():
    for v in lst:
        b.Remove(v)
for v in stub_via:
    b.Remove(v)
tmpl = tmpl_holder[0]

# move R20
for fp in b.GetFootprints():
    if fp.GetReference() == 'R20':
        fp.SetPosition(pcbnew.VECTOR2I(int(68.5 * 1e6),
                                       int(-1.75 * 1e6)))
        fp.SetOrientationDegrees(0)
        print('R20 moved; pads:',
              [(round(p.GetPosition().x / 1e6, 3),
                round(p.GetPosition().y / 1e6, 3), p.GetNetname())
               for p in fp.Pads()], flush=True)

# via template from the staircase via (collected in the single pass)
print(f'via template: width {tmpl.GetWidth() / 1e6} drill '
      f'{tmpl.GetDrillValue() / 1e6}', flush=True)


def add_seg(net, lay, d):
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(int(round(d[0] * 1e6)),
                               int(round(d[1] * 1e6))))
    t.SetEnd(pcbnew.VECTOR2I(int(round(d[2] * 1e6)),
                             int(round(d[3] * 1e6))))
    t.SetWidth(int(round(d[4] * 2 * 1e6)))
    t.SetLayer(LAY[lay])
    t.SetNetCode(nc[net])
    b.Add(t)


def add_via(net, x, y):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(pcbnew.VECTOR2I(int(round(x * 1e6)),
                                  int(round(y * 1e6))))
    v.SetWidth(tmpl.GetWidth())
    v.SetDrill(tmpl.GetDrillValue())
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNetCode(nc[net])
    b.Add(v)


nseg = nvia = 0
for e in man['news']:
    if e[0] == 'seg':
        _, net, lay, d = e
        add_seg(net, lay, tuple(d))
        nseg += 1
    elif e[0] == 'via':
        _, net, (x, y), r = e
        add_via(net, x, y)
        nvia += 1
print(f'added {nseg} segs, {nvia} vias', flush=True)
# GND stitch via for fill island26 at (67.29,0.86)
v = pcbnew.PCB_VIA(b)
v.SetPosition(pcbnew.VECTOR2I(int(67.29 * 1e6), int(0.86 * 1e6)))
v.SetWidth(tmpl.GetWidth())
v.SetDrill(tmpl.GetDrillValue())
v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
v.SetNetCode(nc['GND'])
b.Add(v)
print('added GND stitch via (67.29,0.86)', flush=True)
# zone refill
filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())
b.Save(DST)
print('saved', DST, flush=True)
# reload verify
b2 = pcbnew.LoadBoard(DST)
bad = 0
for t in b2.GetTracks():
    s = t.GetStart()
    if 66.0 < s.x / 1e6 < 74.0 and -10.0 < s.y / 1e6 < 4.0:
        pass
for fp in b2.GetFootprints():
    if fp.GetReference() == 'R20':
        print('R20 at', fp.GetPosition().x / 1e6,
              fp.GetPosition().y / 1e6, 'rot',
              fp.GetOrientationDegrees(), flush=True)
cnt = {'I2C_SCL': 0, '+3V3D': 0}
for t in b2.GetTracks():
    if t.GetNetname() in cnt:
        cnt[t.GetNetname()] += 1
print('track counts after:', cnt, flush=True)

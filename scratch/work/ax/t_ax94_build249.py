"""t_ax94: build exp249 from exp248 (CDR_LOS item).
- move C14 (72.0,36.75) -> (74.75,34.75) rot 0
- rip REFCLKN stub seg (71.225,36.95)->(71.7,37.55) (1 victim)
- rip SDA old F chain pad->via (model chain; victims asserted)
- add SDA re-lay (hw0.125), LOS journey (hw0.10, 4 vias),
  REFCLKN rejoin (hw0.10) from los_design_ax93.json
- zone refill, save exp249, reload census + fragment verify"""
import sys, json
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa

SRC = 'hw/pdlvds_rx.exp248.kicad_pcb'
DST = 'hw/pdlvds_rx.exp249.kicad_pcb'
LAY = {0: pcbnew.F_Cu, 1: pcbnew.In2_Cu, 2: pcbnew.B_Cu}
pool = load_board_pool(SRC)
des = json.load(open('scratch/work/ax/los_design_ax93.json'))

sda_old = chain_segs(pool, 'I2C_SDA', 0, (68.6875, 37.0), (72.125, 32.625))
print('model SDA old chain:', len(sda_old), 'segs', flush=True)
stub = [it for it in pool[0] if it[1] == 'REFCLKN' and it[0] == 'seg'
        and abs(it[2][0] - 71.7) < 0.01 and abs(it[2][1] - 37.55) < 0.01]
print('model REFCLKN stub:', len(stub), flush=True)

b = pcbnew.LoadBoard(SRC)
NETS = ('I2C_SDA', 'CDR_LOS', 'REFCLKN')
nc = {n: b.GetNetcodeFromNetname(n) for n in NETS}
print('netcodes:', nc, flush=True)

targets = {}
for it in sda_old + stub:
    d = it[2]
    p1 = (round(d[0], 3), round(d[1], 3))
    p2 = (round(d[2], 3), round(d[3], 3))
    targets.setdefault((it[1], 0, frozenset((p1, p2))), [])
tmpl_holder = []
for t in b.GetTracks():
    tn = type(t).__name__
    if tn == 'PCB_TRACK':
        s, e = t.GetStart(), t.GetEnd()
        sp = (round(s.x / 1e6, 3), round(s.y / 1e6, 3))
        ep = (round(e.x / 1e6, 3), round(e.y / 1e6, 3))
        key = (t.GetNetname(), 0, frozenset((sp, ep)))
        if key in targets and t.GetLayer() == LAY[0]:
            targets[key].append(t)
    elif tn == 'PCB_VIA':
        px, py = t.GetPosition().x / 1e6, t.GetPosition().y / 1e6
        if abs(px - 72.875) < 0.01 and abs(py - 3.375) < 0.01:
            tmpl_holder.append(t)
ok = True
for key, lst in targets.items():
    print(f'rip {key[0]} {sorted(key[2])}: {len(lst)} victim(s)', flush=True)
    if len(lst) != 1:
        ok = False
if not ok or not tmpl_holder:
    raise SystemExit('RIP COUNT MISMATCH - not saving')
for lst in targets.values():
    for v in lst:
        b.Remove(v)
tmpl = tmpl_holder[0]
print(f'via template: width {tmpl.GetWidth() / 1e6} drill '
      f'{tmpl.GetDrillValue() / 1e6}', flush=True)

for fp in b.GetFootprints():
    if fp.GetReference() == 'C14':
        fp.SetPosition(pcbnew.VECTOR2I(int(74.75 * 1e6),
                                       int(34.75 * 1e6)))
        fp.SetOrientationDegrees(0)
        print('C14 moved; pads:',
              [(round(p.GetPosition().x / 1e6, 3),
                round(p.GetPosition().y / 1e6, 3), p.GetNetname())
               for p in fp.Pads()], flush=True)


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
for key, net, hw in (('sda', 'I2C_SDA', 0.125),
                     ('los', 'CDR_LOS', 0.10),
                     ('refclkn', 'REFCLKN', 0.10)):
    J = des[key]
    its = journey_items_dense(J, net, hw=hw)
    for lay in range(3):
        for it in its[lay]:
            if it[0] == 'seg':
                add_seg(net, lay, it[2])
                nseg += 1
    for (x, y) in J['vias']:
        add_via(net, x, y)
        nvia += 1
print(f'added {nseg} segs, {nvia} vias', flush=True)

filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())
b.Save(DST)
print('saved', DST, flush=True)

b2 = pcbnew.LoadBoard(DST)
for fp in b2.GetFootprints():
    if fp.GetReference() == 'C14':
        print('C14 at', fp.GetPosition().x / 1e6, fp.GetPosition().y / 1e6,
              'rot', fp.GetOrientationDegrees(), flush=True)
cnt = {n: 0 for n in NETS + ('CDR_LOS',)}
for t in b2.GetTracks():
    if t.GetNetname() in cnt:
        cnt[t.GetNetname()] += 1
print('track counts after:', cnt, flush=True)
pool2 = load_board_pool(DST)
for net, box in (('CDR_LOS', (60.0, 100.0, -30.0, 45.0)),
                 ('I2C_SDA', (60.0, 100.0, -30.0, 45.0)),
                 ('REFCLKN', (60.0, 100.0, -30.0, 45.0))):
    fs = fragsets(pool2, net, box)
    print(f'{net}: {len(fs)} fragment(s), sizes '
          f'{sorted((len(f["items"]) for f in fs), reverse=True)}',
          flush=True)

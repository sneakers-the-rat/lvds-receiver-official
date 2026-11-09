"""t_av12: physical build of exp241 from exp241esc by ITEM DELTA.

The gated model (pool_av1.json, saved by the design script) is the
ground truth: removals = items_full(esc) - target, additions =
target - items_full(esc), computed as multisets on rounded keys.
Pads are never added/removed: U9 shifts -1.25 in x and C49 moves to
the design's chosen centre (moves recorded in build_av1.json);
the pad deltas must be exactly those two footprints' pads.

After building: zone refill, save, reload, and assert the saved
board's item multiset EQUALS the target pool exactly.
"""
import wx
_app = wx.App(False)
import sys, json
from collections import Counter
sys.path.insert(0, 'scratch/work/au')
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
import pcbnew
import t_ai_lib as L

SRC = 'hw/pdlvds_rx.exp241esc.kicad_pcb'
OUT = 'hw/pdlvds_rx.exp241.kicad_pcb'
LAY = {0: pcbnew.F_Cu, 1: pcbnew.In2_Cu, 2: pcbnew.B_Cu}

man = json.load(open('scratch/work/av/build_av1.json'))
target = {int(l): [(it[0], it[1], tuple(it[2]), it[3]) for it in lst]
          for l, lst in json.load(
              open('scratch/work/av/pool_av1.json')).items()}

board = pcbnew.LoadBoard(SRC)
items_full = L.load_items(board)


def key(it):
    kind, net, d = it[0], it[1], it[2]
    if kind == 'seg':
        a = (round(d[0], 4), round(d[1], 4))
        b = (round(d[2], 4), round(d[3], 4))
        if b < a:
            a, b = b, a
        return (kind, net, a, b, round(d[4], 4))
    if kind == 'via':
        return (kind, net, round(d[0], 4), round(d[1], 4),
                round(d[2], 4))
    return (kind, net, tuple(round(v, 4) for v in d))


removals, additions = {}, {}
for l in range(3):
    cf = Counter(key(it) for it in items_full[l])
    ct = Counter(key(it) for it in target[l])
    removals[l] = cf - ct
    additions[l] = ct - cf
    print(f'L{l}: esc {sum(cf.values())} target {sum(ct.values())} '
          f'remove {sum(removals[l].values())} '
          f'add {sum(additions[l].values())}', flush=True)

# pad deltas must be exactly U9 (7, shifted -1.25x) + C49 (2, moved)
mv = man['moves']['C49']
c49_from, c49_to = tuple(mv['from']), tuple(mv['to'])
pad_rem_keys = Counter()
pad_add_keys = Counter()
for l in range(3):
    for k in removals[l]:
        if k[0] == 'pad':
            pad_rem_keys[k] += removals[l][k]
    for k in additions[l]:
        if k[0] == 'pad':
            pad_add_keys[k] += additions[l][k]
print('pad removals:', dict(pad_rem_keys), flush=True)
print('pad additions:', dict(pad_add_keys), flush=True)
assert sum(pad_rem_keys.values()) == 9 and \
    sum(pad_add_keys.values()) == 9, \
    'pad delta is not exactly U9 (7) + C49 (2)'

# ---- capture netcodes BEFORE any Remove()
all_nets = set()
for l in range(3):
    for it in target[l]:
        all_nets.add(it[1])
codes = {n: board.GetNetcodeFromNetname(n) for n in all_nets if n}
print(f'netcodes captured: {len(codes)}', flush=True)

# ---- moves
u9 = c49 = None
for fp in board.GetFootprints():
    fx, fy = pcbnew.ToMM(fp.GetPosition())
    if abs(fx - 68.25) < 0.01 and abs(fy - 2.75) < 0.01:
        u9 = fp
    if abs(fx - c49_from[0]) < 0.01 and abs(fy - c49_from[1]) < 0.01:
        c49 = fp
assert u9 is not None and u9.GetReference() == 'U9', u9
assert c49 is not None and c49.GetReference() == 'C49', c49
u9.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(68.25 - 1.25),
                               pcbnew.FromMM(2.75)))
c49.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(c49_to[0]),
                                pcbnew.FromMM(c49_to[1])))
print(f'U9 -> (67.0,2.75); C49 -> {c49_to}', flush=True)

# ---- removals (tracks + vias; pads excluded - they moved)
want_rem = Counter()
for l in range(3):
    for k, c in removals[l].items():
        if k[0] != 'pad':
            want_rem[k] += c
# seg keys are per-layer; via keys appear once per layer (x3) - the
# board holds ONE via object per key, so divide via counts by 3
via_keys = {k: c for k, c in want_rem.items() if k[0] == 'via'}
for k in via_keys:
    assert via_keys[k] % 3 == 0, (k, via_keys[k])
    want_rem[k] = via_keys[k] // 3

victims = []
for tr in board.GetTracks():
    net = tr.GetNetname()
    if isinstance(tr, pcbnew.PCB_VIA):
        x, y = pcbnew.ToMM(tr.GetPosition())
        k = ('via', net, round(x, 4), round(y, 4),
             round(pcbnew.ToMM(tr.GetWidth()) / 2, 4))
        if want_rem.get(k, 0) > 0:
            victims.append(tr)
            want_rem[k] -= 1
    else:
        li = {v: kk for kk, v in LAY.items()}[tr.GetLayer()]
        a = pcbnew.ToMM(tr.GetStart())
        b = pcbnew.ToMM(tr.GetEnd())
        k = ('seg', net,
             (round(a[0], 4), round(a[1], 4)),
             (round(b[0], 4), round(b[1], 4)),
             round(pcbnew.ToMM(tr.GetWidth()) / 2, 4))
        kk = ('seg', net, min(k[2], k[3]), max(k[2], k[3]), k[4])
        if want_rem.get(kk, 0) > 0:
            victims.append(tr)
            want_rem[kk] -= 1
leftover = {k: c for k, c in want_rem.items() if c > 0}
print(f'removal victims found: {len(victims)}; unmatched: {leftover}',
      flush=True)
assert not leftover, 'removal keys unmatched on the board'
for v in victims:
    board.Remove(v)
print(f'removed {len(victims)} board items', flush=True)

# ---- additions
existing_vias = Counter()
existing_segs = Counter()
for tr in board.GetTracks():
    net = tr.GetNetname()
    if isinstance(tr, pcbnew.PCB_VIA):
        x, y = pcbnew.ToMM(tr.GetPosition())
        existing_vias[(net, round(x, 3), round(y, 3))] += 1
    else:
        a = pcbnew.ToMM(tr.GetStart())
        b = pcbnew.ToMM(tr.GetEnd())
        existing_segs[(net, tr.GetLayer(),
                       (round(a[0], 3), round(a[1], 3)),
                       (round(b[0], 3), round(b[1], 3)))] += 1

add_vias = Counter()
add_segs = []
for l in range(3):
    for k, c in additions[l].items():
        if k[0] == 'via':
            add_vias[(k[1], k[2], k[3], k[4])] += c
        elif k[0] == 'seg':
            for _ in range(c):
                add_segs.append((l, k))
for k in add_vias:
    assert add_vias[k] % 3 == 0, (k, add_vias[k])
    add_vias[k] //= 3
print(f'addition vias (distinct): {len(add_vias)}; '
      f'addition segs: {len(add_segs)}', flush=True)

skipped_vias = skipped_segs = 0
for (net, x, y, r), c in add_vias.items():
    for _ in range(c):
        if existing_vias.get((net, round(x, 3), round(y, 3)), 0) > 0:
            skipped_vias += 1
            existing_vias[(net, round(x, 3), round(y, 3))] -= 1
            continue
        v = pcbnew.PCB_VIA(board)
        v.SetNetCode(codes[net])
        v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x),
                                      pcbnew.FromMM(y)))
        v.SetWidth(pcbnew.FromMM(2 * r))
        v.SetDrill(pcbnew.FromMM(0.3))
        board.Add(v)
for (l, k) in add_segs:
    _, net, a, b, hw = k
    skey = (net, LAY[l], (round(a[0], 3), round(a[1], 3)),
            (round(b[0], 3), round(b[1], 3)))
    skey_r = (net, LAY[l], skey[3], skey[2])
    if existing_segs.get(skey, 0) > 0 or existing_segs.get(skey_r, 0) > 0:
        skipped_segs += 1
        continue
    t = pcbnew.PCB_TRACK(board)
    t.SetNetCode(codes[net])
    t.SetLayer(LAY[l])
    t.SetWidth(pcbnew.FromMM(2 * hw))
    t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(a[0]), pcbnew.FromMM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(b[0]), pcbnew.FromMM(b[1])))
    board.Add(t)
print(f'added vias/segs; skipped duplicates: {skipped_vias} vias, '
      f'{skipped_segs} segs', flush=True)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
board.Save(OUT)
print('saved', OUT, flush=True)

# ---- reload census: item multiset must equal the target pool
b2 = pcbnew.LoadBoard(OUT)
items2 = L.load_items(b2)
ok = True
for l in range(3):
    c2 = Counter(key(it) for it in items2[l])
    ct = Counter(key(it) for it in target[l])
    if c2 != ct:
        ok = False
        print(f'L{l} MISMATCH: only-in-board {dict((c2 - ct))} '
              f'only-in-target {dict((ct - c2))}', flush=True)
print('RELOAD CENSUS MATCH' if ok else 'RELOAD CENSUS FAILED',
      flush=True)
assert ok
print('t_av12 DONE', flush=True)

"""t_ax6: SCL bridge design in the exact model on exp241.
Window via W=(67.4,5.65). Sequence:
 0. BEFORE fragment counts (GND/LOL/+3V3D/SCL) in district box.
 1. Place SCL via + In2 approach seg (66.875,6.75)->W (gate seg).
 2. M1 GND In2 staircase re-lay W: rip chain (66.375,6.125)->via
    (67.375,4.125); A* In2 (66.375,6.125)->(67.375,4.125).
 3. M2 CDR_LOL B band re-lay E: rip chain (67.625,6.625)->(68.38,4.12);
    A* B (67.625,6.625)->(68.38,4.12).
 4. M3 +3V3D F jog re-lay N: rip chain (67.38,6.62)->(68.62,6.12);
    A* F hw0.3 (67.38,6.62)->(68.62,6.12).
 5. M4 bridge B ride: A* B W->(69.35,1.4).
 6. AFTER fragment counts + full gate of every new item."""
import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa

pool = load_board_pool()
W = (67.4, 5.65)
DIST = (55, 82, -10, 18)


def frag_count(net):
    return len(fragments(net, DIST))


def chain_segs(net, l, start, end):
    """Walk micro-segs of net on layer l from start to end (rounded
    endpoint chaining). Returns the list of pool items."""
    segs = [it for it in pool[l] if it[1] == net and it[0] == 'seg']
    bypt = {}
    for it in segs:
        d = it[2]
        bypt.setdefault((round(d[0], 3), round(d[1], 3)), []).append(it)
        bypt.setdefault((round(d[2], 3), round(d[3], 3)), []).append(it)
    out = []
    cur = (round(start[0], 3), round(start[1], 3))
    goal = (round(end[0], 3), round(end[1], 3))
    guard = 0
    while cur != goal and guard < 500:
        guard += 1
        cands = []
        for it in bypt.get(cur, []):
            if it in out:
                continue
            d = it[2]
            a = (round(d[0], 3), round(d[1], 3))
            b = (round(d[2], 3), round(d[3], 3))
            far = b if a == cur else a
            dist = (far[0] - goal[0]) ** 2 + (far[1] - goal[1]) ** 2
            cands.append((dist, it, far))
        if not cands:
            raise SystemExit(f'chain walk stuck at {cur} for {net} L{l}')
        cands.sort(key=lambda t: t[0])
        _, nxt, far = cands[0]
        out.append(nxt)
        cur = far
    if cur != goal:
        raise SystemExit(f'chain walk did not reach {goal} for {net} L{l}')
    return out


def gate_journey(tag, J, net, hw):
    its = journey_items_dense(J, net, hw=hw)
    worst = []
    for l in range(3):
        for it in its[l]:
            for o in pool[l]:
                if o[1] == net:
                    continue
                m = item_margin(l, it, [o])
                if m < 0.05:
                    worst.append((m, l, it, o))
    worst.sort(key=lambda t: t[0])
    print(f'{tag} worst pairs:', flush=True)
    for (m, l, it, o) in worst[:4]:
        print(f'   {m:+.3f} L{l} {L.fmt_it(it)} vs {L.fmt_it(o)}', flush=True)
    ok = not worst or worst[0][0] >= -0.001
    print(f'{tag}: {"GATE OK" if ok else "GATE FAIL"}', flush=True)
    return ok, its


def emit(tag, J, net, hw):
    ok, its = gate_journey(tag, J, net, hw)
    if ok:
        add_items(its)
        print(f'{tag} EMITTED', flush=True)
    return ok


print('BEFORE:', {n: frag_count(n) for n in
                  ('I2C_SCL', 'GND', 'CDR_LOL', '+3V3D')}, flush=True)

# 1. SCL via + In2 approach seg (gated at the END: its binder is the
# GND diagonal step that M1 re-lays west; pre-move margin is -0.011
# vs that step, per t_ax7)
seg = ('seg', 'I2C_SCL', (66.875, 6.75, W[0], W[1], 0.10), 0.2)
m = item_margin(1, seg, pool[1])
print(f'In2 approach seg margin (pre-move): {m:+.3f}', flush=True)
add_items({1: [seg]})
via = ('via', 'I2C_SCL', (W[0], W[1], 0.25), 0.2)
add_items({0: [via], 1: [via], 2: [via]})
for l in range(3):
    mm = item_margin(l, via, pool[l])
    print(f'  via margin L{l} (pre-move): {mm:+.3f}', flush=True)

# 2. M1 GND In2 re-lay
rip = chain_segs('GND', 1, (66.375, 6.125), (67.375, 4.125))
print(f'M1 rip {len(rip)} GND In2 segs', flush=True)
n = rip_items(rip)
assert n == len(rip), f'M1 rip count {n} != {len(rip)}'
astar = make_astar((65.4, 68.2, 3.4, 7.0), 0.025)
J = astar('GND', ((1,), 66.375, 6.125), (1, 67.375, 4.125), hw=0.125)
print(f'M1 A*: {"FOUND" if J else "NONE"}', flush=True)
if J:
    print('   vias:', J['vias'],
          'runs:', [(r['layer'], len(r['pts'])) for r in J['runs']],
          flush=True)
    emit('M1 GND relay', J, 'GND', 0.125)

# 3. M2 LOL B re-lay
rip = chain_segs('CDR_LOL', 2, (67.625, 6.625), (68.38, 4.12))
print(f'M2 rip {len(rip)} CDR_LOL B segs', flush=True)
n = rip_items(rip)
assert n == len(rip), f'M2 rip count {n} != {len(rip)}'
astar = make_astar((66.6, 69.6, 3.4, 7.4), 0.025)
J = astar('CDR_LOL', ((2,), 67.625, 6.625), (2, 68.38, 4.12), hw=0.125)
print(f'M2 A*: {"FOUND" if J else "NONE"}', flush=True)
if J:
    print('   vias:', J['vias'],
          'runs:', [(r['layer'], len(r['pts'])) for r in J['runs']],
          flush=True)
    emit('M2 LOL relay', J, 'CDR_LOL', 0.125)

# 4. M3 +3V3D F jog re-lay
rip = chain_segs('+3V3D', 0, (67.38, 6.62), (68.62, 6.12))
print(f'M3 rip {len(rip)} +3V3D F segs', flush=True)
n = rip_items(rip)
assert n == len(rip), f'M3 rip count {n} != {len(rip)}'
astar = make_astar((66.6, 69.6, 5.2, 7.6), 0.025)
J = astar('+3V3D', ((0,), 67.38, 6.62), (0, 68.62, 6.12), hw=0.30)
print(f'M3 A*: {"FOUND" if J else "NONE"}', flush=True)
if J:
    print('   vias:', J['vias'],
          'runs:', [(r['layer'], len(r['pts'])) for r in J['runs']],
          flush=True)
    emit('M3 +3V3D relay', J, '+3V3D', 0.30)

# via + approach margins after fence moves
for l in range(3):
    mm = item_margin(l, via, pool[l])
    print(f'  via margin L{l} (post-move): {mm:+.3f}', flush=True)
mm = item_margin(1, seg, pool[1])
print(f'In2 approach seg margin (post-move): {mm:+.3f}', flush=True)

# 5. M4 bridge B ride
astar = make_astar((66.8, 70.2, 0.8, 6.2), 0.025)
J = astar('I2C_SCL', ((2,), W[0], W[1]), (2, 69.35, 1.4), hw=0.10)
print(f'M4 A*: {"FOUND" if J else "NONE"}', flush=True)
if J:
    print('   vias:', J['vias'],
          'runs:', [(r['layer'], len(r['pts'])) for r in J['runs']],
          flush=True)
    emit('M4 bridge B', J, 'I2C_SCL', 0.10)

print('AFTER:', {n: frag_count(n) for n in
                 ('I2C_SCL', 'GND', 'CDR_LOL', '+3V3D')}, flush=True)
fr = fragments('I2C_SCL', DIST)
for i, f in enumerate(fr):
    has_w = any(it[0] == 'via' and abs(it[2][0] - W[0]) < 0.01
                and abs(it[2][1] - W[1]) < 0.01 for (l, it) in f['items'])
    has_pocket = any(it[0] == 'via' and abs(it[2][0] - 69.35) < 0.01
                     and abs(it[2][1] - 1.4) < 0.01
                     for (l, it) in f['items'])
    has_r20 = any(it[0] == 'pad' and abs(it[2][0] - 69.425) < 0.01
                  for (l, it) in f['items'])
    print(f'  SCL frag {i}: window_via={has_w} pocket_via={has_pocket} '
          f'R20pad={has_r20} items={len(f["items"])}', flush=True)

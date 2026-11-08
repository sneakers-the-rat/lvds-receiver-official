"""t_at2c: staged gate search for CAP-district fixed copper (fast).
Stage 0: fixed items (W, band-hop) vs pool.
Stage 1: S-candidates alone; Stage 2: E-candidates alone;
Stage 3: surviving (S,E) pairs, mutual gates. Pools are box-local.
Score = min copper-edge margin (seg sampling 0.05 in search)."""
import wx
_app = wx.App(False)
import pcbnew, sys, math
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
import t_ai_lib as L
from router import netclass

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
items = L.load_items(board)

def key_seg(d):
    a = (round(d[0], 3), round(d[1], 3), round(d[2], 3), round(d[3], 3))
    b = (round(d[2], 3), round(d[3], 3), round(d[0], 3), round(d[1], 3))
    return a, b

REM_SEGS = {
    1: [('HV_SHDN', s) for s in [
        (68.875, 0.625, 69.125, 0.375), (69.125, 0.375, 69.375, 0.125),
        (69.375, 0.125, 69.625, -0.125), (69.625, -0.125, 69.875, -0.375),
        (67.375, 2.125, 67.125, 2.375), (67.125, 2.375, 66.875, 2.625),
        (66.875, 2.625, 66.625, 2.875), (66.625, 2.875, 66.375, 3.125),
        (66.375, 3.125, 66.125, 3.375), (66.125, 3.375, 65.875, 3.625),
        (65.875, 3.625, 65.625, 3.875)]],
    2: [('I2C_SDA', s) for s in [
        (69.900, 0.820, 69.875, 0.625), (69.875, 0.625, 69.875, -9.125)]],
    0: [('GND', s) for s in [
        (71.000, 0.270, 69.600, 0.250), (69.600, 0.250, 68.900, 0.850),
        (68.900, 0.850, 68.200, 1.150), (68.200, 1.150, 67.850, 1.220),
        (67.850, 1.220, 67.500, 0.950)]],
}
full = {0: [], 1: [], 2: []}
nseg = nvia = 0
for li in range(3):
    remkeys = set()
    for n, s in REM_SEGS.get(li, []):
        a, b = key_seg(s)
        remkeys.add((n, a)); remkeys.add((n, b))
    for it in items[li]:
        if it[0] == 'via' and it[1] == 'I2C_SDA' and \
           abs(it[2][0] - 69.9) < 0.01 and abs(it[2][1] - 0.82) < 0.01:
            nvia += 1
            continue
        if it[0] == 'seg':
            a, b = key_seg(it[2])
            if (it[1], a) in remkeys:
                nseg += 1
                continue
        full[li].append(it)
print(f'removed segs {nseg} (want 18), via-layer entries {nvia} (want 3)')
pool = L.in_box_pool(full, (63.5, 73.5, -5.6, 5.0), pad=1.2)
print('local pool sizes:', {l: len(pool[l]) for l in range(3)})

W = (68.05, 0.20)
BW1, BW2 = (67.6, 1.95), (65.4, 4.15)

def VIA(net, x, y):
    return ('via', net, (x, y, 0.25), netclass(net)[1])

def SEG(net, a, b, w=0.25):
    return ('seg', net, (a[0], a[1], b[0], b[1], w / 2), netclass(net)[1])

FIXED = [(-1, VIA('HV_SHDN', *W)), (-1, VIA('HV_SHDN', *BW1)),
         (-1, VIA('HV_SHDN', *BW2)),
         (1, SEG('HV_SHDN', (68.875, 0.625), W)),
         (1, SEG('HV_SHDN', (67.375, 2.125), BW1)),
         (1, SEG('HV_SHDN', BW2, (65.625, 3.875))),
         (2, SEG('HV_SHDN', BW1, BW2)),
         (2, SEG('HV_SHDN', W, (68.05, -4.70))),
         (2, SEG('HV_SHDN', (68.05, -4.70), (69.00, -4.70)))]

def s_items(S):
    return [(-1, VIA('I2C_SDA', *S)),
            (2, SEG('I2C_SDA', (69.875, -1.5), S))]

def e_items(E):
    return [(-1, VIA('HV_SHDN', *E)),
            (1, SEG('HV_SHDN', E, (69.875, -0.375))),
            (2, SEG('HV_SHDN', (69.00, -4.70), E))]

def gate(items_list, extra=()):
    """min margin of items_list vs pool+extra (extra: (layer,item) list)."""
    worst = (9.9, None, None)
    extra_by_layer = {0: [], 1: [], 2: []}
    for li, it in extra:
        if li == -1:
            for l in range(3):
                extra_by_layer[l].append(it)
        else:
            extra_by_layer[li].append(it)
    for li, it in items_list:
        layers = range(3) if li == -1 else [li]
        for l in layers:
            p = pool[l] + extra_by_layer[l]
            if it[0] == 'via':
                m, w = L.pt_margin(l, it[2][0], it[2][1], it[1], it[2][2], p)
            else:
                d = it[2]
                m, w = L.seg_margin(l, (d[0], d[1]), (d[2], d[3]),
                                    it[1], d[4], p, step=0.05)
            if m < worst[0]:
                worst = (m, it, w)
    return worst

m, it, w = gate(FIXED)
print(f'== FIXED: {m:+.3f}  {L.fmt_it(it)} vs {L.fmt_it(w)}')

SGRID = [(x, y) for x in (69.95, 70.00, 70.05, 70.10, 70.15, 70.20, 70.25, 70.30)
         for y in (0.55, 0.65, 0.75, 0.82, 0.90, 1.00)]
EGRID = [(x, y) for x in (69.15, 69.25, 69.35, 69.45, 69.55, 69.65)
         for y in (-0.10, 0.00, 0.10, 0.20, 0.30, 0.40)]
s_ok = []
for S in SGRID:
    m, it, w = gate(s_items(S), extra=FIXED)
    if m >= 0:
        s_ok.append((m, S, it, w))
print(f'== S survivors: {len(s_ok)} / {len(SGRID)}')
for m, S, it, w in sorted(s_ok, reverse=True)[:8]:
    print(f'   S={S} margin {m:+.3f} worst {L.fmt_it(it)} vs {L.fmt_it(w)}')
e_ok = []
for E in EGRID:
    m, it, w = gate(e_items(E), extra=FIXED)
    if m >= 0:
        e_ok.append((m, E, it, w))
print(f'== E survivors: {len(e_ok)} / {len(EGRID)}')
for m, E, it, w in sorted(e_ok, reverse=True)[:8]:
    print(f'   E={E} margin {m:+.3f} worst {L.fmt_it(it)} vs {L.fmt_it(w)}')

pairs = []
for ms, S, _, _ in s_ok:
    for me, E, _, _ in e_ok:
        m, it, w = gate(s_items(S), extra=e_items(E))
        m2, it2, w2 = gate(e_items(E), extra=s_items(S))
        if m2 < m:
            m, it, w = m2, it2, w2
        pairs.append((min(ms, me, m), S, E, it, w))
pairs.sort(reverse=True)
print(f'== pairs: {len(pairs)}; top 12:')
for m, S, E, it, w in pairs[:12]:
    print(f'   margin {m:+.3f} S={S} E={E} worst {L.fmt_it(it)} vs {L.fmt_it(w)}')

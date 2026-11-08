"""t_at2: gate-search for the CAP-district fixed copper.
Variables: SDA via S=(sx,sy), HV hop east via E=(ex,ey). W=(68.05,0.20) fixed.
Fixed new copper: HV In2 stubs + B hops (mouth + band-window), SDA B re-lay.
Pool: exp241esc items minus removals (HV band 4+7 segs, SDA via + B stub +
B vertical, GND F tree 5 segs). Flexible heals (SDA staircase, SCL B,
+3V3A F, GND tree) are NOT in this gate - they route later in leftover space.
Score = min copper-edge margin over all new-vs-pool and new-vs-new pairs.
Also report via-via centre distances (drill check) for new vias."""
import wx
_app = wx.App(False)
import pcbnew, sys, math, itertools
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
pool = {0: [], 1: [], 2: []}
removed = 0
for li in range(3):
    rem = REM_SEGS.get(li, [])
    remkeys = set()
    for n, s in rem:
        a, b = key_seg(s)
        remkeys.add((n, a)); remkeys.add((n, b))
    for it in items[li]:
        if it[0] == 'via' and it[1] == 'I2C_SDA' and \
           abs(it[2][0] - 69.9) < 0.01 and abs(it[2][1] - 0.82) < 0.01:
            removed += 1
            continue
        if it[0] == 'seg':
            a, b = key_seg(it[2])
            if (it[1], a) in remkeys:
                removed += 1
                continue
        pool[li].append(it)
print(f'removed {removed} items (expect 11+2+5 segs + 3 via-layer entries = 21)')

W = (68.05, 0.20)
BW1, BW2 = (67.6, 1.95), (65.4, 4.15)   # band-window hop vias

def fixed_items(S, E):
    """new items as (layer, item) - vias get layer -1 (all)."""
    sx, sy = S; ex, ey = E
    out = []
    def via(net, x, y):
        out.append((-1, ('via', net, (x, y, 0.25), netclass(net)[1])))
    def seg(li, net, a, b, w):
        out.append((li, ('seg', net, (a[0], a[1], b[0], b[1], w / 2),
                         netclass(net)[1])))
    via('I2C_SDA', sx, sy)
    via('HV_SHDN', *W); via('HV_SHDN', ex, ey)
    via('HV_SHDN', *BW1); via('HV_SHDN', *BW2)
    seg(1, 'HV_SHDN', (68.875, 0.625), W, 0.25)
    seg(1, 'HV_SHDN', (ex, ey), (69.875, -0.375), 0.25)
    seg(1, 'HV_SHDN', (67.375, 2.125), BW1, 0.25)
    seg(1, 'HV_SHDN', BW2, (65.625, 3.875), 0.25)
    seg(2, 'HV_SHDN', BW1, BW2, 0.25)
    seg(2, 'HV_SHDN', W, (68.05, -4.70), 0.25)
    seg(2, 'HV_SHDN', (68.05, -4.70), (69.00, -4.70), 0.25)
    seg(2, 'HV_SHDN', (69.00, -4.70), (ex, ey), 0.25)
    seg(2, 'I2C_SDA', (69.875, -1.5), (sx, sy), 0.25)
    return out

def gate_new(new_items, extra_pool=None):
    """min margin of new items vs pool and vs each other."""
    worst = (9.9, None)
    # build per-layer pools incl new items for mutual checks
    for li, it in new_items:
        layers = range(3) if li == -1 else [li]
        for l in layers:
            p = list(pool[l])
            if extra_pool:
                p += extra_pool.get(l, [])
            if it[0] == 'via':
                m, w = L.pt_margin(l, it[2][0], it[2][1], it[1], it[2][2], p)
            else:
                d = it[2]
                m, w = L.seg_margin(l, (d[0], d[1]), (d[2], d[3]),
                                    it[1], d[4], p)
            if m < worst[0]:
                worst = (m, (l, it, w))
    # mutual: each new item vs the other new items (same layer relevance)
    for i, (li, it) in enumerate(new_items):
        layers = range(3) if li == -1 else [li]
        for l in layers:
            others = [o for j, (lj, o) in enumerate(new_items)
                      if j != i and (lj == -1 or lj == l) and o[1] != it[1]]
            if not others:
                continue
            if it[0] == 'via':
                m, w = L.pt_margin(l, it[2][0], it[2][1], it[1], it[2][2],
                                   others)
            else:
                d = it[2]
                m, w = L.seg_margin(l, (d[0], d[1]), (d[2], d[3]),
                                    it[1], d[4], others)
            if m < worst[0]:
                worst = (m, (l, it, w))
    return worst

# 1) gate the S/E-independent items first (W, band hop) with dummy S,E
base = fixed_items((70.10, 0.82), (69.40, 0.15))
indep = [(li, it) for li, it in base
         if not (it[0] == 'via' and it[1] in ('I2C_SDA',) )
         and not (it[0] == 'via' and it[1] == 'HV_SHDN'
                  and abs(it[2][0] - 69.40) < 0.01)
         and not (it[0] == 'seg' and it[1] == 'I2C_SDA')
         and not (it[0] == 'seg' and it[1] == 'HV_SHDN' and it[2][0] > 69.0
                  and it[2][1] < 0.2 and it[2][2] > 69.5)
         and not (li == 2 and it[0] == 'seg' and it[1] == 'HV_SHDN'
                  and it[2][0] > 68.5)]
m, w = gate_new(indep)
print(f'== independent fixed items: min margin {m:+.3f} worst {L.fmt_it(w[1]) if w else "-"} vs {L.fmt_it(w[2]) if w else "-"} layer {w[0] if w else "-"}')

# 2) grid search S,E
results = []
for sx in [69.95, 70.00, 70.05, 70.10, 70.15, 70.20, 70.25, 70.30]:
    for sy in [0.55, 0.65, 0.75, 0.82, 0.90, 1.00]:
        for ex in [69.15, 69.25, 69.35, 69.45, 69.55, 69.65]:
            for ey in [-0.10, 0.00, 0.10, 0.20, 0.30, 0.40]:
                ni = fixed_items((sx, sy), (ex, ey))
                m, w = gate_new(ni)
                if m >= -0.05:
                    results.append((m, (sx, sy), (ex, ey), w))
results.sort(reverse=True)
print(f'== {len(results)} (S,E) with min margin >= -0.05; top 15:')
for m, S, E, w in results[:15]:
    print(f'   margin {m:+.3f}  S={S} E={E}  worst: {L.fmt_it(w[1])} vs '
          f'{L.fmt_it(w[2])} L{w[0]}')

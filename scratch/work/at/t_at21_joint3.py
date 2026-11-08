"""t_at21: optimized joint search (same model as t_at20).
Chord-vs-SDA-via interaction is analytic (point-seg distance)
instead of full seg_gate per triple. Progress + stderr kept."""
import wx
_app = wx.App(False)
import sys, math, time
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
import t_ai_lib as L

src = open('scratch/work/at/t_at20_joint2.py').read()
exec(src.split('results = []')[0])
print('pool ready', flush=True)

scl_grid = [(69.0 + 0.05 * i, 1.15 + 0.05 * j)
            for i in range(17) for j in range(12)]
sda_grid = [(68.5 + 0.05 * i, 1.8 + 0.05 * j)
            for i in range(23) for j in range(19)]
bend_grid = [(68.7 + 0.1 * i, 1.9 + 0.1 * j)
             for i in range(10) for j in range(9)]

t0 = time.time()
sda_ok = []
for (x, y) in sda_grid:
    if rect_dist(x, y, SDA_PAD_RECT) > 1.6:
        continue
    g = via_gate('I2C_SDA', x, y)
    if g >= 0.0:
        sda_ok.append((x, y, g))
print(f'SDA candidates: {len(sda_ok)} ({time.time() - t0:.0f}s)',
      flush=True)

# Precompute chord options: (sx, sy, gs, bx, by, g1, g2, slot)
opts = []
for (sx, sy) in scl_grid:
    gs = via_gate('I2C_SCL', sx, sy)
    if gs < 0.0:
        continue
    slot_via = band_dist(sx, sy) - 0.25 - 0.125 - 0.20
    if slot_via < 0.0:
        continue
    for (bx, by) in bend_grid:
        if math.hypot(bx - sx, by - sy) < 0.3:
            continue
        g1 = seg_gate(1, 'I2C_SCL', CHORD0, (bx, by))
        if g1 < 0.0:
            continue
        g2 = seg_gate(1, 'I2C_SCL', (bx, by), (sx, sy))
        if g2 < 0.0:
            continue
        smin = slot_via
        for (a, b) in ((CHORD0, (bx, by)), ((bx, by), (sx, sy))):
            for k in range(21):
                px = a[0] + (b[0] - a[0]) * k / 20
                py = a[1] + (b[1] - a[1]) * k / 20
                smin = min(smin, band_dist(px, py) - 0.10 - 0.125 - 0.20)
        if smin < 0.0:
            continue
        opts.append((sx, sy, gs, bx, by, g1, g2, smin))
print(f'chord options passing fixed gates + slot: {len(opts)} '
      f'({time.time() - t0:.0f}s)', flush=True)

results = []
for (sx, sy, gs, bx, by, g1, g2, slot) in opts:
    for (ax, ay, ga) in sda_ok:
        dvv = math.hypot(ax - sx, ay - sy)
        if dvv < 0.70:
            continue
        # SDA gate incl. SCL via (not in base pool): analytic
        g3 = min(ga, dvv - 0.45)
        d1 = pt_seg(ax, ay, CHORD0, (bx, by)) - 0.25 - 0.20
        d2 = pt_seg(ax, ay, (bx, by), (sx, sy)) - 0.25 - 0.20
        if min(d1, d2) < 0.0:
            continue
        score = min(gs, ga, g1, g2, g3, d1, d2, slot)
        results.append((score, slot, (sx, sy), (bx, by), (ax, ay),
                        gs, g1, g2))
results.sort(reverse=True)
print(f'joint feasible: {len(results)} ({time.time() - t0:.0f}s)')
for r in results[:15]:
    print(f'score {r[0]:+.3f} slot {r[1]:+.3f} SCLvia {r[2]} '
          f'bend {r[3]} SDAvia {r[4]} gates scl {r[5]:+.3f} '
          f'chord {r[6]:+.3f}/{r[7]:+.3f}')

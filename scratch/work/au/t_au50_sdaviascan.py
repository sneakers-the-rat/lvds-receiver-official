"""t_au50: SDA via scan. Candidates: baseline (69.05,2.05) +
west moves. Per candidate: stub gate, hop A*, exit A* (2 goals),
heal1 F-only, DATA entry. First full pass wins -> heals_au50.json."""
import wx
_app = wx.App(False)
import sys, json
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'p1b'}
src = open('scratch/work/au/t_au43_phase1b.py').read()
exec(src.split("J40 = json.load")[0], g)
exec(src[src.index("def entry_astar"):src.index("out = {}")], g)
exec(src[src.index("FBOX ="):src.index("J = fastest('+3V3A'")], g)
pool0 = g['pool']
entry_astar = g['entry_astar']
journey_items_dense = g['journey_items_dense']
fastest = g['fastest']
seg_ = g['seg_']
via_ = g['via_']
import t_ai_lib as L

# base pool contains SDA via (69.05,2.05)+stub from t_au43 head FIXED.
# Remove them for the scan: identify by geometry.
def is_sda_via(it):
    return it[0] == 'via' and it[1] == 'I2C_SDA' and \
        abs(it[2][0] - 69.05) < 0.01 and abs(it[2][1] - 2.05) < 0.01


def is_sda_stub(it):
    return it[0] == 'seg' and it[1] == 'I2C_SDA' and \
        abs(it[2][0] - 68.45) < 0.01 and abs(it[2][1] - 2.1) < 0.01


pool_base = {l: [it for it in pool0[l]
                 if not is_sda_via(it) and not is_sda_stub(it)]
             for l in range(3)}
J40 = json.load(open('scratch/work/au/joint_au40.json'))
CANDS = [(69.05, 2.05), (68.45, 1.90), (68.60, 1.95), (68.70, 1.80),
         (68.55, 1.75), (68.35, 2.00)]
winner = None
for (sx, sy) in CANDS:
    pool = {l: list(pool_base[l]) for l in range(3)}
    g['pool'] = pool
    # bheal first (independent of SDA via)
    for l, its in journey_items_dense(J40['jobs']['bheal'], 'I2C_SCL',
                                      hw=0.10).items():
        pool[l] += its

    def add_j(J, net, hw=0.10):
        for l, its in journey_items_dense(J, net, hw=hw).items():
            pool[l] += its
    # SDA via + stub gates
    def pg_pocket(o):
        # PG items whose bbox intersects the pocket box are
        # detour-absorbable (phase 2 re-lays them)
        if o[1] != 'PG_3V3':
            return False
        d = o[2]
        if o[0] == 'seg':
            bx0, bx1 = min(d[0], d[2]) - d[4], max(d[0], d[2]) + d[4]
            by0, by1 = min(d[1], d[3]) - d[4], max(d[1], d[3]) + d[4]
        else:
            bx0, bx1, by0, by1 = d[0] - 0.3, d[0] + 0.3, d[1] - 0.3, \
                d[1] + 0.3
        return bx1 > 60.0 and bx0 < 70.0 and by1 > 0.0 and by0 < 16.0

    def gate_pool(l):
        return [o for o in pool[l] if o[1] != 'I2C_SDA'
                and not pg_pocket(o)]
    ok = True
    for l in range(3):
        m, _ = L.pt_margin(l, sx, sy, 'I2C_SDA', 0.25, gate_pool(l))
        if m < 0:
            ok = False
            break
    if ok:
        m, _ = L.seg_margin(0, (68.225, 2.1), (sx, sy), 'I2C_SDA', 0.10,
                            [o for o in pool[0] if o[1] != 'I2C_SDA'])
        ok = m >= 0
    print(f'SDA via ({sx},{sy}): gates', 'OK' if ok else 'FAIL',
          flush=True)
    if not ok:
        continue
    via_(pool, 'I2C_SDA', sx, sy)
    seg_(pool, 0, 'I2C_SDA', (68.225, 2.1), (sx, sy))
    Jh = fastest('I2C_SDA', ((0, 1, 2), sx, sy), (1, 71.125, 1.875),
                 hw=0.125)
    print('  hop:', 'FOUND' if Jh else 'NONE', flush=True)
    if not Jh:
        continue
    add_j(Jh, 'I2C_SDA', 0.125)
    Jx = None
    for goal in ((69.55, 2.70), (69.4, 2.8)):
        Jx = fastest('CAP_CLK', ((0, 1, 2), 70.2, 1.8),
                     (2, goal[0], goal[1]))
        if Jx:
            break
    print('  exit:', 'FOUND' if Jx else 'NONE', flush=True)
    if not Jx:
        continue
    add_j(Jx, 'CAP_CLK', 0.10)
    J1 = fastest('+3V3A', ((0,), 68.225, 2.75), (0, 69.125, 4.375),
                 hw=0.10)
    print('  heal1:', 'FOUND' if J1 else 'NONE', flush=True)
    if not J1:
        continue
    add_j(J1, '+3V3A', 0.10)
    Je = entry_astar('CAP_DATA', 1, 69.9, 3.175, 63.85, 6.3,
                     (60.0, 72.0, -1.0, 10.0))
    print('  entry:', 'FOUND' if Je else 'NONE', flush=True)
    if not Je:
        continue
    winner = dict(sda_via=(sx, sy), hop=Jh, clk_exit=Jx, v3a_heal1=J1,
                  data_entry=Je)
    break
if winner:
    J30 = json.load(open('scratch/work/as/journey30_CAP_DATA_DC.json'))
    pts0 = J30['runs'][0]['pts']
    winner['data_tail'] = dict(
        vias=J30['vias'],
        runs=[dict(layer=1, pts=pts0[213:])] + J30['runs'][1:])
    json.dump(winner, open('scratch/work/au/heals_au50.json', 'w'))
    print('WINNER SDA via', winner['sda_via'], flush=True)
else:
    print('NO WINNER', flush=True)
print('done', flush=True)

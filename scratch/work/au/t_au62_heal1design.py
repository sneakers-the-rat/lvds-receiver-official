"""t_au62: gate hand-designed heal1 (In2 ride at x68.3) vs v6 pool,
excluding PG (phase-2 detour absorbs PG conflicts)."""
import wx
_app = wx.App(False)
import sys, json
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'p1b'}
src60 = open('scratch/work/au/t_au60_v6.py').read()
exec(src60.split("\nout = {")[0], g)
pool = g['pool']
import t_ai_lib as L

def gp(l, excl_pg=True):
    return [o for o in pool[l] if o[1] != '+3V3A'
            and not (excl_pg and o[1] == 'PG_3V3')]

items = [
    ('stubF1', 0, (67.975, 2.75), (68.3, 2.85)),
    ('via1', None, (68.3, 2.95), None),
    ('ride1', 1, (68.3, 2.95), (68.55, 3.6)),
    ('ride2', 1, (68.55, 3.6), (69.0, 4.3)),
    ('via2', None, (69.0, 4.3), None),
    ('stubF2', 0, (69.0, 4.3), (69.125, 4.375)),
]
for (tag, l, a, b) in items:
    if l is None:
        worst = (9, None, None)
        for ll in range(3):
            m, w = L.pt_margin(ll, a[0], a[1], '+3V3A', 0.25, gp(ll))
            if m < worst[0]:
                worst = (m, ll, w)
        print(f'{tag} via {a}: worst {worst[0]:+.3f} L{worst[1]} vs '
              f'{L.fmt_it(worst[2])}', flush=True)
    else:
        m, w = L.seg_margin(l, a, b, '+3V3A', 0.10, gp(l))
        print(f'{tag} L{l} {a}->{b}: {m:+.3f} vs {L.fmt_it(w)}',
              flush=True)
print('done')

"""t_au45: heal1 ablation diagnosis in the v5 model."""
import wx
_app = wx.App(False)
import sys, json
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'p1b'}
src = open('scratch/work/au/t_au43_phase1b.py').read()
head = src.split("J = fastest('+3V3A'")[0]
exec(head, g)
pool = g['pool']
fastest = g['fastest']
C = g['C']

# exit items = CAP_CLK items added beyond esc's own (via 68.975 + F run +
# B join seg): identify by geometry
def is_exit(it):
    if it[1] != 'CAP_CLK':
        return False
    if it[0] == 'via':
        return abs(it[2][0] - 68.975) < 0.01 and abs(it[2][1] - 2.8) < 0.01
    return True  # CLK segs in pocket box are exit/stub (ride is N of y16)
variants = {}
variants['v5 full'] = pool
p2 = {l: [it for it in pool[l] if not is_exit(it)] for l in range(3)}
variants['minus exit'] = p2
p3 = {l: [it for it in p2[l]
          if not (it[1] == 'PG_3V3' and 66.0 < C(it)[0] < 70.0
                  and 1.5 < C(it)[1] < 5.0)] for l in range(3)}
variants['minus exit minus PG pocket'] = p3
p4 = {l: [it for it in p2[l]
          if not (it[1] == 'CAP_DATA' and C(it)[1] < 10.0)] for l in range(3)}
variants['minus exit minus DATA entry'] = p4
import t_au43_phase1b as _m  # noqa - not used; fastest closes over g pool
for name, px in variants.items():
    g['pool'] = px
    # fastest() reads 'pool' from its own module globals (exec'd in g)
    J = fastest('+3V3A', ((0,), 68.225, 2.75), (0, 69.125, 4.375), hw=0.10)
    print(f'{name}:', 'FOUND' if J else 'NONE', flush=True)
    if J:
        print('  vias', J['vias'],
              [(r['layer'], r['pts'][0], r['pts'][-1]) for r in J['runs']])
g['pool'] = pool
print('done')

"""t_au84: diagnostics 2 in the au83 model state.
(a) ALL ULPI_DIR F segs with an endpoint in x[55,72] y[-1,9].
(b) ALL XO items x[70,90] y[8,14] (any layer) + RIP2 XO items.
(c) XO items x[68,74] y[16,22] (any layer)."""
import wx
_app = wx.App(False)
import sys, json, math
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'p2m'}
src71 = open('scratch/work/au/t_au71_phase2b.py').read()
exec(src71.split("NEW = {")[0], g)
pool = g['pool']
C = g['C']
import t_ai_lib as L

B = json.load(open('scratch/work/au/build_au83.json'))
for net, lst in B['rip2'].items():
    for itj in lst:
        it = (itj[0], itj[1], tuple(itj[2]), itj[3])
        for l in range(3):
            if it in pool[l]:
                pool[l].remove(it)
print('--- (a) ULPI_DIR F segs endpoints in x[55,72] y[-1,9]:',
      flush=True)
for it in pool[0]:
    if it[0] == 'seg' and it[1] == 'ULPI_DIR':
        d = it[2]
        if (55 < d[0] < 72 and -1 < d[1] < 9) or \
                (55 < d[2] < 72 and -1 < d[3] < 9):
            print('   ', L.fmt_it(it), flush=True)
print('--- (b) XO items x[70,90] y[8,14]:', flush=True)
for l in range(3):
    for it in pool[l]:
        if it[1] == 'XO' and 70 < C(it)[0] < 90 and 8 < C(it)[1] < 14:
            print(f'    L{l}', L.fmt_it(it), flush=True)
print('--- RIP2 XO items:', flush=True)
for itj in B['rip2'].get('XO', []):
    print('   ', itj, flush=True)
print('--- (c) XO items x[68,74] y[16,22]:', flush=True)
for l in range(3):
    for it in pool[l]:
        if it[1] == 'XO' and 68 < C(it)[0] < 74 and 16 < C(it)[1] < 22:
            print(f'    L{l}', L.fmt_it(it), flush=True)
print('done', flush=True)

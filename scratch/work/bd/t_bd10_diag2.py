"""t_bd10: trustworthy best-config diagnostic for family C v2.
Same grid and gates as t_bd9, but: incumbent-tracked in ONE loop,
every improvement is RE-EVALUATED at floor=-9 (full detail, no
pruning) and printed immediately from that re-evaluation -- no
stored tops, no deferred pairing (the t_bd3 lesson)."""
import sys, time
sys.path.insert(0, 'hw')
src = open('scratch/work/bd/t_bd9_famc2.py').read()
src = src[:src.index('t0 = time.time()')]
D = type(sys)('D')
exec(compile(src, 't_bd9_defs', 'exec'), D.__dict__)

t0 = time.time()
best = -0.30
n = 0
for nvx in (75.00, 75.04, 75.08):
    for nvy in (17.30, 17.34, 17.38):
        for dvx in (74.72, 74.76, 74.80):
            for dvy in (17.96, 18.04, 18.12):
                for b1x in (75.60, 75.65, 75.70):
                    for b2x in (75.40, 75.45, 75.50):
                        for ib in ((74.42, 17.75), (74.48, 17.85)):
                            for bb in ((73.9, 18.75), (73.8, 18.65), None):
                                n += 1
                                cfg = ((nvx, nvy), (dvx, dvy), (b1x, 17.32),
                                       (b2x, 17.85), ib, bb)
                                w, _det = D.gate_stage1(*cfg, best)
                                if w > best:
                                    w2, det2 = D.gate_stage1(*cfg, -9e9)
                                    print(f'  best {w2:+.3f} NV={cfg[0]} DV={cfg[1]} '
                                          f'b1={cfg[2]} b2={cfg[3]} in2={ib} bb={bb} '
                                          f'[{time.time()-t0:.0f}s]', flush=True)
                                    for k, v in det2.items():
                                        print(f'      {k}: {v[0]:+.3f} binding {v[1]}',
                                              flush=True)
                                    best = w2
print(f'\ndiag2 done: {n} configs, {time.time()-t0:.0f}s, best {best:+.3f}')

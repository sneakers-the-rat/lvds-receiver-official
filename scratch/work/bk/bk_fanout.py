#!/usr/bin/env python3
"""DIR/NXT fanout search on BK-A pool (DM re-laid west, RST dive present).
DIR: F pad (75.750,16.875) -> elbow -> via -> B -> (73.300,18.420).
NXT: F pad (75.250,16.875) -> elbow -> via -> In2 -> join (74.500,19.250)
     or the existing In2 seg (74.100,17.700)->(74.500,19.250).
Seeded grid search: via candidates x elbow candidates, joint pair scoring."""
import itertools
import sys
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/scratch/work/bk')
import bk_lib as L
import gridroute as G

OUT = '/home/hatch/workspace/pdlvds-route/scratch/work/bk/bk_fanout_out.txt'
lines = []

DIR_PAD = (75.750, 16.875)
DIR_B = (73.300, 18.420)
NXT_PAD = (75.250, 16.875)
NXT_IN2_A = (74.100, 17.700)
NXT_IN2_B = (74.500, 19.250)


def cand(net, pad, layer2, target, via_c, elbow_f, elbow2, dia=0.5):
    its = [G.Item(net, 'via', a=via_c, hw=dia / 2)]
    if elbow_f:
        its.append(G.Item(net, 'trk', layer='F', a=pad, b=elbow_f, hw=0.10))
        its.append(G.Item(net, 'trk', layer='F', a=elbow_f, b=via_c, hw=0.10))
    else:
        its.append(G.Item(net, 'trk', layer='F', a=pad, b=via_c, hw=0.10))
    if elbow2:
        its.append(G.Item(net, 'trk', layer=layer2, a=via_c, b=elbow2, hw=0.125))
        its.append(G.Item(net, 'trk', layer=layer2, a=elbow2, b=target, hw=0.125))
    else:
        its.append(G.Item(net, 'trk', layer=layer2, a=via_c, b=target, hw=0.125))
    return its


def worst(its, env):
    w = 9.9
    for it in its:
        if it.kind == 'via':
            m, _ = L.m_via(it.a, it.hw, it.net, env)
        else:
            m, _ = L.m_trk(it.a, it.b, it.layer, it.hw, it.net, env)
        w = min(w, m)
    return w


def grid(x0, x1, y0, y1, step):
    xs = []
    x = x0
    while x <= x1 + 1e-9:
        xs.append(round(x, 3)); x += step
    ys = []
    y = y0
    while y <= y1 + 1e-9:
        ys.append(round(y, 3)); y += step
    return [(a, b) for a in xs for b in ys]


# ---- DIR singles ----
dir_vias = grid(74.55, 75.45, 18.15, 19.30, 0.05) + [(74.85, 18.40)]
dir_elbows = grid(75.05, 75.65, 17.35, 18.15, 0.10) + [None]
dir_b_elbows = [None, (74.30, 18.55), (74.60, 18.30), (74.00, 18.60)]
dir_ok = []
for vc in dir_vias:
    mv, _ = L.m_via(vc, 0.25, 'ULPI_DIR', L.full)
    if mv < -0.05:
        continue
    for ef in dir_elbows:
        for eb in dir_b_elbows:
            its = cand('ULPI_DIR', DIR_PAD, 'B', DIR_B, vc, ef, eb)
            w = worst(its, L.full)
            if w >= -0.05:
                dir_ok.append((w, vc, ef, eb))
dir_ok.sort(reverse=True)
lines.append(f'DIR candidates >= -0.05: {len(dir_ok)}')
for w, vc, ef, eb in dir_ok[:8]:
    lines.append(f'  DIR {w:+.3f} via{vc} elbowF{ef} elbowB{eb}')

# ---- NXT singles ----
nxt_vias = grid(74.95, 75.55, 16.95, 17.85, 0.05)
nxt_elbows = grid(75.15, 75.60, 16.95, 17.45, 0.10) + [None]
nxt_joins = [NXT_IN2_B, (74.42, 18.85), (74.30, 18.60)]
nxt_e2 = [None, (74.85, 17.85), (74.80, 17.80), (74.90, 18.10)]
nxt_ok = []
for vc in nxt_vias:
    mv, _ = L.m_via(vc, 0.25, 'ULPI_NXT', L.full)
    if mv < -0.05:
        continue
    for ef in nxt_elbows:
        for tg in nxt_joins:
            for e2 in nxt_e2:
                its = cand('ULPI_NXT', NXT_PAD, 'In2', tg, vc, ef, e2)
                w = worst(its, L.full)
                if w >= -0.05:
                    nxt_ok.append((w, vc, ef, tg, e2))
nxt_ok.sort(reverse=True)
lines.append(f'NXT candidates >= -0.05: {len(nxt_ok)}')
for w, vc, ef, tg, e2 in nxt_ok[:8]:
    lines.append(f'  NXT {w:+.3f} via{vc} elbowF{ef} join{tg} elbow2{e2}')

# ---- joint best pair ----
best = None
for wd, vc_d, ef_d, eb_d in dir_ok[:14]:
    d_its = cand('ULPI_DIR', DIR_PAD, 'B', DIR_B, vc_d, ef_d, eb_d)
    env2 = L.full + d_its
    for wn, vc_n, ef_n, tg_n, e2_n in nxt_ok[:14]:
        n_its = cand('ULPI_NXT', NXT_PAD, 'In2', tg_n, vc_n, ef_n, e2_n)
        w2 = worst(n_its, env2)
        score = min(wd, wn, w2)
        if best is None or score > best[0]:
            best = (score, (wd, vc_d, ef_d, eb_d), (wn, vc_n, ef_n, tg_n, e2_n), w2)
lines.append(f'JOINT BEST: {best}')
txt = '\n'.join(lines) + '\n'
open(OUT, 'w').write(txt)
print(txt)
print('WROTE', OUT)

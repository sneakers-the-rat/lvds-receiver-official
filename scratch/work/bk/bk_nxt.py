#!/usr/bin/env python3
"""NXT staged diagnostic: via-only grid (wide), then per-via stub pricing
with binding items named. Pool = bk_lib full (DIR adds NOT included)."""
import sys
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/scratch/work/bk')
import bk_lib as L
import gridroute as G

OUT = '/home/hatch/workspace/pdlvds-route/scratch/work/bk/bk_nxt_out.txt'
lines = []
PAD = (75.250, 16.875)
TGT = (74.500, 19.250)


def grid(x0, x1, y0, y1, step):
    out = []
    x = x0
    while x <= x1 + 1e-9:
        y = y0
        while y <= y1 + 1e-9:
            out.append((round(x, 3), round(y, 3)))
            y += step
        x += step
    return out


vias = []
for c in grid(74.90, 75.70, 16.95, 18.60, 0.05):
    m, d = L.m_via(c, 0.25, 'ULPI_NXT', L.full)
    vias.append((m, c, d))
vias.sort(reverse=True)
lines.append('NXT via-only top 12:')
for m, c, d in vias[:12]:
    lines.append(f'  {m:+.3f} via{c} bind: {d}')

# stub pricing for top vias: F variants x In2 variants, binding named
F_ELB = [None, (75.45, 17.10), (75.50, 17.30), (75.35, 17.45), (75.55, 17.50),
         (75.30, 17.70), (75.45, 17.65)]
I_MID = [None, (75.05, 18.30), (74.95, 18.60), (75.10, 18.05), (74.85, 18.45)]
results = []
for mv, vc, _ in vias[:10]:
    if mv < -0.10:
        continue
    for ef in F_ELB:
        f_its = [G.Item('ULPI_NXT', 'trk', layer='F', a=PAD, b=ef or vc, hw=0.10)]
        if ef:
            f_its.append(G.Item('ULPI_NXT', 'trk', layer='F', a=ef, b=vc, hw=0.10))
        wf, bf = 9.9, ''
        for it in f_its:
            m, d = L.m_trk(it.a, it.b, 'F', it.hw, 'ULPI_NXT', L.full)
            if m < wf:
                wf, bf = m, d
        if wf < -0.10:
            continue
        for em in I_MID:
            i_its = [G.Item('ULPI_NXT', 'trk', layer='In2', a=vc, b=em or TGT, hw=0.125)]
            if em:
                i_its.append(G.Item('ULPI_NXT', 'trk', layer='In2', a=em, b=TGT, hw=0.125))
            wi, bi = 9.9, ''
            for it in i_its:
                m, d = L.m_trk(it.a, it.b, 'In2', it.hw, 'ULPI_NXT', L.full)
                if m < wi:
                    wi, bi = m, d
            results.append((min(mv, wf, wi), vc, ef, em, mv, wf, bf, wi, bi))
results.sort(key=lambda r: r[0], reverse=True)
lines.append('NXT full top 10 (score, via, elbowF, midIn2 | viaM, fM bind, iM bind):')
for r in results[:10]:
    lines.append(f'  {r[0]:+.3f} via{r[1]} eF{r[2]} mI{r[3]} | via {r[4]:+.3f} F {r[5]:+.3f} [{r[6]}] In2 {r[7]:+.3f} [{r[8]}]')
txt = '\n'.join(lines) + '\n'
open(OUT, 'w').write(txt)
print(txt)
print('WROTE', OUT)

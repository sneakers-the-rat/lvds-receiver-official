#!/usr/bin/env python3
"""Price fixed composite vs (pool + sibling adds); rip verification report."""
import sys
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/scratch/work/bk')
from bk_lib import ADDS, _bad, full, price

OUT = '/home/hatch/workspace/pdlvds-route/scratch/work/bk/bk_price_out.txt'
lines = ['RIP VERIFICATION (unmatched rips):']
lines.append(f'  unmatched: {len(_bad)}')
for b in _bad:
    lines.append(f'  {b}')
lines.append(f'adds: {len(ADDS)}; env full {len(full)}')
rows = price(ADDS, full)
lines.append('FIXED ADD MARGINS (worst 30):')
for m, label, it, d in rows[:30]:
    lines.append(f'  {m:+.3f} {label:12s} {it.kind}[{it.layer}] {it.net} {it.a} -> {d}')
txt = '\n'.join(lines) + '\n'
open(OUT, 'w').write(txt)
print(txt)
print('WROTE', OUT)

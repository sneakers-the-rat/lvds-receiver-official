#!/usr/bin/env python3
"""bn fix2b (parent-driven): SPLIT build of bn_fix2 — only the nets that
gate clean (ULPI_D1, ULPI_D2, I2C_SCL, NRST, +3V3D) plus the C19/C48
moves -> exp271. The D3-D6 knot stays exactly as exp270 has it and is
attacked next with a joint via grid. Imports bn_fix2's data, filtered."""
import sys
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/hw')
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/scratch/work/bm')
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/scratch/work/bn')
import bn_fix2 as F

KEEP = {'ULPI_D1', 'I2C_SCL', 'NRST', '+3V3D'}
F.RIP_SEGS = [r for r in F.RIP_SEGS if r[0] in KEEP]
F.RIP_VIAS = [r for r in F.RIP_VIAS if r[0] in KEEP]
F.NEW_TRK = [r for r in F.NEW_TRK if r[0] in KEEP]
F.NEW_VIA = [r for r in F.NEW_VIA if r[0] in KEEP]
# Named carry: D1's new legs graze the CONDEMNED D2 via (80.3,12.8) at
# -0.10/-0.08 — strictly better than exp270's own -0.155 for the same
# pair; the knot pass re-places that via and heals the pair for good.
F.ALLOW = [('ULPI_D1', 'via ULPI_D2@(80.3, 12.8)')]

if __name__ == '__main__':
    bad = F.gate()
    if bad:
        print('GATE FAILED — not building')
        sys.exit(1)
    print('gate clean')
    if '--gate-only' not in sys.argv:
        F.build()

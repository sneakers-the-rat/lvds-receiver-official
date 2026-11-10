#!/usr/bin/env python3
"""bn fix2c (parent-driven): fix2b with the C19/C48 moves REVERTED.
The moves (bn's design) pushed C48's GND pad onto CDR_SQUELCH's F chain
(2 shorts + mask bridges), pushed C48's pad1 onto D6's via (short), and
pushed both courtyards into X1's — the gate never priced the moved pads
as new items. Lesson recorded: a moved part's pads ARE new items.
Here: parts stay at exp270 positions; NRST/+3V3D feeds re-based to the
real pad points; D1/SCL re-lays as fix2b. exp270 -> exp271."""
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
F.MOVES = {'C19': (0.0, 0.0), 'C48': (0.0, 0.0)}
F.NEW_TRK = [t for t in F.NEW_TRK if t[0] not in ('NRST', '+3V3D')] + [
    ('NRST', 'F.Cu', (80.775, 12.0), (80.55, 10.65), 0.2),
    ('NRST', 'F.Cu', (80.55, 10.65), (80.225, 10.5), 0.2),
    ('+3V3D', 'F.Cu', (80.825, 13.6), (81.3, 13.0), 0.2),
    ('+3V3D', 'F.Cu', (81.3, 13.0), (81.55, 12.7), 0.2),
    ('+3V3D', 'F.Cu', (81.55, 12.7), (81.55, 11.6), 0.2),
    ('+3V3D', 'F.Cu', (81.55, 11.6), (81.625, 10.9), 0.2),
]
# Named carry: D1's new legs graze the CONDEMNED D2 via (80.3,12.8),
# strictly better than exp270's own margin for the same pair; the knot
# pass re-places that via and heals the pair for good.
F.ALLOW = [('ULPI_D1', 'via ULPI_D2@(80.3, 12.8)')]

if __name__ == '__main__':
    bad = F.gate()
    if bad:
        print('GATE FAILED — not building')
        sys.exit(1)
    print('gate clean')
    if '--gate-only' not in sys.argv:
        F.build()

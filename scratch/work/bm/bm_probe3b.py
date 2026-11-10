#!/usr/bin/env python3
"""Probe A-chain candidates vs XI seg1 / PV / row track using bm_gate."""
import sys
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/hw')
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/scratch/work/bm')
import bm_gate as BG

SEG1 = ((75.82, 10.3), (76.1, 10.25))
SEG2 = ((76.1, 10.25), (76.28, 10.42))
PV = (75.82, 10.3)
ROW = ((75.625, 11.125), (75.875, 11.125))
PAD30 = (75.875, 11.125, 76.125, 12.0)

CANDS = {
    'hi2': [(76.5, 11.562), (76.47, 10.96), (76.22, 10.88), (75.92, 10.74), (75.64, 10.7), (75.5, 10.54), (75.2, 10.35), (74.99, 10.28)],
    'hi3': [(76.5, 11.562), (76.47, 10.96), (76.22, 10.88), (75.92, 10.72), (75.64, 10.66), (75.5, 10.54), (75.2, 10.35), (74.99, 10.28)],
    'hi4': [(76.5, 11.562), (76.47, 10.96), (76.22, 10.88), (75.95, 10.73), (75.66, 10.67), (75.5, 10.54), (75.2, 10.35), (74.99, 10.28)],
    'hi5': [(76.5, 11.562), (76.47, 10.94), (76.24, 10.87), (75.95, 10.72), (75.66, 10.67), (75.5, 10.54), (75.2, 10.35), (74.99, 10.28)],
    'hi6': [(76.5, 11.562), (76.47, 10.96), (76.22, 10.89), (75.98, 10.75), (75.68, 10.68), (75.5, 10.54), (75.2, 10.35), (74.99, 10.28)],
}
for name, pts in CANDS.items():
    worst = []
    for a, b in zip(pts, pts[1:]):
        m1 = BG.seg_seg(a, b, *SEG1) - 0.2 - 0.2
        m2 = BG.seg_seg(a, b, *SEG2) - 0.2 - 0.2
        m3 = BG.pt_seg(PV, a, b) - 0.1 - 0.25 - 0.2
        m4 = BG.seg_seg(a, b, *ROW) - 0.1 - 0.1 - 0.25
        m5 = BG.seg_rect(a, b, PAD30) - 0.1 - 0.25
        worst.append((min(m1, m2, m3, m4, m5), f'{a}->{b} seg1={m1:+.3f} seg2={m2:+.3f} pv={m3:+.3f} row={m4:+.3f} pad30={m5:+.3f}'))
    worst.sort()
    print(f"== {name}: worst seg {worst[0][0]:+.3f}")
    for m, d in worst[:3]:
        print('   ', d)

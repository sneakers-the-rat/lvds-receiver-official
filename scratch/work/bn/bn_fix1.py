#!/usr/bin/env python3
"""bn fix1 v4: east D-fan repair on exp270 -> exp271.
C19 +0.25E, C48 +0.2E/+0.15S; SCL In2 vertical x79.45 -> x79.2;
D1 re-escape (w0.15 legs, shallow-then-north); D2 via (80.33,12.88);
D3 via (79.82,13.82) west; D4 In2 head east; D5 via (80.35,15.28);
D6 via (80.85,14.7) + saddle fan; NRST/+3V3D feeds re-laid.
Gate: bm_gate margins vs victim-filtered pool + new-vs-new.
Exception: >=-0.05 vs a power-net item = clean (gate prices power
at 0.25; KiCad's binding rule is 0.20)."""
import sys
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/hw')
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/scratch/work/bm')
import gridroute as G
import bm_gate as BG
import build_lib as BL

SRC = 'hw/pdlvds_rx.exp270.kicad_pcb'
DST = 'hw/pdlvds_rx.exp271.kicad_pcb'

RIP_SEGS = [
    ('ULPI_D1', 'F.Cu', (79.1875, 12.75), (79.4375, 12.75)),
    ('ULPI_D1', 'F.Cu', (79.4375, 12.75), (79.93, 12.6)),
    ('ULPI_D1', 'F.Cu', (79.93, 12.6), (79.93, 11.95)),
    ('ULPI_D1', 'F.Cu', (79.93, 11.95), (79.78, 11.5)),
    ('ULPI_D1', 'F.Cu', (79.78, 11.5), (79.75, 10.9)),
    ('ULPI_D1', 'F.Cu', (79.75, 10.9), (79.35, 10.35)),
    ('ULPI_D2', 'F.Cu', (79.4375, 13.25), (79.875, 13.125)),
    ('ULPI_D2', 'F.Cu', (79.875, 13.125), (80.3, 12.8)),
    ('ULPI_D2', 'In2.Cu', (80.3, 12.8), (80.0, 8.3)),
    ('ULPI_D3', 'F.Cu', (79.95, 13.75), (80.15, 13.7)),
    ('ULPI_D3', 'In2.Cu', (80.15, 13.7), (82.2, 11.6)),
    ('ULPI_D4', 'In2.Cu', (80.2, 14.45), (80.5, 13.9)),
    ('ULPI_D4', 'In2.Cu', (80.5, 13.9), (80.875, 13.625)),
    ('ULPI_D5', 'F.Cu', (79.1875, 14.75), (79.75, 14.78)),
    ('ULPI_D5', 'F.Cu', (79.75, 14.78), (80.25, 15.188)),
    ('ULPI_D5', 'In2.Cu', (80.25, 15.188), (80.8, 15.55)),
    ('ULPI_D6', 'F.Cu', (79.4375, 15.25), (80.25, 15.0)),
    ('ULPI_D6', 'F.Cu', (80.25, 15.0), (81.0, 14.4)),
    ('ULPI_D6', 'In2.Cu', (81.0, 14.4), (81.375, 14.125)),
    ('I2C_SCL', 'In2.Cu', (79.15, 10.6), (79.45, 11.1)),
    ('I2C_SCL', 'In2.Cu', (79.45, 11.1), (79.45, 14.375)),
    ('I2C_SCL', 'In2.Cu', (79.45, 14.375), (79.0, 14.85)),
    ('NRST', 'F.Cu', (80.775, 12.0), (80.225, 10.5)),
    ('+3V3D', 'F.Cu', (80.825, 13.6), (81.55, 12.3)),
    ('+3V3D', 'F.Cu', (81.55, 12.3), (81.55, 11.05)),
    ('+3V3D', 'F.Cu', (81.55, 11.05), (81.625, 10.9)),
]
RIP_VIAS = [('ULPI_D2', (80.3, 12.8)), ('ULPI_D3', (80.15, 13.7)),
            ('ULPI_D5', (80.25, 15.188)), ('ULPI_D6', (81.0, 14.4))]
OLD_RECTS = [(80.325, 11.525, 81.225, 12.475), (81.925, 11.525, 82.825, 12.475),
             (80.375, 13.125, 81.275, 14.075), (81.925, 13.125, 82.825, 14.075)]

NEW_TRK = [  # (net, layer, a, b, width)
    ('ULPI_D1', 'F.Cu', (79.19, 12.75), (79.78, 12.64), 0.15),
    ('ULPI_D1', 'F.Cu', (79.78, 12.64), (80.05, 11.92), 0.15),
    ('ULPI_D1', 'F.Cu', (80.05, 11.92), (79.86, 11.5), 0.2),
    ('ULPI_D1', 'F.Cu', (79.86, 11.5), (79.83, 10.9), 0.2),
    ('ULPI_D1', 'F.Cu', (79.83, 10.9), (79.35, 10.35), 0.2),
    ('ULPI_D2', 'F.Cu', (79.438, 13.25), (79.95, 13.25), 0.2),
    ('ULPI_D2', 'F.Cu', (79.95, 13.25), (80.33, 12.88), 0.2),
    ('ULPI_D2', 'In2.Cu', (80.33, 12.88), (80.0, 8.3), 0.25),
    ('ULPI_D3', 'F.Cu', (79.95, 13.75), (79.82, 13.82), 0.2),
    ('ULPI_D3', 'In2.Cu', (79.82, 13.82), (82.2, 11.6), 0.25),
    ('ULPI_D4', 'In2.Cu', (80.2, 14.45), (80.5, 14.2), 0.25),
    ('ULPI_D4', 'In2.Cu', (80.5, 14.2), (80.75, 13.95), 0.25),
    ('ULPI_D4', 'In2.Cu', (80.75, 13.95), (80.875, 13.625), 0.25),
    ('ULPI_D5', 'F.Cu', (79.19, 14.75), (79.7, 14.8), 0.2),
    ('ULPI_D5', 'F.Cu', (79.7, 14.8), (80.35, 15.28), 0.2),
    ('ULPI_D5', 'In2.Cu', (80.35, 15.28), (80.8, 15.55), 0.25),
    ('ULPI_D5', 'In2.Cu', (80.8, 15.55), (81.3, 15.35), 0.25),
    ('ULPI_D6', 'F.Cu', (79.438, 15.25), (79.764, 15.216), 0.2),
    ('ULPI_D6', 'F.Cu', (79.764, 15.216), (80.038, 15.75), 0.2),
    ('ULPI_D6', 'F.Cu', (80.038, 15.75), (80.5, 16.0), 0.2),
    ('ULPI_D6', 'F.Cu', (80.5, 16.0), (81.15, 15.35), 0.2),
    ('ULPI_D6', 'F.Cu', (81.15, 15.35), (80.85, 14.7), 0.2),
    ('ULPI_D6', 'In2.Cu', (80.85, 14.7), (81.375, 14.125), 0.25),
    ('I2C_SCL', 'In2.Cu', (79.15, 10.6), (79.2, 11.1), 0.25),
    ('I2C_SCL', 'In2.Cu', (79.2, 11.1), (79.2, 14.375), 0.25),
    ('I2C_SCL', 'In2.Cu', (79.2, 14.375), (79.0, 14.85), 0.25),
    ('NRST', 'F.Cu', (81.025, 12.0), (80.55, 10.65), 0.2),
    ('NRST', 'F.Cu', (80.55, 10.65), (80.225, 10.5), 0.2),
    ('+3V3D', 'F.Cu', (81.025, 13.75), (81.3, 13.0), 0.2),
    ('+3V3D', 'F.Cu', (81.3, 13.0), (81.85, 12.6), 0.2),
    ('+3V3D', 'F.Cu', (81.85, 12.6), (81.82, 11.0), 0.2),
    ('+3V3D', 'F.Cu', (81.82, 11.0), (81.625, 10.9), 0.2),
]
NEW_VIA = [('ULPI_D2', (80.33, 12.88)), ('ULPI_D3', (79.82, 13.82)),
           ('ULPI_D5', (80.35, 15.28)), ('ULPI_D6', (80.85, 14.7))]


def rk(p):
    return (round(p[0], 3), round(p[1], 3))


def is_victim(it):
    if it.kind == 'trk':
        a, b = rk(it.a), rk(it.b)
        for nn, ll, a0, b0 in RIP_SEGS:
            if it.net == nn and it.layer == ll and {a, b} == {rk(a0), rk(b0)}:
                return True
    if it.kind == 'via':
        for nn, at in RIP_VIAS:
            if it.net == nn and abs(it.a[0] - at[0]) < 0.01 and abs(it.a[1] - at[1]) < 0.01:
                return True
    if it.kind == 'pad' and it.rect in OLD_RECTS:
        return True
    return False


def allowed(m, other):
    return m >= -0.05 and ('+3V3D' in other or '+3V3A' in other)


def main():
    items = G.load_items(SRC)
    for it in items:
        it.layer = {'F': 'F.Cu', 'In2': 'In2.Cu', 'B': 'B.Cu'}.get(it.layer, it.layer)
    pool = []
    for it in items:
        if is_victim(it):
            continue
        if it.kind == 'pad':
            cx = (it.rect[0] + it.rect[2]) / 2; cy = (it.rect[1] + it.rect[3]) / 2
            if it.layer != 'F.Cu' and 74.3 < cx < 79.7 and 11.4 < cy < 16.6:
                continue
        pool.append(it)
    pool.append(G.Item('NRST', 'pad', layer='F.Cu', rect=(80.575, 11.525, 81.475, 12.475)))
    pool.append(G.Item('GND', 'pad', layer='F.Cu', rect=(82.175, 11.525, 83.075, 12.475)))
    pool.append(G.Item('+3V3D', 'pad', layer='F.Cu', rect=(80.575, 13.275, 81.475, 14.225)))
    pool.append(G.Item('GND', 'pad', layer='F.Cu', rect=(82.125, 13.275, 83.025, 14.225)))
    bad = 0
    segs = [(nn, ll, a, b, w / 2) for nn, ll, a, b, w in NEW_TRK]
    for nn, ll, a, b, hw in segs:
        ms = BG.margin_trk(a, b, ll, nn, pool, hw=hw)
        neg = [(m, d) for m, d in ms if m < 0 and not allowed(m, d)]
        if neg:
            bad += len(neg)
            print(f'{nn} {ll} {a}->{b}: negatives={len(neg)} worst={sorted(neg)[:2]}')
    for nn, at in NEW_VIA:
        ms = BG.margin_via(at, nn, pool, r=0.25)
        neg = [(m, d) for m, d in ms if m < 0 and not allowed(m, d)]
        if neg:
            bad += len(neg)
            print(f'via {nn} {at}: negatives={len(neg)} worst={sorted(neg)[:2]}')
    for i, (n1, l1, a, b, h1) in enumerate(segs):
        for n2, l2, c, d, h2 in segs[i + 1:]:
            if n1 != n2 and l1 == l2:
                m = BG.seg_seg(a, b, c, d) - h1 - h2 - BG.clr(n2)
                if m < 0 and not allowed(m, n2):
                    bad += 1
                    print(f'NN trk-trk {n1} {a}->{b} vs {n2} {c}->{d}: {m:+.3f}')
        for n2, c in NEW_VIA:
            if n1 != n2:
                m = BG.pt_seg(c, a, b) - h1 - 0.25 - BG.clr(n2)
                if m < 0 and not allowed(m, n2):
                    bad += 1
                    print(f'NN trk-via {n1} {a}->{b} vs via {n2}@{c}: {m:+.3f}')
    for i, (n1, c1) in enumerate(NEW_VIA):
        for n2, c2 in NEW_VIA[i + 1:]:
            if n1 != n2:
                m = __import__('math').hypot(c1[0] - c2[0], c1[1] - c2[1]) - 0.5 - BG.clr(n2)
                if m < 0 and not allowed(m, n2):
                    bad += 1
                    print(f'NN via-via {n1}@{c1} vs {n2}@{c2}: {m:+.3f}')
    print(f'gate negatives: {bad}')
    if bad:
        print('GATE FAILED — not building')
        return
    print('gate clean; building')
    nets = ['ULPI_D1', 'ULPI_D2', 'ULPI_D3', 'ULPI_D4', 'ULPI_D5',
            'ULPI_D6', 'I2C_SCL', 'NRST', '+3V3D']
    s = BL.Surgery(SRC, DST, nets=nets)
    layb = {'F.Cu': BL.F, 'In2.Cu': BL.IN2, 'B.Cu': BL.B}
    for fp in s.b.GetFootprints():
        ref = fp.GetReference()
        p0 = fp.GetPosition()
        if ref == 'C19':
            fp.SetPosition(BL.pcbnew.VECTOR2I(p0.x + BL.pcbnew.FromMM(0.25), p0.y))
        elif ref == 'C48':
            fp.SetPosition(BL.pcbnew.VECTOR2I(p0.x + BL.pcbnew.FromMM(0.2),
                                              p0.y + BL.pcbnew.FromMM(0.15)))
    victims = []
    for nn, ll, a, b in RIP_SEGS:
        victims += s.find_seg(nn, layb[ll], a, b)
    for nn, at in RIP_VIAS:
        victims += s.find_via(nn, at)
    s.remove(victims)
    for nn, ll, a, b, w in NEW_TRK:
        s.add_track(nn, layb[ll], a, b, w)
    for nn, at in NEW_VIA:
        s.add_via(nn, at[0], at[1], dia=0.5, drill=0.3)
    s.finish()


if __name__ == '__main__':
    main()

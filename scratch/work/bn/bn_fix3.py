#!/usr/bin/env python3
"""bn fix3 (parent-driven): the D2-D6 knot on exp271 -> exp272, with
C48 shrunk 0603 -> 0402 (C_0402_1005Metric, same centre; the C20/C28
precedent). The shrink moves C48 pad1's west edge 80.375 -> 80.84 and
opens the east column: the joint via grid (bn_fix3_grid.py, true 0402
rects) found 2.8M legal tuples; the chosen set optimises feedability:
  D2 via (80.35,13.05) — east wedge dive, In2 straight north to the
     existing far via (80.0,8.3)
  D3 via (79.9,13.7) — the west pocket
  D5 via (80.95,14.8) — feed zigzags between D4's via disc (cross x80.2
     at y15.02) and D6's via disc (cross x80.5 at y14.88)
  D6 via (80.5,15.45) — saddle from the west, In2 head ducks north
     under D5's via then east to the chain at (81.375,14.125)
  D4 via stays (80.2,14.45); its In2 head re-lays to join the chain
     further east at (81.375,13.125), clearing D3's legs.
C48 pad2 (GND) is zone-connected (no track/via) — the swap keeps it in
the F GND zone; connectivity is referee-checked after the build.
Gate: bm_gate margins vs victim-filtered pool (C48's pads replaced by
the true 0402 rects) + new-vs-new, KiCad pricing 0.20 flat.
Usage: bn_fix3.py [--gate-only]"""
import math
import sys
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/hw')
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/scratch/work/bm')
import gridroute as G
import bm_gate as BG
import build_lib as BL

SRC = 'hw/pdlvds_rx.exp271.kicad_pcb'
DST = 'hw/pdlvds_rx.exp272.kicad_pcb'

# (net, layer, a, b) — every entry verified present in dump271 (exp271)
RIP_SEGS = [
    ('ULPI_D2', 'F.Cu', (79.438, 13.25), (79.875, 13.125)),
    ('ULPI_D2', 'F.Cu', (79.875, 13.125), (80.3, 12.8)),
    ('ULPI_D2', 'In2.Cu', (80.3, 12.8), (80.0, 8.3)),
    ('ULPI_D3', 'F.Cu', (79.95, 13.75), (80.15, 13.7)),
    ('ULPI_D3', 'In2.Cu', (80.15, 13.7), (82.2, 11.6)),
    ('ULPI_D5', 'F.Cu', (79.188, 14.75), (79.75, 14.78)),
    ('ULPI_D5', 'F.Cu', (79.75, 14.78), (80.15, 15.05)),
    ('ULPI_D5', 'F.Cu', (80.15, 15.05), (80.35, 15.14)),
    ('ULPI_D5', 'F.Cu', (80.35, 15.14), (80.25, 15.188)),
    ('ULPI_D5', 'In2.Cu', (80.25, 15.188), (81.3, 15.35)),
    ('ULPI_D5', 'In2.Cu', (81.3, 15.35), (82.0, 15.3)),
    ('ULPI_D6', 'F.Cu', (79.438, 15.25), (79.875, 15.375)),
    ('ULPI_D6', 'F.Cu', (79.875, 15.375), (80.125, 15.625)),
    ('ULPI_D6', 'F.Cu', (80.125, 15.625), (80.625, 15.625)),
    ('ULPI_D6', 'F.Cu', (80.625, 15.625), (80.0, 15.75)),
    ('ULPI_D6', 'F.Cu', (80.0, 15.75), (80.875, 15.75)),
    ('ULPI_D6', 'F.Cu', (80.875, 15.75), (81.0, 14.4)),
    ('ULPI_D6', 'In2.Cu', (81.0, 14.4), (81.375, 14.125)),
    ('+3V3D', 'F.Cu', (80.825, 13.6), (81.3, 13.0)),
]
RIP_VIAS = [('ULPI_D2', (80.3, 12.8)), ('ULPI_D3', (80.15, 13.7)),
            ('ULPI_D5', (80.25, 15.188)),
            ('ULPI_D6', (81.0, 14.4))]

NEW_TRK = [  # (net, layer, a, b, width)
    ('ULPI_D2', 'F.Cu', (79.438, 13.25), (79.95, 13.1), 0.2),
    ('ULPI_D2', 'F.Cu', (79.95, 13.1), (80.28, 12.95), 0.2),
    ('ULPI_D2', 'In2.Cu', (80.28, 12.95), (80.0, 8.3), 0.25),
    ('ULPI_D3', 'F.Cu', (79.95, 13.75), (79.93, 13.73), 0.2),
    ('ULPI_D3', 'In2.Cu', (79.93, 13.73), (82.2, 11.6), 0.25),
    ('ULPI_D5', 'F.Cu', (79.19, 14.75), (79.75, 14.82), 0.2),
    ('ULPI_D5', 'F.Cu', (79.75, 14.82), (80.35, 15.3), 0.2),
    ('ULPI_D5', 'In2.Cu', (80.35, 15.3), (81.95, 15.65), 0.25),
    ('ULPI_D5', 'In2.Cu', (81.95, 15.65), (82.0, 15.3), 0.25),
    ('ULPI_D6', 'F.Cu', (79.438, 15.25), (79.72, 15.27), 0.2),
    ('ULPI_D6', 'F.Cu', (79.72, 15.27), (80.18, 15.95), 0.2),
    ('ULPI_D6', 'F.Cu', (80.18, 15.95), (80.7, 15.95), 0.2),
    ('ULPI_D6', 'F.Cu', (80.7, 15.95), (80.95, 15.3), 0.2),
    ('ULPI_D6', 'F.Cu', (80.95, 15.3), (80.85, 14.8), 0.2),
    ('ULPI_D6', 'In2.Cu', (80.85, 14.8), (81.375, 14.125), 0.25),
    ('+3V3D', 'F.Cu', (81.12, 13.6), (81.3, 13.0), 0.2),
]
NEW_VIA = [('ULPI_D2', (80.28, 12.95)), ('ULPI_D3', (79.93, 13.73)),
           ('ULPI_D5', (80.35, 15.3)), ('ULPI_D6', (80.85, 14.8))]

# C48 pads: old centres (0603) dropped from the pool; true 0402 rects in
C48_OLD = [(80.825, 13.6), (82.375, 13.6)]
C48_NEW = [('+3V3D', (80.84, 13.29, 81.40, 13.91)),
           ('GND', (81.80, 13.29, 82.36, 13.91))]


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
    return False


ALLOW = []


def gate():
    BG.clr = lambda net: 0.20  # KiCad DRC pricing
    items = G.load_items(SRC)
    for it in items:
        it.layer = {'F': 'F.Cu', 'In2': 'In2.Cu', 'B': 'B.Cu'}.get(it.layer, it.layer)
    pool = []
    for it in items:
        if is_victim(it):
            continue
        if it.kind == 'pad':
            cx = (it.rect[0] + it.rect[2]) / 2; cy = (it.rect[1] + it.rect[3]) / 2
            if any(abs(cx - ox) < 0.01 and abs(cy - oy) < 0.01 for ox, oy in C48_OLD):
                continue
        pool.append(it)
    for net, rect in C48_NEW:
        pool.append(G.Item(net, 'pad', layer='F.Cu', rect=rect))
    bad = 0
    segs = [(nn, ll, a, b, w / 2) for nn, ll, a, b, w in NEW_TRK]
    for nn, ll, a, b, hw in segs:
        ms = BG.margin_trk(a, b, ll, nn, pool, hw=hw)
        neg = [(m, d) for m, d in ms if m < 0 and not any(a2 == nn and sub in d for a2, sub in ALLOW)]
        if neg:
            bad += len(neg)
            print(f'{nn} {ll} {a}->{b}: negatives={len(neg)} worst={sorted(neg)}')
    for nn, at in NEW_VIA:
        ms = BG.margin_via(at, nn, pool, r=0.25)
        neg = [(m, d) for m, d in ms if m < 0 and not any(a2 == nn and sub in d for a2, sub in ALLOW)]
        if neg:
            bad += len(neg)
            print(f'via {nn} {at}: negatives={len(neg)} worst={sorted(neg)}')
    for i, (n1, l1, a, b, h1) in enumerate(segs):
        for n2, l2, c, d, h2 in segs[i + 1:]:
            if n1 != n2 and l1 == l2:
                m = BG.seg_seg(a, b, c, d) - h1 - h2 - BG.clr(n2)
                if m < 0:
                    bad += 1
                    print(f'NN trk-trk {n1} {a}->{b} vs {n2} {c}->{d}: {m:+.3f}')
        for n2, c in NEW_VIA:
            if n1 != n2:
                m = BG.pt_seg(c, a, b) - h1 - 0.25 - BG.clr(n2)
                if m < 0:
                    bad += 1
                    print(f'NN trk-via {n1} {a}->{b} vs via {n2}@{c}: {m:+.3f}')
    for i, (n1, c1) in enumerate(NEW_VIA):
        for n2, c2 in NEW_VIA[i + 1:]:
            if n1 != n2:
                m = math.hypot(c1[0] - c2[0], c1[1] - c2[1]) - 0.5 - BG.clr(n2)
                if m < 0:
                    bad += 1
                    print(f'NN via-via {n1}@{c1} vs {n2}@{c2}: {m:+.3f}')
    print(f'gate negatives: {bad}')
    return bad


def swap_c48(s):
    """Replace C48's footprint with C_0402_1005Metric, same centre."""
    import pcbnew
    old = None
    for fp in s.b.GetFootprints():
        if fp.GetReference() == 'C48':
            old = fp
            break
    assert old is not None
    codes = {pad.GetNumber(): pad.GetNetCode() for pad in old.Pads()}
    new = pcbnew.FootprintLoad(
        '/usr/share/kicad/footprints/Capacitor_SMD.pretty',
        'C_0402_1005Metric')
    assert new is not None
    new.SetPosition(old.GetPosition())
    new.SetOrientation(old.GetOrientation())
    new.SetReference('C48')
    new.SetValue(old.GetValue())
    for pad in new.Pads():
        pad.SetNetCode(codes[pad.GetNumber()])
    s.b.Remove(old)
    s.b.Add(new)
    print('C48 footprint swapped 0603 -> 0402 (pads at +/-0.48)')


def build():
    nets = ['ULPI_D2', 'ULPI_D3', 'ULPI_D4', 'ULPI_D5', 'ULPI_D6', '+3V3D']
    s = BL.Surgery(SRC, DST, nets=nets)
    swap_c48(s)
    layb = {'F.Cu': BL.F, 'In2.Cu': BL.IN2, 'B.Cu': BL.B}
    victims = []
    for nn, ll, a, b in RIP_SEGS:
        found = s.find_seg(nn, layb[ll], a, b)
        assert len(found) == 1, f'rip seg {nn} {ll} {a}->{b}: {len(found)} found'
        victims += found
    for nn, at in RIP_VIAS:
        found = s.find_via(nn, at)
        assert len(found) == 1, f'rip via {nn} {at}: {len(found)} found'
        victims += found
    s.remove(victims)
    print(f'ripped {len(victims)} items (asserted)')
    for nn, ll, a, b, w in NEW_TRK:
        s.add_track(nn, layb[ll], a, b, w)
    for nn, at in NEW_VIA:
        s.add_via(nn, at[0], at[1], dia=0.5, drill=0.3)
    s.finish()


if __name__ == '__main__':
    bad = gate()
    if bad:
        print('GATE FAILED — not building')
        sys.exit(1)
    print('gate clean')
    if '--gate-only' not in sys.argv:
        build()

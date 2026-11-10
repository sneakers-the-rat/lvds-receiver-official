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
    ('+3V3D', 'F.Cu', (81.3, 13.0), (81.55, 12.7)),
    ('+3V3D', 'F.Cu', (81.55, 12.7), (81.55, 11.6)),
    ('+3V3D', 'F.Cu', (81.55, 11.6), (81.625, 10.9)),
    ('+3V3D', 'In2.Cu', (81.575, 10.875), (81.625, 10.9)),
    ('NRST', 'F.Cu', (80.775, 12.0), (80.55, 10.65)),
    ('ULPI_D2', 'F.Cu', (79.438, 13.25), (79.875, 13.125)),
    ('ULPI_D2', 'F.Cu', (79.875, 13.125), (80.3, 12.8)),
    ('ULPI_D2', 'In2.Cu', (80.3, 12.8), (80.0, 8.3)),
    ('ULPI_D3', 'F.Cu', (79.95, 13.75), (80.15, 13.7)),
    ('ULPI_D3', 'In2.Cu', (80.15, 13.7), (82.2, 11.6)),
    ('ULPI_D4', 'F.Cu', (79.875, 14.375), (80.2, 14.45)),
    ('ULPI_D4', 'In2.Cu', (80.2, 14.45), (80.375, 14.125)),
    ('ULPI_D4', 'In2.Cu', (80.375, 14.125), (80.625, 13.875)),    ('ULPI_D5', 'F.Cu', (79.188, 14.75), (79.75, 14.78)),
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
RIP_VIAS = [('+3V3D', (81.625, 10.9)), ('ULPI_D2', (80.3, 12.8)), ('ULPI_D3', (80.15, 13.7)),
            ('ULPI_D4', (80.2, 14.45)),
            ('ULPI_D5', (80.25, 15.188)),
            ('ULPI_D6', (81.0, 14.4))]

NEW_TRK = [  # (net, layer, a, b, width)
    ('NRST', 'F.Cu', (81.07, 11.85), (80.55, 10.65), 0.2),
    ('ULPI_D2', 'F.Cu', (79.438, 13.25), (80.0, 13.12), 0.2),
    ('ULPI_D2', 'F.Cu', (80.0, 13.12), (80.52, 12.52), 0.2),
    ('ULPI_D2', 'In2.Cu', (80.52, 12.52), (80.05, 12.4), 0.25),
    ('ULPI_D2', 'In2.Cu', (80.05, 12.4), (80.0, 8.3), 0.25),
    ('ULPI_D3', 'F.Cu', (79.95, 13.75), (79.93, 13.73), 0.2),
    ('ULPI_D3', 'In2.Cu', (79.93, 13.73), (80.88, 12.98), 0.25),
    ('ULPI_D3', 'In2.Cu', (80.88, 12.98), (82.2, 11.6), 0.25),
    ('ULPI_D4', 'F.Cu', (79.875, 14.375), (80.46, 14.21), 0.2),
    ('ULPI_D4', 'In2.Cu', (80.46, 14.21), (81.375, 13.125), 0.25),
    ('ULPI_D5', 'F.Cu', (79.19, 14.75), (79.75, 14.82), 0.2),
    ('ULPI_D5', 'F.Cu', (79.75, 14.82), (80.13, 14.9), 0.2),
    ('ULPI_D5', 'In2.Cu', (80.13, 14.9), (80.85, 15.85), 0.25),
    ('ULPI_D5', 'In2.Cu', (80.85, 15.85), (82.0, 15.3), 0.25),
    ('ULPI_D6', 'F.Cu', (79.438, 15.25), (79.62, 15.26), 0.2),
    ('ULPI_D6', 'F.Cu', (79.62, 15.26), (80.05, 15.5), 0.2),
    ('ULPI_D6', 'F.Cu', (80.05, 15.5), (80.3, 15.75), 0.2),
    ('ULPI_D6', 'F.Cu', (80.3, 15.75), (80.72, 15.82), 0.2),
    ('ULPI_D6', 'F.Cu', (80.72, 15.82), (80.85, 14.81), 0.2),
    ('ULPI_D6', 'In2.Cu', (80.85, 14.81), (81.375, 14.125), 0.25),
    ('+3V3D', 'F.Cu', (81.12, 13.6), (81.3, 13.0), 0.2),
    ('+3V3D', 'F.Cu', (81.3, 13.0), (82.72, 12.9), 0.2),
    ('+3V3D', 'F.Cu', (82.72, 12.9), (82.72, 11.0), 0.2),
    ('+3V3D', 'F.Cu', (82.72, 11.0), (82.3, 10.5), 0.2),
    ('+3V3D', 'F.Cu', (82.3, 10.5), (81.7, 10.25), 0.2),
    ('+3V3D', 'In2.Cu', (81.7, 10.25), (81.575, 10.875), 0.3),
    ('GND', 'F.Cu', (82.03, 11.85), (82.08, 11.08), 0.3),
    ('GND', 'F.Cu', (82.08, 11.08), (81.15, 10.82), 0.3),
    ('GND', 'F.Cu', (80.995, 10.24), (81.135, 9.9), 0.3),
]
NEW_VIA = [('ULPI_D2', (80.52, 12.52)), ('ULPI_D3', (79.93, 13.73)),
           ('ULPI_D4', (80.46, 14.21)), ('ULPI_D5', (80.13, 14.9)),
           ('ULPI_D6', (80.85, 14.81)), ('+3V3D', (81.7, 10.25))]

# C48 pads: old centres (0603) dropped from the pool; true 0402 rects in
C48_OLD = [(80.825, 13.6), (82.375, 13.6)]
C48_NEW = [('+3V3D', (80.84, 13.29, 81.40, 13.91)),
           ('GND', (81.80, 13.29, 82.36, 13.91))]
# C19 likewise: 0603 -> 0402 and centre nudged 0.15 north
C19_OLD = [(80.775, 12.0), (82.325, 12.0)]
C19_NEW = [('NRST', (80.79, 11.54, 81.35, 12.16)),
           ('GND', (81.75, 11.54, 82.31, 12.16))]


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
            if any(abs(cx - ox) < 0.01 and abs(cy - oy) < 0.01
                   for ox, oy in C48_OLD + C19_OLD):
                continue
        pool.append(it)
    for net, rect in C48_NEW + C19_NEW:
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


def collect_swaps(s):
    """Collect C48/C19 0603 -> 0402 swaps WITHOUT mutating the board.

    build_lib's standing note: after any BOARD.Remove(), fresh
    GetTracks()/GetFootprints() can return a non-iterable wrapper.
    So: find everything first (rips + both old footprints), remove
    everything, then add. New footprints follow ay's C20 pattern
    (pass 214): configured fully, Added after the removes, pad
    netcodes set after the Add (before-Add SetNetCode does not
    stick). C19's centre is nudged 0.15 north."""
    import pcbnew
    swaps = []
    for ref, pos in (('C48', (81.6, 13.6)), ('C19', (81.55, 11.85))):
        old = None
        for fp in s.b.GetFootprints():
            if fp.GetReference() == ref:
                old = fp
        assert old is not None, ref
        netmap = {pad.GetNumber(): (pad.GetNetname(), pad.GetNetCode())
                  for pad in old.Pads()}
        fieldpos = {}
        for f in old.Fields():
            fp0 = f.GetPosition()
            fieldpos[f.GetName()] = (fp0.x, fp0.y)
        new = pcbnew.FootprintLoad(
            '/usr/share/kicad/footprints/Capacitor_SMD.pretty',
            'C_0402_1005Metric')
        assert new is not None
        new.SetPosition(pcbnew.VECTOR2I(int(pos[0] * 1e6), int(pos[1] * 1e6)))
        new.SetOrientation(old.GetOrientation())
        new.SetReference(ref)
        new.SetValue(old.GetValue())
        for f in new.Fields():
            if f.GetName() in fieldpos:
                fx, fy = fieldpos[f.GetName()]
                f.SetPosition(pcbnew.VECTOR2I(fx, fy))
        swaps.append((ref, old, new, netmap))
        print(f'{ref} swap collected (0603 -> 0402 at {pos})')
    return swaps


def build():
    nets = ['ULPI_D2', 'ULPI_D3', 'ULPI_D4', 'ULPI_D5', 'ULPI_D6',
            '+3V3D', 'NRST', 'GND']
    s = BL.Surgery(SRC, DST, nets=nets)
    layb = {'F.Cu': BL.F, 'In2.Cu': BL.IN2, 'B.Cu': BL.B}
    # 1. find everything while the board is pristine
    victims = []
    for nn, ll, a, b in RIP_SEGS:
        found = s.find_seg(nn, layb[ll], a, b)
        assert len(found) == 1, f'rip seg {nn} {ll} {a}->{b}: {len(found)} found'
        victims += found
    for nn, at in RIP_VIAS:
        found = s.find_via(nn, at)
        assert len(found) == 1, f'rip via {nn} {at}: {len(found)} found'
        victims += found
    swaps = collect_swaps(s)
    # 2. remove everything (no board iteration after this point)
    s.remove(victims)
    print(f'ripped {len(victims)} items (asserted)')
    for ref, old, new, netmap in swaps:
        s.b.Remove(old)
    # 3. add everything
    for ref, old, new, netmap in swaps:
        s.b.Add(new)
        for pad in new.Pads():
            pad.SetNetCode(netmap[pad.GetNumber()][1])
            assert pad.GetNetname() == netmap[pad.GetNumber()][0], (
                ref, pad.GetNumber(), pad.GetNetname())
        print(f'{ref} swapped 0603 -> 0402')
    for nn, ll, a, b, w in NEW_TRK:
        s.add_track(nn, layb[ll], a, b, w)
    for nn, at in NEW_VIA:
        s.add_via(nn, at[0], at[1], dia=(0.6 if nn == '+3V3D' else 0.5),
                  drill=0.3)
    s.finish()


if __name__ == '__main__':
    bad = gate()
    if bad:
        print('GATE FAILED — not building')
        sys.exit(1)
    print('gate clean')
    if '--gate-only' not in sys.argv:
        build()

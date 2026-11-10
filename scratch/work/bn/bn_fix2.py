#!/usr/bin/env python3
"""bn fix2 (parent-driven): east D-fan repair on exp270 -> exp271.
Fixes vs bn_fix1 v4: rip list corrected against dump2 (the AUTHORITATIVE
board dump — v4 ripped two D6 segments that don't exist and missed the
real densified D5/D6 F pieces); moved-part pads gated as TRUE rects
computed from the footprints (v4's OLD_RECTS missed by 0.05, double-
counting C19's GND pad); SCL In2 jogged (x79.5 north of the +3V3A via
latitude, x79.2 south past D3's via); D1 first legs bowed east of D0's
pad; D3 via (79.92,13.66) with a SINGLE direct In2 leg to (82.2,11.6)
(the original's geometry); D5 via (80.55,15.35); D6 via (80.95,14.55).
Gate: bm_gate margins vs victim-filtered pool + new-vs-new, >= 0.
Usage: bn_fix2.py [--gate-only]"""
import math
import sys
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/hw')
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/scratch/work/bm')
import gridroute as G
import bm_gate as BG
import build_lib as BL

SRC = 'hw/pdlvds_rx.exp270.kicad_pcb'
DST = 'hw/pdlvds_rx.exp271.kicad_pcb'

# (net, layer, a, b) — every entry verified present in dump2 (exp270)
RIP_SEGS = [
    ('ULPI_D1', 'F.Cu', (79.188, 12.75), (79.438, 12.75)),
    ('ULPI_D1', 'F.Cu', (79.438, 12.75), (79.93, 12.6)),
    ('ULPI_D1', 'F.Cu', (79.93, 12.6), (79.93, 11.95)),
    ('ULPI_D1', 'F.Cu', (79.93, 11.95), (79.78, 11.5)),
    ('ULPI_D1', 'F.Cu', (79.78, 11.5), (79.75, 10.9)),
    ('ULPI_D1', 'F.Cu', (79.75, 10.9), (79.35, 10.35)),
    ('ULPI_D2', 'F.Cu', (79.438, 13.25), (79.875, 13.125)),
    ('ULPI_D2', 'F.Cu', (79.875, 13.125), (80.3, 12.8)),
    ('ULPI_D2', 'In2.Cu', (80.3, 12.8), (80.0, 8.3)),
    ('ULPI_D3', 'F.Cu', (79.95, 13.75), (80.15, 13.7)),
    ('ULPI_D3', 'In2.Cu', (80.15, 13.7), (82.2, 11.6)),
    ('ULPI_D4', 'In2.Cu', (80.2, 14.45), (80.375, 14.125)),
    ('ULPI_D4', 'In2.Cu', (80.375, 14.125), (80.625, 13.875)),
    ('ULPI_D4', 'In2.Cu', (80.625, 13.875), (80.875, 13.625)),
    ('ULPI_D5', 'F.Cu', (79.188, 14.75), (79.75, 14.78)),
    ('ULPI_D5', 'F.Cu', (79.75, 14.78), (80.15, 15.05)),
    ('ULPI_D5', 'F.Cu', (80.15, 15.05), (80.35, 15.14)),
    ('ULPI_D5', 'F.Cu', (80.35, 15.14), (80.25, 15.188)),
    ('ULPI_D5', 'In2.Cu', (80.25, 15.188), (81.3, 15.35)),
    ('ULPI_D6', 'F.Cu', (79.438, 15.25), (79.875, 15.375)),
    ('ULPI_D6', 'F.Cu', (79.875, 15.375), (80.125, 15.625)),
    ('ULPI_D6', 'F.Cu', (80.125, 15.625), (80.625, 15.625)),
    ('ULPI_D6', 'F.Cu', (80.625, 15.625), (80.0, 15.75)),
    ('ULPI_D6', 'F.Cu', (80.0, 15.75), (80.875, 15.75)),
    ('ULPI_D6', 'F.Cu', (80.875, 15.75), (81.0, 14.4)),
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
MOVES = {'C19': (0.25, 0.0), 'C48': (0.2, 0.15)}

NEW_TRK = [  # (net, layer, a, b, width)
    ('ULPI_D1', 'F.Cu', (79.19, 12.75), (79.82, 12.68), 0.15),
    ('ULPI_D1', 'F.Cu', (79.82, 12.68), (80.02, 12.35), 0.15),
    ('ULPI_D1', 'F.Cu', (80.02, 12.35), (79.92, 11.7), 0.15),
    ('ULPI_D1', 'F.Cu', (79.92, 11.7), (79.86, 11.5), 0.2),
    ('ULPI_D1', 'F.Cu', (79.86, 11.5), (79.83, 10.9), 0.2),
    ('ULPI_D1', 'F.Cu', (79.83, 10.9), (79.35, 10.35), 0.2),
    ('ULPI_D2', 'F.Cu', (79.438, 13.25), (79.95, 13.1), 0.2),
    ('ULPI_D2', 'F.Cu', (79.95, 13.1), (80.1, 12.6), 0.2),
    ('ULPI_D2', 'In2.Cu', (80.1, 12.6), (80.0, 8.3), 0.25),
    ('ULPI_D3', 'F.Cu', (79.95, 13.75), (80.2, 13.75), 0.2),
    ('ULPI_D3', 'In2.Cu', (80.2, 13.75), (80.6, 13.5), 0.25),
    ('ULPI_D3', 'In2.Cu', (80.6, 13.5), (81.3, 12.3), 0.25),
    ('ULPI_D3', 'In2.Cu', (81.3, 12.3), (82.2, 11.6), 0.25),
    ('ULPI_D4', 'In2.Cu', (80.2, 14.45), (80.55, 14.32), 0.25),
    ('ULPI_D4', 'In2.Cu', (80.55, 14.32), (80.8, 14.08), 0.25),
    ('ULPI_D4', 'In2.Cu', (80.8, 14.08), (80.875, 13.625), 0.25),
    ('ULPI_D5', 'F.Cu', (79.19, 14.75), (79.75, 14.82), 0.2),
    ('ULPI_D5', 'F.Cu', (79.75, 14.82), (80.15, 15.2), 0.2),
    ('ULPI_D5', 'In2.Cu', (80.15, 15.2), (80.9, 15.6), 0.25),
    ('ULPI_D5', 'In2.Cu', (80.9, 15.6), (81.3, 15.35), 0.25),
    ('ULPI_D6', 'F.Cu', (79.438, 15.25), (79.7, 15.55), 0.2),
    ('ULPI_D6', 'F.Cu', (79.7, 15.55), (80.35, 15.95), 0.2),
    ('ULPI_D6', 'F.Cu', (80.35, 15.95), (80.9, 16.05), 0.2),
    ('ULPI_D6', 'F.Cu', (80.9, 16.05), (81.15, 15.35), 0.2),
    ('ULPI_D6', 'F.Cu', (81.15, 15.35), (80.85, 14.8), 0.2),
    ('ULPI_D6', 'In2.Cu', (80.85, 14.8), (81.375, 14.125), 0.25),
    ('I2C_SCL', 'In2.Cu', (79.15, 10.6), (79.5, 11.15), 0.25),
    ('I2C_SCL', 'In2.Cu', (79.5, 11.15), (79.5, 12.6), 0.25),
    ('I2C_SCL', 'In2.Cu', (79.5, 12.6), (79.2, 13.2), 0.25),
    ('I2C_SCL', 'In2.Cu', (79.2, 13.2), (79.2, 14.375), 0.25),
    ('I2C_SCL', 'In2.Cu', (79.2, 14.375), (79.0, 14.85), 0.25),
    ('NRST', 'F.Cu', (81.025, 12.0), (80.55, 10.65), 0.2),
    ('NRST', 'F.Cu', (80.55, 10.65), (80.225, 10.5), 0.2),
    ('+3V3D', 'F.Cu', (81.025, 13.75), (81.3, 13.0), 0.2),
    ('+3V3D', 'F.Cu', (81.3, 13.0), (81.8, 12.6), 0.2),
    ('+3V3D', 'F.Cu', (81.8, 12.6), (81.78, 11.0), 0.2),
    ('+3V3D', 'F.Cu', (81.78, 11.0), (81.625, 10.9), 0.2),
]
NEW_VIA = [('ULPI_D2', (80.1, 12.6)), ('ULPI_D3', (80.2, 13.75)),
           ('ULPI_D5', (80.15, 15.2)), ('ULPI_D6', (80.85, 14.8))]


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


def moved_pad_items():
    """True pad rects for C19/C48 at their NEW positions, from the board."""
    import wx
    wx.App(False)
    import pcbnew
    b = pcbnew.LoadBoard(SRC)
    out, centres = [], []
    for fp in b.GetFootprints():
        ref = fp.GetReference()
        if ref not in MOVES:
            continue
        dx, dy = MOVES[ref]
        c = fp.GetPosition()
        centres.append((c.x / 1e6, c.y / 1e6))
        rot = fp.GetOrientation().AsDegrees() % 180
        for pad in fp.Pads():
            p = pad.GetPosition()
            sx, sy = pad.GetSize().x / 1e6, pad.GetSize().y / 1e6
            if rot > 45:
                sx, sy = sy, sx
            cx, cy = p.x / 1e6 + dx, p.y / 1e6 + dy
            layers = []
            if pad.IsOnLayer(pcbnew.F_Cu):
                layers.append('F.Cu')
            if pad.IsOnLayer(pcbnew.B_Cu):
                layers.append('B.Cu')
            for lay in layers or ['F.Cu']:
                out.append(G.Item(pad.GetNetname(), 'pad', layer=lay,
                                  rect=(cx - sx / 2, cy - sy / 2, cx + sx / 2, cy + sy / 2)))
    return out, centres


ALLOW = []


def gate():
    BG.clr = lambda net: 0.20  # KiCad DRC pricing (see pairgrid note)
    items = G.load_items(SRC)
    for it in items:
        it.layer = {'F': 'F.Cu', 'In2': 'In2.Cu', 'B': 'B.Cu'}.get(it.layer, it.layer)
    new_pads, centres = moved_pad_items()
    pool = []
    for it in items:
        if is_victim(it):
            continue
        if it.kind == 'pad' and any(abs((it.rect[0] + it.rect[2]) / 2 - cx) < 1.05 and
                                    abs((it.rect[1] + it.rect[3]) / 2 - cy) < 1.05
                                    for cx, cy in centres):
            continue
        pool.append(it)
    pool += new_pads
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


def build():
    nets = ['ULPI_D1', 'ULPI_D2', 'ULPI_D3', 'ULPI_D4', 'ULPI_D5',
            'ULPI_D6', 'I2C_SCL', 'NRST', '+3V3D']
    s = BL.Surgery(SRC, DST, nets=nets)
    layb = {'F.Cu': BL.F, 'In2.Cu': BL.IN2, 'B.Cu': BL.B}
    for fp in s.b.GetFootprints():
        ref = fp.GetReference()
        if ref in MOVES:
            dx, dy = MOVES[ref]
            p0 = fp.GetPosition()
            fp.SetPosition(BL.pcbnew.VECTOR2I(p0.x + BL.pcbnew.FromMM(dx),
                                              p0.y + BL.pcbnew.FromMM(dy)))
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

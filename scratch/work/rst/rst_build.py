#!/usr/bin/env python3
"""rst build (parent-driven): USB_RST on exp272 -> exp273.

Composite, ported from bk's exp258 build (which connected the net at
41 DRC violations) and re-based to exp272 (U7 re-placed +0.75 east in
pass 220's repair; the +3V3A d0.8 via at (73.625,10.625) that sealed
bk's journey is GONE — +3V3A now feeds via (75.58,11.7)):

  DM_PHY F loop re-laid west (bk verbatim) to open the dive.
  RST dive via (74.5,17.25) d0.5, F stub from U7.9 pad (75.0,16.875)
  (south-dive triple RST/DIR/NXT chosen by a joint via grid on exp272:
  RST (74.5,17.25) +0.451, DIR (74.45,18.25), NXT (74.65,19.0)).
  DIR / NXT escapes re-fanned (bk topology, exp272 pad points).
  RBIAS via re-placed (73.7,11.55) d0.5 + In2 column shifted -0.30;
  CK column bows east at the via latitude to open the journey's pass.
  CK jog re-laid shallower (74.38,10.28).
  RST In2 journey west of the CK column, surfacing at (74.72,6.02)
  d0.5 (bk's d0.40 surf via was below the board minimum; the CK/RST
  via pair at (75.48,5.92)/(74.72,6.02) is 0.77 apart).
  CK arrival per bh: via (75.48,5.92) d0.5, sagging F escape, In2 bow.
  BIST / MOSI / SCL window nudges (bh via bk) to clear the arrival.

Gate: bm_gate margins vs victim-filtered pool + new-vs-new, KiCad
pricing 0.20 flat (the bn_fix3 harness). Usage: rst_build.py [--gate-only]
"""
import math
import sys
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/hw')
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/scratch/work/bm')
import gridroute as G
import bm_gate as BG
import build_lib as BL

SRC = 'hw/pdlvds_rx.exp272.kicad_pcb'
DST = 'hw/pdlvds_rx.exp273.kicad_pcb'

RIP_SEGS = [
    # DM_PHY F loop west part (exp257 coords, verified identical on exp272)
    ('DM_PHY', 'F.Cu', (74.125, 18.625), (74.125, 17.375)),
    ('DM_PHY', 'F.Cu', (74.125, 17.375), (73.562, 17.0)),
    ('DM_PHY', 'F.Cu', (73.875, 18.875), (74.125, 18.625)),
    ('DM_PHY', 'F.Cu', (73.625, 19.125), (73.875, 18.875)),
    # DIR full escape re-fan (grid winner: via (74.45,18.25))
    ('ULPI_DIR', 'F.Cu', (76.5, 16.438), (76.46, 17.08)),
    ('ULPI_DIR', 'F.Cu', (76.46, 17.08), (76.24, 17.42)),
    ('ULPI_DIR', 'F.Cu', (76.24, 17.42), (76.08, 17.6)),
    ('ULPI_DIR', 'F.Cu', (76.08, 17.6), (75.5, 17.8)),
    ('ULPI_DIR', 'F.Cu', (75.5, 17.8), (74.84, 18.07)),
    ('ULPI_DIR', 'B.Cu', (74.84, 18.07), (73.3, 18.42)),
    # NXT full escape re-fan (grid winner: via (74.65,19.0))
    ('ULPI_NXT', 'F.Cu', (76.0, 16.438), (75.9, 17.14)),
    ('ULPI_NXT', 'F.Cu', (75.9, 17.14), (75.1, 17.32)),
    ('ULPI_NXT', 'F.Cu', (75.1, 17.32), (74.94, 17.36)),
    ('ULPI_NXT', 'In2.Cu', (74.94, 17.36), (74.1, 17.7)),
    ('ULPI_NXT', 'In2.Cu', (74.1, 17.7), (74.5, 19.25)),
    # CK arrival + jog + column bow section
    ('ULPI_CK', 'F.Cu', (75.125, 5.875), (75.25, 5.162)),
    ('ULPI_CK', 'In2.Cu', (74.625, 6.375), (74.875, 6.125)),
    ('ULPI_CK', 'In2.Cu', (74.875, 6.125), (75.125, 5.875)),
    ('ULPI_CK', 'In2.Cu', (74.625, 6.375), (74.625, 9.4)),
    ('ULPI_CK', 'In2.Cu', (74.625, 9.4), (74.32, 10.2)),
    ('ULPI_CK', 'In2.Cu', (74.32, 10.2), (74.625, 11.0)),
    ('ULPI_CK', 'In2.Cu', (74.625, 11.0), (74.625, 13.5)),
    # RBIAS via F feed
    ('RBIAS', 'F.Cu', (74.0, 11.562), (73.875, 11.625)),
    # ULPI_D0 F staircase (re-laid flat-south to open the arrival)
    ('ULPI_D0', 'F.Cu', (74.125, 5.875), (74.375, 6.125)),
    ('ULPI_D0', 'F.Cu', (74.375, 6.125), (74.625, 6.375)),
    ('ULPI_D0', 'F.Cu', (74.625, 6.375), (74.875, 6.625)),
    ('ULPI_D0', 'F.Cu', (74.875, 6.625), (75.375, 6.625)),
    ('ULPI_D0', 'F.Cu', (75.375, 6.625), (75.625, 6.875)),
    ('ULPI_D0', 'F.Cu', (75.625, 6.875), (75.875, 7.125)),
    # BIST window (bh3)
    ('BIST_DRV', 'In2.Cu', (73.875, 6.125), (74.125, 5.875)),
    ('BIST_DRV', 'In2.Cu', (74.125, 5.875), (74.375, 5.625)),
    ('BIST_DRV', 'In2.Cu', (74.375, 5.625), (74.625, 5.375)),
    ('BIST_DRV', 'In2.Cu', (74.625, 5.375), (74.875, 5.125)),
    ('BIST_DRV', 'In2.Cu', (74.875, 5.125), (75.375, 5.125)),
    # SPI_MOSI window
    ('SPI_MOSI', 'In2.Cu', (71.9, 7.25), (73.4, 5.2)),
    ('SPI_MOSI', 'In2.Cu', (73.4, 5.2), (75.1, 4.55)),
    ('SPI_MOSI', 'In2.Cu', (75.1, 4.55), (76.4, 3.35)),
    # I2C_SCL B corner
    ('I2C_SCL', 'B.Cu', (74.125, 5.875), (74.375, 6.125)),
    ('I2C_SCL', 'B.Cu', (74.375, 6.125), (74.625, 6.375)),
    ('I2C_SCL', 'B.Cu', (74.625, 6.375), (74.875, 6.625)),
    ('I2C_SCL', 'B.Cu', (74.875, 6.625), (75.125, 6.875)),
]
RIP_VIAS = [
    ('ULPI_CK', (75.125, 5.875)),
    ('RBIAS', (73.875, 11.625)),
    ('ULPI_DIR', (74.84, 18.07)),
    ('ULPI_NXT', (74.94, 17.36)),
]

# RBIAS In2 column in the shift window: generated from the board itself
# (bk's rule), so the densified micro-segs are all caught.
_items0 = G.load_items(SRC)
for _it in _items0:
    _it.layer = {'F': 'F.Cu', 'In2': 'In2.Cu', 'B': 'B.Cu'}.get(_it.layer, _it.layer)


def _in_win(p):
    return 73.7 <= p[0] <= 74.2 and 11.4 <= p[1] <= 16.7


RBIAS_COL = [it for it in _items0 if it.net == 'RBIAS' and it.kind == 'trk'
             and it.layer == 'In2.Cu' and _in_win(it.a) and _in_win(it.b)]
RBIAS_BND = [it for it in _items0 if it.net == 'RBIAS' and it.kind == 'trk'
             and it.layer == 'In2.Cu' and _in_win(it.a) != _in_win(it.b)]
for _it in RBIAS_COL + RBIAS_BND:
    RIP_SEGS.append(('RBIAS', 'In2.Cu',
                     (round(_it.a[0], 3), round(_it.a[1], 3)),
                     (round(_it.b[0], 3), round(_it.b[1], 3))))

NEW_TRK = [  # (net, layer, a, b, width)
    # DM re-lay west (return leg bowed south, clear of DIR's kept via area)
    ('DM_PHY', 'F.Cu', (73.562, 17.0), (73.1, 17.12), 0.25),
    ('DM_PHY', 'F.Cu', (73.1, 17.12), (72.7, 17.6), 0.25),
    ('DM_PHY', 'F.Cu', (72.7, 17.6), (72.7, 18.5), 0.25),
    ('DM_PHY', 'F.Cu', (72.7, 18.5), (73.42, 18.95), 0.25),
    ('DM_PHY', 'F.Cu', (73.42, 18.95), (73.625, 19.125), 0.25),
    # DIR re-fan: F stub to via (74.75,18.65); B head rejoins kept seg at (73.3,18.42)
    ('ULPI_DIR', 'F.Cu', (76.5, 16.875), (76.05, 17.85), 0.2),
    ('ULPI_DIR', 'F.Cu', (76.05, 17.85), (75.28, 18.08), 0.2),
    ('ULPI_DIR', 'F.Cu', (75.28, 18.08), (74.88, 18.58), 0.2),
    ('ULPI_DIR', 'F.Cu', (74.88, 18.58), (74.75, 18.65), 0.2),
    ('ULPI_DIR', 'B.Cu', (74.75, 18.65), (73.3, 18.42), 0.2),
    # NXT re-fan: F stub to via (74.5,17.95); In2 head threads between the
    # DIR via and DM's d0.6 via, rejoins its kept seg at (74.5,19.25)
    ('ULPI_NXT', 'F.Cu', (76.0, 16.875), (75.8, 17.3), 0.2),
    ('ULPI_NXT', 'F.Cu', (75.8, 17.3), (75.55, 17.55), 0.2),
    ('ULPI_NXT', 'F.Cu', (75.55, 17.55), (74.7, 17.65), 0.2),
    ('ULPI_NXT', 'F.Cu', (74.7, 17.65), (74.5, 17.95), 0.2),
    ('ULPI_NXT', 'In2.Cu', (74.5, 17.95), (74.05, 18.55), 0.2),
    ('ULPI_NXT', 'In2.Cu', (74.05, 18.55), (74.25, 19.0), 0.2),
    ('ULPI_NXT', 'In2.Cu', (74.25, 19.0), (74.5, 19.25), 0.2),
    # RST F stub + dive via (74.55,17.05) — grid family, solo margin +0.44
    ('USB_RST', 'F.Cu', (75.0, 16.875), (74.55, 17.05), 0.2),
    # RST In2 journey: dive -> channel -> via pass east of RBIAS via,
    # west of the CK east-bow -> jog pass -> arrival diagonal
    ('USB_RST', 'In2.Cu', (74.55, 17.05), (74.12, 16.9), 0.2),
    ('USB_RST', 'In2.Cu', (74.12, 16.9), (74.22, 15.0), 0.2),
    ('USB_RST', 'In2.Cu', (74.22, 15.0), (74.16, 12.0), 0.2),
    ('USB_RST', 'In2.Cu', (74.16, 12.0), (74.28, 11.5), 0.2),
    ('USB_RST', 'In2.Cu', (74.28, 11.5), (73.96, 10.58), 0.2),
    ('USB_RST', 'In2.Cu', (73.96, 10.58), (73.9, 10.0), 0.2),
    ('USB_RST', 'In2.Cu', (73.9, 10.0), (74.14, 9.0), 0.2),
    ('USB_RST', 'In2.Cu', (74.14, 9.0), (74.14, 7.05), 0.2),
    ('USB_RST', 'In2.Cu', (74.14, 7.05), (74.72, 6.02), 0.2),
    # RST F hop into U6.40 (pad rect y<=5.4)
    ('USB_RST', 'F.Cu', (74.72, 6.02), (74.74, 5.5), 0.2),
    ('USB_RST', 'F.Cu', (74.74, 5.5), (74.75, 5.35), 0.2),
    # CK jog shallower + east bow at the RBIAS-via latitude + column re-adds
    ('ULPI_CK', 'In2.Cu', (74.625, 9.4), (74.38, 10.28), 0.25),
    ('ULPI_CK', 'In2.Cu', (74.38, 10.28), (74.625, 11.0), 0.25),
    ('ULPI_CK', 'In2.Cu', (74.625, 11.0), (74.88, 11.85), 0.25),
    ('ULPI_CK', 'In2.Cu', (74.88, 11.85), (74.625, 13.5), 0.25),
    ('ULPI_CK', 'In2.Cu', (74.625, 7.35), (74.625, 9.4), 0.25),
    ('ULPI_CK', 'In2.Cu', (75.48, 5.92), (75.2, 6.8), 0.25),
    ('ULPI_CK', 'In2.Cu', (75.2, 6.8), (74.75, 7.05), 0.25),
    ('ULPI_CK', 'In2.Cu', (74.75, 7.05), (74.625, 7.35), 0.25),
    ('ULPI_CK', 'F.Cu', (75.25, 5.162), (75.33, 5.62), 0.2),
    ('ULPI_CK', 'F.Cu', (75.33, 5.62), (75.48, 5.92), 0.2),
    # RBIAS re-place: F stub + In2 connector (column adds appended below)
    ('RBIAS', 'F.Cu', (74.0, 11.562), (73.7, 11.55), 0.2),
    ('RBIAS', 'In2.Cu', (73.7, 11.55), (73.575, 11.625), 0.25),
    # D0 re-lay (flat at y6.85-6.9 across the +3V3D pad, dives east of it)
    ('ULPI_D0', 'F.Cu', (74.125, 5.875), (74.14, 6.29), 0.25),
    ('ULPI_D0', 'F.Cu', (74.14, 6.29), (74.6, 6.75), 0.25),
    ('ULPI_D0', 'F.Cu', (74.6, 6.75), (75.2, 6.9), 0.25),
    ('ULPI_D0', 'F.Cu', (75.2, 6.9), (75.875, 7.125), 0.25),
    # SCL re-add: corner bowed south, clear of the RST surf via
    ('I2C_SCL', 'B.Cu', (74.125, 5.875), (74.2, 6.78), 0.25),
    ('I2C_SCL', 'B.Cu', (74.2, 6.78), (74.95, 7.0), 0.25),
    ('I2C_SCL', 'B.Cu', (74.95, 7.0), (75.125, 6.875), 0.25),
    # BIST re-add (bh3, joints +0.012 north)
    ('BIST_DRV', 'In2.Cu', (73.875, 6.125), (74.05, 5.8), 0.25),
    ('BIST_DRV', 'In2.Cu', (74.05, 5.8), (74.3, 5.5), 0.25),
    ('BIST_DRV', 'In2.Cu', (74.3, 5.5), (74.62, 5.32), 0.25),
    ('BIST_DRV', 'In2.Cu', (74.62, 5.32), (74.95, 5.1), 0.25),
    ('BIST_DRV', 'In2.Cu', (74.95, 5.1), (75.375, 5.08), 0.25),
    ('BIST_DRV', 'In2.Cu', (75.375, 5.08), (75.375, 5.125), 0.25),
    # MOSI re-add (bh3)
    ('SPI_MOSI', 'In2.Cu', (71.9, 7.25), (73.4, 5.186), 0.2),
    ('SPI_MOSI', 'In2.Cu', (73.4, 5.186), (75.1, 4.536), 0.2),
    ('SPI_MOSI', 'In2.Cu', (75.1, 4.536), (76.4, 3.35), 0.2),
]
# RBIAS column shifted -0.30 + boundary connectors (bk machinery)
for _it in RBIAS_COL:
    NEW_TRK.append(('RBIAS', 'In2.Cu',
                    (round(_it.a[0] - 0.30, 3), round(_it.a[1], 3)),
                    (round(_it.b[0] - 0.30, 3), round(_it.b[1], 3)),
                    _it.hw * 2))
for _it in RBIAS_BND:
    _inside, _outside = (_it.a, _it.b) if _in_win(_it.a) else (_it.b, _it.a)
    NEW_TRK.append(('RBIAS', 'In2.Cu',
                    (round(_inside[0] - 0.30, 3), round(_inside[1], 3)),
                    (round(_outside[0], 3), round(_outside[1], 3)),
                    _it.hw * 2))

NEW_VIA = [  # (net, centre) — all d0.5/drill 0.3 (board minimum)
    ('USB_RST', (74.55, 17.05)),
    ('USB_RST', (74.72, 6.02)),
    ('ULPI_CK', (75.48, 5.92)),
    ('RBIAS', (73.7, 11.55)),
    ('ULPI_DIR', (74.75, 18.65)),
    ('ULPI_NXT', (74.5, 17.95)),
]



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
    pool = [it for it in items if not is_victim(it)]
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
    nets = sorted({nn for nn, *_ in RIP_SEGS} | {nn for nn, *_ in NEW_TRK}
                  | {nn for nn, _ in NEW_VIA} | {nn for nn, _ in RIP_VIAS})
    s = BL.Surgery(SRC, DST, nets=nets)
    layb = {'F.Cu': BL.F, 'In2.Cu': BL.IN2, 'B.Cu': BL.B}
    victims = []
    for nn, ll, a, b in RIP_SEGS:
        # densified nets can carry coincident duplicate tracks (the gate
        # pool prices the geometry once); count first, rip them all.
        def _m(t, a=a, b=b):
            p0, q0 = s.ends(t)
            return (s._near(p0, a) and s._near(q0, b)) or \
                   (s._near(p0, b) and s._near(q0, a))
        probe = s.find_tracks(nn, layb[ll], _m)
        assert len(probe) >= 1, f'rip seg {nn} {ll} {a}->{b}: 0 found'
        victims += s.find_seg(nn, layb[ll], a, b, expect=len(probe))
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

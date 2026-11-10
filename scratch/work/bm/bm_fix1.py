#!/usr/bin/env python3
"""bm fix1: north cluster re-fan on exp261 -> exp262.
NXT F approach, DIR F+B, STP F+B (straighten B jog), CK F+via+In2
(around GND via 77.25,18.38), +3V3A north F rip/re-tie, D7 via west.
All new geometry exact-gated (DRC classes) vs unripped items first."""
import sys
sys.path.insert(0, 'hw')
sys.path.insert(0, 'scratch/work/bm')
import gridroute as G
import bm_gate as BG
import build_lib as BL

SRC, DST = 'hw/pdlvds_rx.exp261.kicad_pcb', 'hw/pdlvds_rx.exp262.kicad_pcb'
items = G.load_items(SRC)


def inb(p, box):
    return box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3]


# ---- rip predicates (mirror on item model for gating) ----
def ripped(it):
    if it.kind == 'trk':
        a, b = it.a, it.b
        if it.net == 'ULPI_NXT' and it.layer == 'F' and inb(a, (74.8, 16.3, 76.2, 17.6)) and inb(b, (74.8, 16.3, 76.2, 17.6)):
            return True
        if it.net == 'ULPI_DIR' and it.layer in ('F', 'B') and inb(a, (73.0, 16.3, 76.7, 18.6)) and inb(b, (73.0, 16.3, 76.7, 18.6)):
            return True
        if it.net == 'ULPI_STP' and it.layer == 'F' and inb(a, (75.9, 16.3, 77.2, 18.3)) and inb(b, (75.9, 16.3, 77.2, 18.3)):
            return True
        if it.net == 'ULPI_STP' and it.layer == 'B' and inb(a, (75.9, 12.8, 76.95, 18.2)) and inb(b, (75.9, 12.8, 76.95, 18.2)):
            return True
        if it.net == 'ULPI_CK' and it.layer == 'F' and inb(a, (76.4, 16.3, 77.9, 19.1)) and inb(b, (76.4, 16.3, 77.9, 19.1)):
            return True
        if it.net == 'ULPI_CK' and it.layer == 'In2' and (
                (inb(a, (76.65, 16.3, 77.9, 19.1)) and inb(b, (76.65, 16.3, 77.9, 19.1)))
                or (abs(a[0] - 76.9) < 0.03 and abs(a[1] - 18.75) < 0.03 and abs(b[0] - 76.62) < 0.03 and abs(b[1] - 18.3) < 0.03)
                or (abs(b[0] - 76.9) < 0.03 and abs(b[1] - 18.75) < 0.03 and abs(a[0] - 76.62) < 0.03 and abs(a[1] - 18.3) < 0.03)):
            return True
        if it.net == '+3V3A' and it.layer == 'F' and inb(a, (78.0, 16.2, 79.5, 16.9)) and inb(b, (78.0, 16.2, 79.5, 16.9)):
            return True
    if it.kind == 'via':
        if it.net == 'ULPI_DIR' and BG.pt_seg(it.a, (74.82, 18.1), (74.82, 18.1)) == 0:
            return True
        if it.net == 'ULPI_STP' and abs(it.a[0] - 76.065) < 0.03 and abs(it.a[1] - 17.96) < 0.03:
            return True
        if it.net == 'ULPI_CK' and abs(it.a[0] - 77.05) < 0.03 and abs(it.a[1] - 17.85) < 0.03:
            return True
        if it.net == 'GND' and abs(it.a[0] - 77.25) < 0.03 and abs(it.a[1] - 18.38) < 0.03:
            return True
    return False


pool = [it for it in items if not ripped(it)
        and not (it.kind == 'pad' and it.net == '' and it.layer != 'F')]

NEW_TRK = [  # (net, layer, pts)
    ('ULPI_NXT', 'F', [(76.0, 16.438), (75.98, 17.05), (75.45, 17.32), (74.94, 17.36)]),
    ('ULPI_DIR', 'F', [(76.5, 16.438), (76.5, 17.30), (76.15, 17.42), (75.35, 17.85), (74.84, 18.07)]),
    ('ULPI_DIR', 'B', [(74.84, 18.07), (73.3, 18.42)]),
    ('ULPI_STP', 'F', [(77.0, 16.438), (76.92, 17.0), (76.92, 17.90), (76.065, 17.96)]),
    ('ULPI_STP', 'B', [(76.065, 17.96), (76.1, 16.0), (76.35, 14.6), (76.425, 12.9)]),
    ('ULPI_CK', 'F', [(77.5, 16.438), (77.45, 17.30), (77.4, 17.85)]),
    ('ULPI_CK', 'In2', [(77.4, 17.85), (77.5, 18.40), (77.05, 18.80), (76.7, 18.85), (76.62, 18.30)]),
    ('+3V3A', 'F', [(78.5, 16.438), (78.625, 16.75)]),
]
NEW_VIA = [('ULPI_DIR', (74.84, 18.07)), ('ULPI_STP', (76.065, 17.96)),
           ('ULPI_CK', (77.4, 17.85)), ('GND', (78.0, 18.3))]

ok = True
for net, layer, pts in NEW_TRK:
    for a, b in zip(pts, pts[1:]):
        neg = BG.report(f'{net} {layer} {a}->{b}', BG.margin_trk(a, b, layer, net, pool), 2)
        ok = ok and not neg
for net, c in NEW_VIA:
    neg = BG.report(f'via {net} {c}', BG.margin_via(c, net, pool), 2)
    ok = ok and not neg
# new-vs-new (same session geometry must not self-conflict across nets)
for i, (n1, l1, p1) in enumerate(NEW_TRK):
    for n2, l2, p2 in NEW_TRK:
        if n1 == n2:
            continue
        for a, b in zip(p1, p1[1:]):
            fake = [G.Item(n2, 'trk', layer=l2, a=x, b=y, hw=0.10) for x, y in zip(p2, p2[1:])]
            neg = [m for m in BG.margin_trk(a, b, l1, n1, fake) if m[0] < 0]
            if neg:
                print('NEW-NEW conflict', n1, a, b, 'vs', n2, neg[:1])
                ok = False
if not ok:
    print('GATE FAILED — not building')
    sys.exit(1)
print('gate clean; building')

NETS = ('ULPI_NXT', 'ULPI_DIR', 'ULPI_STP', 'ULPI_CK', '+3V3A', 'GND')
S = BL.Surgery(SRC, DST, nets=NETS)


def rip_where(net, layer, box, expect_min=1):
    def pred(t):
        s, e = S.ends(t)
        return inb(s, box) and inb(e, box)
    vs = S.find_where(net, layer, pred, expect=-1, label=f'{net} {layer} in {box}') \
        if False else None
    return vs


# predicate rips via find_tracks + manual count print
def rip_pred(net, layer, box):
    nc = S.NC[net]
    lay = {'F': BL.F, 'In2': BL.IN2, 'B': BL.B}[layer]
    vs = [t for t in S.b.GetTracks() if t.GetNetCode() == nc
          and t.Type() == pcbnew_type_track() and t.GetLayer() == lay
          and inb(S.ends(t)[0], box) and inb(S.ends(t)[1], box)]
    print(f'rip {net} {layer} {box}: {len(vs)}')
    assert vs, f'no victims {net} {layer}'
    S.remove(vs)


def pcbnew_type_track():
    import pcbnew
    return pcbnew.PCB_TRACE_T


def find_box(net, layer, box):
    lay = {'F': BL.F, 'In2': BL.IN2, 'B': BL.B}[layer]
    vs = S.find_tracks(net, lay, lambda t: inb(S.ends(t)[0], box) and inb(S.ends(t)[1], box))
    print(f'find {net} {layer} {box}: {len(vs)}')
    assert vs, f'no victims {net} {layer}'
    return vs


ALLV = []
ALLV += find_box('ULPI_NXT', 'F', (74.8, 16.3, 76.2, 17.6))
ALLV += find_box('ULPI_DIR', 'F', (73.0, 16.3, 76.7, 18.6))
ALLV += find_box('ULPI_DIR', 'B', (73.0, 16.3, 76.7, 18.6))
ALLV += find_box('ULPI_STP', 'F', (75.9, 16.3, 77.2, 18.3))
ALLV += find_box('ULPI_STP', 'B', (75.9, 12.8, 76.95, 18.2))
ALLV += find_box('ULPI_CK', 'F', (76.4, 16.3, 77.9, 19.1))
ALLV += S.find_seg('ULPI_CK', BL.IN2, (77.05, 17.85), (77.35, 18.35))
ALLV += S.find_seg('ULPI_CK', BL.IN2, (77.35, 18.35), (76.9, 18.75))
ALLV += S.find_seg('ULPI_CK', BL.IN2, (76.9, 18.75), (76.62, 18.3))
ALLV += find_box('+3V3A', 'F', (78.0, 16.2, 79.5, 16.9))
ALLV += S.find_via('ULPI_DIR', (74.82, 18.1))
ALLV += S.find_via('ULPI_STP', (76.065, 17.96))
ALLV += S.find_via('ULPI_CK', (77.05, 17.85))
ALLV += S.find_via('GND', (77.25, 18.38))
S.remove(ALLV)

LAY = {'F': BL.F, 'In2': BL.IN2, 'B': BL.B}
for net, layer, pts in NEW_TRK:
    S.add_polyline(net, LAY[layer], pts, 0.20)
for net, (x, y) in NEW_VIA:
    if net == 'GND':
        S.add_via(net, x, y, dia=0.6, drill=0.3)
    else:
        S.add_via(net, x, y)
S.finish()

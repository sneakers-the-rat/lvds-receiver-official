"""t_ap8: probe what kills DM A7 via candidates in the ap7 pools
(CC1 re-lay + VBUS rejoin + CC2 re-plan adds present). Self-contained
replication of ap7's rip set and stage adds up to the DM scan."""
import sys, math, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
from t_ai_lib import (load_items, pt_margin, seg_margin, in_box_pool,
                      apply_rip, fmt_it)
from router import netclass

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp233.kicad_pcb')
items = load_items(b)
A7 = (30.250, 71.480)
VB_A = (30.125, 71.125)
VB_B = (30.625, 70.625)
BIGBOX = (26.0, 48.0, 42.0, 76.0)

def seg(net, li, a, c, w):
    return (li, ('seg', net, (a[0], a[1], c[0], c[1], w / 2),
                 netclass(net)[1]))
def via(net, x, y, d):
    return ('via', net, (x, y, d / 2), netclass(net)[1])

RIPS = [('via', 'DM_CON', 29.875, 70.375),
        ('seg', 'DM_CON', 29.875, 70.375),
        ('seg', 'DM_CON', 30.250, 70.980),
        ('seg', 'DM_CON', 29.625, 70.625),
        ('seg', 'DM_CON', 30.125, 70.125),
        ('seg', 'DM_CON', 30.125, 69.875),
        ('via', 'CC2', 30.375, 72.375),
        ('seg', 'CC2', 30.500, 72.930),
        ('seg', 'CC2', 30.375, 72.375),
        ('seg', 'CC2', 30.375, 71.625),
        ('seg', 'CC2', 30.375, 70.875),
        ('seg', 'CC2', 30.625, 70.625),
        ('seg', 'CC2', 30.625, 70.125),
        ('seg', 'CC2', 30.875, 69.875),
        ('seg', 'CC2', 31.125, 69.625),
        ('seg', 'CC1', 29.250, 69.980),
        ('seg', 'CC1', 29.875, 69.625),
        ('seg', 'CC1', 30.125, 69.375),
        ('seg', 'CC1', 30.125, 68.875),
        ('seg', 'CC1', 30.375, 68.625),
        ('seg', 'CC1', 30.625, 68.375),
        ('seg', 'CC1', 30.875, 68.125),
        ('seg', 'CC1', 30.925, 67.500),
        ('seg', 'VBUS_RAW', 30.375, 70.875),
        ('seg', 'VBUS_RAW', 30.625, 70.625)]
statics, nrip = apply_rip(items, RIPS)
print(f'rips: {nrip}')
# list what was actually ripped for CC1/VBUS (collateral check)
# (apply_rip already applied; re-derive from a fresh load for the report)
items2 = load_items(b)
gone = []
for li in range(3):
    s0 = set()
    for it in items2[li]:
        s0.add(fmt_it(it))
    s1 = set(fmt_it(it) for it in statics[li])
    for x in s0 - s1:
        if any(n in x for n in ('CC1', 'VBUS', 'DM_CON', 'CC2')):
            gone.append(x)
print('ripped items (district nets):')
for g in sorted(gone):
    print('   ', g)

def build_pool(adds):
    it2 = {li: list(statics[li]) for li in range(3)}
    for a in adds:
        if isinstance(a[0], int):
            it2[a[0]].append(a[1])
        else:
            for li in range(3):
                it2[li].append(a)
    return in_box_pool(it2, BIGBOX, pad=1.2)

vb_adds = [seg('VBUS_RAW', 1, VB_A, (30.3, 70.75), 0.2),
           seg('VBUS_RAW', 1, (30.3, 70.75), VB_B, 0.2)]
cc1_poly = [(29.250, 69.980), (29.250, 69.600), (30.300, 69.600),
            (30.925, 67.250)]
cc1_adds = [seg('CC1', 0, a, c, 0.2)
            for a, c in zip(cc1_poly, cc1_poly[1:])]
cc2_adds = [via('CC2', 30.125, 72.375, 0.5)]

for label, adds in [('statics only', []),
                    ('+vb', vb_adds),
                    ('+vb+cc1', vb_adds + cc1_adds),
                    ('+vb+cc1+cc2via', vb_adds + cc1_adds + cc2_adds)]:
    pool = build_pool(adds)
    m0, w0 = pt_margin(0, 29.85, 70.40, 'DM_CON', 0.25, pool[0])
    m1, w1 = pt_margin(1, 29.85, 70.40, 'DM_CON', 0.25, pool[1])
    m2, w2 = pt_margin(2, 29.85, 70.40, 'DM_CON', 0.25, pool[2])
    ms, ws = seg_margin(0, A7, (29.85, 70.40), 'DM_CON', 0.10, pool[0])
    print(f'{label}: DMvia(29.85,70.40) F {m0:+.3f} [{fmt_it(w0)}] '
          f'In2 {m1:+.3f} [{fmt_it(w1)}] B {m2:+.3f} [{fmt_it(w2)}] '
          f'stub {ms:+.3f} [{fmt_it(ws)}]')

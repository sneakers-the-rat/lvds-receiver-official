import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp249.kicad_pcb')
# minimal edits: C16 pads only (GND start), C47 goal is stock
c16_old = [it for it in pool[0] if it[0] == 'pad'
           and abs(it[2][1] - 9.75) < 0.01
           and it[2][0] in (75.225, 76.775)]
rip_items(c16_old)
add_items({0: [('pad', '+3V3D', (71.025, 13.0, 0.450, 0.475, 0.0), 0.2),
               ('pad', 'GND', (69.475, 13.0, 0.450, 0.475, 0.0), 0.2)]})
Bpts = [(75.7375, 10.75), (75.3, 11.35), (74.9, 11.75), (74.2, 12.25),
        (73.5, 12.55), (73.3, 12.2), (73.22, 11.94), (72.92, 11.62),
        (72.35, 11.65), (71.9, 11.95), (71.3, 12.1), (70.7, 11.85),
        (70.3, 12.15), (70.2, 12.5), (70.18, 12.75)]
bj = {0: [], 1: [], 2: []}
for a, bpt in zip(Bpts, Bpts[1:]):
    bj[2].append(('seg', 'PHY_1V8A', (a[0], a[1], bpt[0], bpt[1], 0.10),
                  0.2))
add_items(bj)
for label, use_hole, use_phy in (('no blockers', 0, 0),
                                 ('hole only', 1, 0),
                                 ('phy only', 0, 1),
                                 ('both', 1, 1)):
    added = []
    if use_hole:
        blk = {l: [('via', 'ZZB', (70.925, 9.975, 0.35), 0.2)]
               for l in range(3)}
        add_items(blk)
        added += [it for l in range(3) for it in blk[l]]
    if use_phy:
        pb = {0: [], 1: [], 2: []}
        for a, bpt in (((72.92, 11.62), (72.35, 11.65)),
                       ((72.35, 11.65), (71.9, 11.95))):
            pb[2].append(('seg', 'ZZB', (a[0], a[1], bpt[0], bpt[1], 0.30),
                          0.2))
        add_items(pb)
        added += [it for l in range(3) for it in pb[l]]
    astar = make_astar((67.0, 74.0, 9.0, 15.0), 0.05)
    J = astar('GND', ((0,), 69.475, 13.0), (0, 71.775, 11.0), hw=0.10)
    print(label, ':', 'FOUND vias=' + str(J['vias']) if J else 'NONE',
          flush=True)
    if added:
        rip_items(added)

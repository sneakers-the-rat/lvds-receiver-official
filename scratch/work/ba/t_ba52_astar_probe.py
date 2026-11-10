"""t_ba52: A* start/goal probes for XI on exp253 pool
(excursion ripped in model):
A: B (75.6,16.0)->(75.6,13.0) mid-corridor, no arc.
B: B arc via (75.625,18.625)->(75.6,16.0).
C: F C20.1 pad (75.72,18.73)->B (75.6,13.0) multilayer.
D: B (75.625,18.625)->(75.625,17.0) short hop south.
E: dump pool items (all nets) within 1.2mm of the arc via
on B and F."""
import sys
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa

pool = load_board_pool('hw/pdlvds_rx.exp253.kicad_pcb')
rip = [it for it in pool[2]
       if it[1] == 'ULPI_STP' and it[0] == 'seg'
       and 74.3 <= C(it)[0] <= 76.0 and 13.4 <= C(it)[1] <= 17.2]
rip_items(rip)

print('--- items within 1.2mm of (75.625,18.625) ---')
for l in (2, 0):
    for it in pool[l]:
        cc = C(it)
        if abs(cc[0] - 75.625) <= 1.2 and abs(cc[1] - 18.625) <= 1.2:
            d = it[2]
            print(f"  L{l} {it[0]} {it[1]} centre "
                  f"({cc[0]:.2f},{cc[1]:.2f}) {d}")

astar = make_astar((70.0, 80.0, 6.0, 22.0), 0.05)
tests = {
    'A mid-corridor': ('XI', ((2,), 75.6, 16.0), (2, 75.6, 13.0)),
    'B arc->16.0': ('XI', ((2,), 75.625, 18.625), (2, 75.6, 16.0)),
    'C Fpad->B13': ('XI', ((0, 2), 75.72, 18.73), (2, 75.6, 13.0)),
    'D arc->17.0': ('XI', ((2,), 75.625, 18.625), (2, 75.625, 17.0)),
}
for label, (net, st, go) in tests.items():
    rr = astar(net, st, go, 0.10)
    print(label, ':', 'FOUND vias=' + str(rr['vias']) if rr else 'NONE')
print('=== done ===')

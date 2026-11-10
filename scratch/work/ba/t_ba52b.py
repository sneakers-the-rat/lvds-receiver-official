import sys
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
pool = load_board_pool('hw/pdlvds_rx.exp253.kicad_pcb')
rip = [it for it in pool[2]
       if it[1] == 'ULPI_STP' and it[0] == 'seg'
       and 74.3 <= C(it)[0] <= 76.0 and 13.4 <= C(it)[1] <= 17.2]
rip_items(rip)
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

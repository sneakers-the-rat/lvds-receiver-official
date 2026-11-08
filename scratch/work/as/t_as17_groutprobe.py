"""t_as17: interrogate groute's item model (repair.build_items) around
U6.35 CAP_DATA: print edge distance + required clearance for every foreign
item near the west-apron cells, F layer, on exp241prep."""
import sys
sys.path.insert(0, 'hw')
import pcbnew
import repair
from router import netclass, dist_to_item

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp241prep.kicad_pcb')
items, _pc = repair.build_items(board)

def pair_clr(net, other):
    return max(netclass(net)[1], netclass(other)[1] if other else 0.2)

for (x, y) in [(70.5, 2.25), (70.375, 2.25), (70.25, 2.25), (70.125, 2.0),
               (70.25, 2.0), (70.375, 2.125)]:
    print(f'cell ({x},{y}):')
    for it in items[0].near(0, x, y):
        if it[1] == 'CAP_DATA':
            continue
        d = dist_to_item(it, x, y)
        req_trk = 0.1 + pair_clr('CAP_DATA', it[1]) + 0.004
        req_via = 0.25 + pair_clr('CAP_DATA', it[1]) + 0.004
        flag = ''
        if d < req_trk:
            flag = ' BLOCKS-TRACK'
        if d < req_via:
            flag += ' BLOCKS-VIA'
        if flag:
            print(f'   {it[0]} {it[1]} geom={it[2]} dist {d:.3f} '
                  f'req_trk {req_trk:.3f} req_via {req_via:.3f}{flag}')

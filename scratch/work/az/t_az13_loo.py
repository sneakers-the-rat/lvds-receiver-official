"""t_az13: leave-one-out restoration on the X-H mega-rip for XI, and
mega-rip bisection for USB_RST.
XI: rip pocket+column boxes (non-XI segs/vias), then restore one
net's items at a time; if XI breaks, that net binds (in context).
RST: mega-rip south column box, then north+south, then LOO by net.
"""
import sys
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa

BOARD = 'hw/pdlvds_rx.exp251.kicad_pcb'


def ctr_in(x0, x1, y0, y1):
    def f(it):
        p = C(it)
        return x0 <= p[0] <= x1 and y0 <= p[1] <= y1
    return f


def probe(net, box, start, goals, hw=0.10, quiet=False):
    astar = make_astar(box, 0.125)
    res = []
    for (gl, gx, gy) in goals:
        r = astar(net, start, (gl, gx, gy), hw)
        res.append(bool(r))
        if r and not quiet:
            print(f'      -> L{gl} ({gx},{gy}) FOUND vias={r["vias"]}')
    return any(res)


XI_BOX = (70.0, 88.0, 8.0, 23.0)
XI_START = ((0,), 76.25, 11.562)
XI_GOALS = [(2, 75.625, 18.625), (0, 75.72, 18.73), (2, 78.375, 21.125)]
POCKET = ctr_in(75.3, 77.1, 10.0, 12.3)
COLUMN = ctr_in(75.6, 76.6, 12.3, 18.3)


def xi_rip(pool, restore_net=None):
    its = []
    for l in range(3):
        for it in pool[l]:
            if it[1] == 'XI' or it[0] == 'pad':
                continue
            if it[1] == restore_net:
                continue
            if POCKET(it) or COLUMN(it):
                its.append(it)
    rip_items(its)
    return len(its)


pool0 = load_board_pool(BOARD)
nets_in_boxes = sorted({it[1] for l in range(3) for it in pool0[l]
                        if it[0] != 'pad' and (POCKET(it) or COLUMN(it))
                        and it[1] != 'XI'})
print('nets with segs/vias in XI boxes:', nets_in_boxes)
print('== XI baseline X-H (all ripped):')
pool = load_board_pool(BOARD)
xi_rip(pool)
print('   found:', probe('XI', XI_BOX, XI_START, XI_GOALS))
for net in nets_in_boxes:
    pool = load_board_pool(BOARD)
    xi_rip(pool, restore_net=net)
    ok = probe('XI', XI_BOX, XI_START, XI_GOALS, quiet=True)
    print(f'== XI restore {net}: found={ok}')

# ---------------- RST ----------------
RST_BOX = (68.0, 84.0, 0.0, 20.0)
RST_START = ((0,), 74.25, 16.4375)
RST_GOALS = [(0, 74.75, 4.662), (2, 74.75, 4.662), (1, 74.75, 4.662)]
SOUTH = ctr_in(72.5, 77.0, 3.0, 15.0)
NORTH = ctr_in(73.0, 77.0, 15.0, 20.5)


def rst_rip(pool, boxes, restore_net=None):
    its = []
    for l in range(3):
        for it in pool[l]:
            if it[1] == 'USB_RST' or it[0] == 'pad':
                continue
            if it[1] == restore_net:
                continue
            if any(b(it) for b in boxes):
                its.append(it)
    rip_items(its)
    return len(its)


print('== RST mega-rip SOUTH box only:')
pool = load_board_pool(BOARD)
rst_rip(pool, [SOUTH])
print('   found:', probe('USB_RST', RST_BOX, RST_START, RST_GOALS))
print('== RST mega-rip SOUTH+NORTH boxes:')
pool = load_board_pool(BOARD)
rst_rip(pool, [SOUTH, NORTH])
print('   found:', probe('USB_RST', RST_BOX, RST_START, RST_GOALS))
pool0 = load_board_pool(BOARD)
nets_s = sorted({it[1] for l in range(3) for it in pool0[l]
                 if it[0] != 'pad' and (SOUTH(it) or NORTH(it))
                 and it[1] != 'USB_RST'})
print('nets in RST boxes:', nets_s)
for net in nets_s:
    pool = load_board_pool(BOARD)
    rst_rip(pool, [SOUTH, NORTH], restore_net=net)
    ok = probe('USB_RST', RST_BOX, RST_START, RST_GOALS, quiet=True)
    print(f'== RST restore {net}: found={ok}')
print('=== done ===')

"""t_az6: ablation A* probes on faithful exp251 pool. For each named
fence set: reload pool, rip the fence items, re-run the net's probes.
FOUND => that fence set (jointly) binds; then the re-lay design work
targets exactly those fences.
"""
import sys
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa

BOARD = 'hw/pdlvds_rx.exp251.kicad_pcb'


def Ctr(it):
    return C(it)


def rip_pred(pool, pred, label):
    its = []
    for l in range(3):
        for it in pool[l]:
            if pred(l, it):
                its.append(it)
    # dedupe (vias appear on all layers as separate entries)
    n = rip_items(its)
    print(f'    ripped {label}: {len(its)} entries, {n} removals')
    return its


def in_box(x0, x1, y0, y1):
    def f(p):
        return x0 <= p[0] <= x1 and y0 <= p[1] <= y1
    return f


def probe(net, box, start, goals, hw=0.10):
    astar = make_astar(box, 0.125)
    out = []
    for (gl, gx, gy) in goals:
        r = astar(net, start, (gl, gx, gy), hw)
        out.append('FOUND' if r else 'none')
        if r:
            print(f'    {net} -> L{gl} ({gx},{gy}): FOUND vias={r["vias"]}')
    print(f'    {net}: {out}')


XI_BOX = (70.0, 88.0, 8.0, 23.0)
XI_START = ((0,), 76.25, 11.562)
XI_GOALS = [(2, 75.625, 18.625), (0, 75.72, 18.73), (2, 78.375, 21.125)]
PHY_BOX = (68.0, 82.0, 6.0, 22.0)
PHY_START = ((0,), 72.02, 18.0)
PHY_GOALS = [(2, 77.8, 16.2), (0, 77.25, 16.4375), (2, 76.95, 13.0)]
RST_BOX = (68.0, 84.0, 0.0, 20.0)
RST_START = ((0,), 74.25, 16.4375)
RST_GOALS = [(0, 74.75, 4.662), (2, 74.75, 4.662), (1, 74.75, 4.662)]


def run(tag, net, box, start, goals, rips):
    print(f'== {tag}')
    pool = load_board_pool(BOARD)
    for pred, label in rips:
        rip_pred(pool, pred, label)
    probe(net, box, start, goals)


def net_is(name):
    return lambda l, it: it[1] == name


def box_ctr(x0, x1, y0, y1):
    b = in_box(x0, x1, y0, y1)
    return lambda l, it: b(Ctr(it))


def layer_is(L):
    return lambda l, it: l == L


def both(p, q):
    return lambda l, it: p(l, it) and q(l, it)


# ---------- XI ablations ----------
run('X-A: -STP pocket (x75.4-77,y9.8-14)', 'XI', XI_BOX, XI_START, XI_GOALS,
    [(both(net_is('ULPI_STP'), box_ctr(75.4, 77.0, 9.8, 14.0)), 'STP pocket')])
run('X-B: -notch via', 'XI', XI_BOX, XI_START, XI_GOALS,
    [(lambda l, it: it[1] == 'PHY_1V8A' and it[0] == 'via'
      and abs(it[2][0] - 75.7375) < 0.01 and abs(it[2][1] - 10.75) < 0.01,
      'notch via')])
run('X-C: -STP pocket -notch via', 'XI', XI_BOX, XI_START, XI_GOALS,
    [(both(net_is('ULPI_STP'), box_ctr(75.4, 77.0, 9.8, 14.0)), 'STP pocket'),
     (lambda l, it: it[1] == 'PHY_1V8A' and it[0] == 'via'
      and abs(it[2][0] - 75.7375) < 0.01 and abs(it[2][1] - 10.75) < 0.01,
      'notch via')])
run('X-D: -+3V3A In2 web (x76.2-78.2,y9.8-14)', 'XI', XI_BOX, XI_START,
    XI_GOALS,
    [(both(both(net_is('+3V3A'), layer_is(1)), box_ctr(76.2, 78.2, 9.8, 14.0)),
      '+3V3A In2')])
run('X-E: X-C + -+3V3A In2 web', 'XI', XI_BOX, XI_START, XI_GOALS,
    [(both(net_is('ULPI_STP'), box_ctr(75.4, 77.0, 9.8, 14.0)), 'STP pocket'),
     (lambda l, it: it[1] == 'PHY_1V8A' and it[0] == 'via'
      and abs(it[2][0] - 75.7375) < 0.01 and abs(it[2][1] - 10.75) < 0.01,
      'notch via'),
     (both(both(net_is('+3V3A'), layer_is(1)), box_ctr(76.2, 78.2, 9.8, 14.0)),
      '+3V3A In2')])
run('X-F: -XO F escape (x76.2-77,y10.3-11.7)', 'XI', XI_BOX, XI_START,
    XI_GOALS,
    [(both(both(net_is('XO'), layer_is(0)), box_ctr(76.2, 77.0, 10.3, 11.7)),
      'XO F esc')])
run('X-G: X-C + -XO F escape', 'XI', XI_BOX, XI_START, XI_GOALS,
    [(both(net_is('ULPI_STP'), box_ctr(75.4, 77.0, 9.8, 14.0)), 'STP pocket'),
     (lambda l, it: it[1] == 'PHY_1V8A' and it[0] == 'via'
      and abs(it[2][0] - 75.7375) < 0.01 and abs(it[2][1] - 10.75) < 0.01,
      'notch via'),
     (both(both(net_is('XO'), layer_is(0)), box_ctr(76.2, 77.0, 10.3, 11.7)),
      'XO F esc')])

# ---------- PHY ablations ----------
run('P-A: -STP B column (x75.7-76.6,y10-18.3)', 'PHY_1V8', PHY_BOX,
    PHY_START, PHY_GOALS,
    [(both(both(net_is('ULPI_STP'), layer_is(2)),
           box_ctr(75.7, 76.6, 10.0, 18.3)), 'STP B col')])
run('P-B: -+3V3A B diagonals (x70.5-76.6,y8-12.6)', 'PHY_1V8', PHY_BOX,
    PHY_START, PHY_GOALS,
    [(both(both(net_is('+3V3A'), layer_is(2)),
           box_ctr(70.5, 76.6, 8.0, 12.6)), '+3V3A B')])
run('P-C: -+3V3A In2 web (x76.2-78.6,y10-16.6)', 'PHY_1V8', PHY_BOX,
    PHY_START, PHY_GOALS,
    [(both(both(net_is('+3V3A'), layer_is(1)),
           box_ctr(76.2, 78.6, 10.0, 16.6)), '+3V3A In2')])
run('P-D: P-A + P-C', 'PHY_1V8', PHY_BOX, PHY_START, PHY_GOALS,
    [(both(both(net_is('ULPI_STP'), layer_is(2)),
           box_ctr(75.7, 76.6, 10.0, 18.3)), 'STP B col'),
     (both(both(net_is('+3V3A'), layer_is(1)),
           box_ctr(76.2, 78.6, 10.0, 16.6)), '+3V3A In2')])
run('P-E: P-A + P-B', 'PHY_1V8', PHY_BOX, PHY_START, PHY_GOALS,
    [(both(both(net_is('ULPI_STP'), layer_is(2)),
           box_ctr(75.7, 76.6, 10.0, 18.3)), 'STP B col'),
     (both(both(net_is('+3V3A'), layer_is(2)),
           box_ctr(70.5, 76.6, 8.0, 12.6)), '+3V3A B')])

# ---------- RST ablations ----------
run('R-A: -DM_PHY F loop', 'USB_RST', RST_BOX, RST_START, RST_GOALS,
    [(both(both(net_is('DM_PHY'), layer_is(0)), box_ctr(73.2, 74.6, 15.2, 19.6)),
      'DM F loop'),
     (lambda l, it: it[1] == 'DM_PHY' and it[0] == 'via'
      and abs(it[2][0] - 73.625) < 0.01 and abs(it[2][1] - 19.125) < 0.01,
      'DM via')])
run('R-B: R-A + -DP_PHY F stub/via', 'USB_RST', RST_BOX, RST_START, RST_GOALS,
    [(both(both(net_is('DM_PHY'), layer_is(0)), box_ctr(73.2, 74.6, 15.2, 19.6)),
      'DM F loop'),
     (lambda l, it: it[1] == 'DM_PHY' and it[0] == 'via'
      and abs(it[2][0] - 73.625) < 0.01 and abs(it[2][1] - 19.125) < 0.01,
      'DM via'),
     (lambda l, it: it[1] == 'DP_PHY' and it[0] == 'via'
      and abs(it[2][0] - 72.125) < 0.01 and abs(it[2][1] - 15.875) < 0.01,
      'DP via'),
     (both(both(net_is('DP_PHY'), layer_is(0)), box_ctr(71.8, 73.8, 15.2, 16.2)),
      'DP F stub')])
run('R-C: -ULPI_CK In2 vertical (x74.3-74.95,y6-13.6)', 'USB_RST', RST_BOX,
    RST_START, RST_GOALS,
    [(both(both(net_is('ULPI_CK'), layer_is(1)),
           box_ctr(74.3, 74.95, 6.0, 13.6)), 'CK In2 vert')])
run('R-D: R-A + R-C', 'USB_RST', RST_BOX, RST_START, RST_GOALS,
    [(both(both(net_is('DM_PHY'), layer_is(0)), box_ctr(73.2, 74.6, 15.2, 19.6)),
      'DM F loop'),
     (lambda l, it: it[1] == 'DM_PHY' and it[0] == 'via'
      and abs(it[2][0] - 73.625) < 0.01 and abs(it[2][1] - 19.125) < 0.01,
      'DM via'),
     (both(both(net_is('ULPI_CK'), layer_is(1)),
           box_ctr(74.3, 74.95, 6.0, 13.6)), 'CK In2 vert')])
run('R-E: -XO F south run (x71.8-76,y9.2-10)', 'USB_RST', RST_BOX, RST_START,
    RST_GOALS,
    [(both(both(net_is('XO'), layer_is(0)), box_ctr(71.8, 76.0, 9.2, 10.0)),
      'XO F run')])
print('=== done ===')

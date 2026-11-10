"""t_az12: name the binding items at key points on the S6 pool and on
the faithful pool: per layer, the foreign item minimizing
(df - clr) for XI at each query point.
"""
import sys, math
sys.path.insert(0, 'scratch/work/ax')
sys.path.insert(0, 'scratch/work/ai')
from t_ax0_pre import *  # noqa
import t_ai_lib as L
sys.path.insert(0, 'scratch/work/az')
import importlib.util
spec = importlib.util.spec_from_file_location(
    'az10', 'scratch/work/az/t_az10_astar_scen.py')


# load az10's apply_scen without running its probe loop: read source
# up to the XI_BOX marker and exec only the defs
src = open('scratch/work/az/t_az10_astar_scen.py').read()
head = src.split('XI_BOX')[0]
g = {'__name__': 'az10defs'}
exec(head, g)
apply_scen = g['apply_scen']

BOARD = 'hw/pdlvds_rx.exp251.kicad_pcb'


def df_pt(it, x, y):
    if it[0] == 'pad':
        cx, cy, hw, hh, rot = it[2]
        if rot:
            c, s = math.cos(rot), math.sin(rot)
            dxl = (x - cx) * c + (y - cy) * s
            dyl = -(x - cx) * s + (y - cy) * c
            return math.hypot(max(abs(dxl) - hw, 0.0),
                              max(abs(dyl) - hh, 0.0))
        return math.hypot(max(abs(x - cx) - hw, 0.0),
                          max(abs(y - cy) - hh, 0.0))
    if it[0] == 'via':
        return math.hypot(x - it[2][0], y - it[2][1]) - it[2][2]
    x1, y1, x2, y2, hw = it[2]
    vx, vy = x2 - x1, y2 - y1
    L2 = vx * vx + vy * vy
    if L2 == 0:
        return math.hypot(x - x1, y - y1) - hw
    t = min(1.0, max(0.0, ((x - x1) * vx + (y - y1) * vy) / L2))
    return math.hypot(x - (x1 + t * vx), y - (y1 + t * vy)) - hw


def report(pool, label, pts):
    print(f'##### {label}')
    for (x, y) in pts:
        line = [f'({x},{y}):']
        for l, ln in enumerate(('F', 'In2', 'B')):
            best = (9.9, None)
            for it in pool[l]:
                if it[1] == 'XI':
                    continue
                a = C(it)
                if abs(a[0] - x) > 2.5 or abs(a[1] - y) > 2.5:
                    continue
                v = df_pt(it, x, y) - max(0.2, it[3])
                if v < best[0]:
                    best = (v, it)
            line.append(f'{ln} {best[0]:+.3f} [{L.fmt_it(best[1])}]')
        print('  ' + ' | '.join(line))


PTS = [(76.25, 11.25), (76.25, 11.0), (76.25, 10.75), (76.3, 10.5),
       (76.28, 10.8), (76.4, 10.6), (76.0, 10.625), (76.2, 10.55),
       (77.5, 9.3), (76.6, 8.6)]
pool = load_board_pool(BOARD)
report(pool, 'faithful', PTS)
pool = load_board_pool(BOARD)
apply_scen(pool, 'S6')
report(pool, 'S6', PTS)
print('=== done ===')

import wx
_app = wx.App(False)
import sys
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'av16'}
src = open('scratch/work/au/t_au97_phase2y.py').read()
exec(src.split("# 1. RBIAS tail re-lay")[0], g)
make_astar = g['make_astar']

def web_relay(net, new_xy, old_xy):
    a = make_astar((min(new_xy[0], old_xy[0]) - 1.5,
                    max(new_xy[0], old_xy[0]) + 1.5,
                    min(new_xy[1], old_xy[1]) - 1.5,
                    max(new_xy[1], old_xy[1]) + 1.5), step=0.025)
    for gl in (0, 2, 1):
        J = a(net, ((0, 1, 2), new_xy[0], new_xy[1]),
              (gl, old_xy[0], old_xy[1]), 0.10)
        if J is not None:
            return J, gl
    return None, None

J, gl = web_relay('+3V3A', (69.725, 19.5), (69.225, 19.5))
print(f'goal layer {gl}: vias={J["vias"]}', flush=True)
for r in J['runs']:
    pts = r['pts']
    print(f'  L{r["layer"]} {tuple(pts[0])} -> {tuple(pts[-1])} ({len(pts)} pts)', flush=True)
print('done', flush=True)

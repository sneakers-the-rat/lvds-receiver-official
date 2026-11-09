import wx
_app = wx.App(False)
import sys, json, pickle, math
sys.path.insert(0, 'scratch/work/au')
import numpy as np
g = {'__name__': 'aw36'}
src = open('scratch/work/au/t_au97_phase2y.py').read()
exec(src.split("# 1. RBIAS tail re-lay")[0], g)
st = pickle.load(open('scratch/work/aw/state_aw.pkl', 'rb'))
_ns = {id(g): g}
for _fn in (g['fragments'], g['item_margin'], g['make_astar'],
            g['try_emit'], g['journey_items_dense']):
    _ns[id(_fn.__globals__)] = _fn.__globals__
for _d in _ns.values():
    _d['pool'] = st['pool']; _d['NEW'] = st['NEW']
    _d['JOURNEYS'] = st['JOURNEYS']; _d['NET_HW'] = st['NET_HW']
pool = st['pool']
import t_ai_lib as L
from router import dist_to_item, netclass
net = 'I2C_SCL'
myclr = netclass(net)[1]
def margin_at(l, px, py):
    worst = (9e9, None)
    for it in pool[l]:
        if it[1] == net:
            continue
        req = max(myclr, it[3])
        d = dist_to_item(it, px, py) - req
        if d < worst[0]:
            worst = (d, it)
    return worst
for (px, py) in [(67.0, 5.5), (67.5, 5.0), (66.5, 5.5), (68.0, 5.5),
                 (66.875, 5.9), (67.0, 6.2)]:
    print(f'point ({px},{py}):', flush=True)
    for l in range(3):
        d, it = margin_at(l, px, py)
        print(f'   L{l}: {d:+.3f} vs {L.fmt_it(it)}', flush=True)

import sys, math
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import thread_far as tf
from hand_stub import build_items
from bridge import groups_of
TM = pcbnew.ToMM

def ctr(s):
    bb = s.BBox()
    return (TM(bb.GetLeft() + bb.GetWidth() / 2),
            TM(bb.GetTop() + bb.GetHeight() / 2))

def facing(s, oc):
    bb = s.BBox()
    return (min(max(oc[0], TM(bb.GetLeft())), TM(bb.GetRight())),
            min(max(oc[1], TM(bb.GetTop())), TM(bb.GetBottom())))

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp14.kicad_pcb')
items = build_items(board)
for net in ('HV_GATE', 'HV_SS', '+5V'):
    gs = groups_of(items, net)
    print(f'== {net}: {len(gs)} groups')
    if len(gs) < 2:
        continue
    best = (9.9, None, None)
    for i1 in range(len(gs)):
        for i2 in range(i1 + 1, len(gs)):
            for a in gs[i1]:
                for b in gs[i2]:
                    v = tf.gapf(a[3], a[2], b[3], b[2])
                    if v is not None and v < best[0]:
                        best = (v, a, b)
    gap, a, b = best
    if a is None:
        print('   no pair within gate')
        continue
    print(f'   nearest pair gap {gap:.2f}: {a[4]} ({a[1]}) <-> {b[4]} ({b[1]})')
    w_net, _ = tf.netclass(net)
    w = max(0.2, min(w_net, 0.3))
    for (src, dst, p, tag) in (
            (a, b, facing(a[3], ctr(b[3])), 'start A'),
            (b, a, facing(b[3], ctr(a[3])), 'goal  B')):
        shared = [l for l in tf.LAYERS if l in src[2] and l in dst[2]] or [pcbnew.F_Cu]
        sx = [math.floor(p[0] / tf.STEP) * tf.STEP,
              math.ceil(p[0] / tf.STEP) * tf.STEP]
        sy = [math.floor(p[1] / tf.STEP) * tf.STEP,
              math.ceil(p[1] / tf.STEP) * tf.STEP]
        print(f'   {tag}: anchor {src[4]} net {src[1]} facing ({p[0]:.3f}, {p[1]:.3f})')
        for nx in sorted(set(sx)):
            for ny in sorted(set(sy)):
                for layer in shared:
                    bl = tf.blockers(items, net,
                                     tf.segm(p[0], p[1], nx, ny, w), layer)
                    ln = {pcbnew.F_Cu: 'F', pcbnew.In2_Cu: 'In2', pcbnew.B_Cu: 'B'}[layer]
                    if not bl:
                        print(f'     ({nx:.1f},{ny:.1f}) {ln}: CLEAR')
                    else:
                        desc = [(items[k][0], items[k][1],
                                 'RIP' if tf.rippable(items, [k]) else 'WALL')
                                for k in bl]
                        print(f'     ({nx:.1f},{ny:.1f}) {ln}: {desc}')

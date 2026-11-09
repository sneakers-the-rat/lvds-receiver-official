"""t_av1: census of the two open joins in the au97 model state.
Rebuilds the model exactly as t_au97_phase2y does from au93
(without au97's geometric changes), then dumps:
- all RBIAS items board-wide (to identify the 17-seg In2 staircase,
  its end vias and F parts)
- XO items + fragments in the knot box
- arr_clk journey geometry (tail dive (70.1,21.8), F run y21.9)
- the +3V3D decap fragment items (pad (72.725,20.5))
- full census of box x[66,78] y[9,26] per layer (fences for both joins)
"""
import wx
_app = wx.App(False)
import sys, json
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'av1'}
src = open('scratch/work/au/t_au97_phase2y.py').read()
head = src.split("# 1. RBIAS tail re-lay")[0]
exec(head, g)
pool = g['pool']
C = g['C']
item_margin = g['item_margin']
fragments = g['fragments']
import t_ai_lib as L

LAY = {0: 'F', 1: 'In2', 2: 'B'}


def dump_items(net, box=None, layers=(0, 1, 2)):
    out = []
    for l in layers:
        for it in pool[l]:
            if it[1] != net:
                continue
            if box:
                cx, cy = C(it)
                if not (box[0] - 1 < cx < box[1] + 1
                        and box[2] - 1 < cy < box[3] + 1):
                    continue
            out.append((l, it))
    out.sort(key=lambda t: (t[0], C(t[1])[1], C(t[1])[0]))
    return out


print('=== RBIAS all items (board-wide) ===', flush=True)
for l, it in dump_items('RBIAS'):
    print(f'  L{l}({LAY[l]}) {L.fmt_it(it)}', flush=True)

print('=== XO items in knot box x[64,78] y[14,24] ===', flush=True)
for l, it in dump_items('XO', (64, 78, 14, 24)):
    print(f'  L{l}({LAY[l]}) {L.fmt_it(it)}', flush=True)
fr = fragments('XO', (60.0, 90.0, 4.0, 33.0))
print(f'XO fragments (wide box): {len(fr)}', flush=True)
for i, f in enumerate(fr):
    print(f'  frag {i}: {len(f["items"])} items, terms={f["terms"]}',
          flush=True)
    for (l, it) in sorted(f['items'],
                          key=lambda t: (t[0], C(t[1])[1], C(t[1])[0])):
        cx, cy = C(it)
        if 60 < cx < 80 and 8 < cy < 28:
            print(f'    L{l} {L.fmt_it(it)}', flush=True)

B = json.load(open('scratch/work/au/build_au93.json'))
print('=== arr_clk journey (au93 manifest) ===', flush=True)
print(json.dumps(B['journeys']['arr_clk']), flush=True)
print('=== arr_data journey ===', flush=True)
print(json.dumps(B['journeys']['arr_data']), flush=True)
print('=== journeys in au93 manifest ===', flush=True)
print(sorted(B['journeys'].keys()), flush=True)
print('=== rip2 nets/counts (au93) ===', flush=True)
for net, lst in B['rip2'].items():
    print(f'  {net}: {len(lst)}', flush=True)

print('=== +3V3D items near decap fragment x[69,77] y[18,26] ===',
      flush=True)
for l, it in dump_items('+3V3D', (69, 77, 18, 26)):
    print(f'  L{l}({LAY[l]}) {L.fmt_it(it)}', flush=True)
fr3 = fragments('+3V3D', (50.0, 86.0, -2.0, 32.0))
print(f'+3V3D fragments (wide): {len(fr3)}', flush=True)
for i, f in enumerate(fr3):
    print(f'  frag {i}: {len(f["items"])} items, terms={f["terms"]}',
          flush=True)
    for (l, it) in sorted(f['items'],
                          key=lambda t: (t[0], C(t[1])[1], C(t[1])[0])):
        cx, cy = C(it)
        if 66 < cx < 78 and 16 < cy < 26:
            print(f'    L{l} {L.fmt_it(it)}', flush=True)
print('=== PHY_1V8A all items ===', flush=True)
for l, it in dump_items('PHY_1V8A'):
    print(f'  L{l}({LAY[l]}) {L.fmt_it(it)}', flush=True)
print('=== GND pads in knot box x[69,72] y[18,22] ===', flush=True)
for l, it in dump_items('GND', (69, 72, 18, 22), layers=(0,)):
    print(f'  L{l} {L.fmt_it(it)}', flush=True)

print('=== box census x[66,78] y[9,26]: item counts per layer/net ===',
      flush=True)
from collections import Counter
for l in range(3):
    cnt = Counter()
    for it in pool[l]:
        cx, cy = C(it)
        if 66 < cx < 78 and 9 < cy < 26:
            cnt[it[1]] += 1
    print(f'  L{l}({LAY[l]}): {dict(cnt)}', flush=True)
print('done', flush=True)

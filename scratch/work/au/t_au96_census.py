"""t_au96: census for build + handovers. Rebuild from au93.
1. Manifest journeys: vias + runs summary (clk9 vs arr_clk,
   data_tail vs arr_data overlap check).
2. Pads x[74,78] y[17,28] (U5 W column + X1 area).
3. RBIAS items in (66,74,14,24).
4. Pads near the +3V3D stub pad (72.725,20.5)."""
import wx
_app = wx.App(False)
import sys, json, math
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'cen'}
src71 = open('scratch/work/au/t_au71_phase2b.py').read()
exec(src71.split("NEW = {")[0], g)
pool = g['pool']
C = g['C']
import t_ai_lib as L

B = json.load(open('scratch/work/au/build_au93.json'))
print('=== manifest journeys (build_au93) ===', flush=True)
for name, J in B['journeys'].items():
    runs = '; '.join(
        f"L{r['layer']}[{r['pts'][0]}..{r['pts'][-1]} n{len(r['pts'])}]"
        for r in J['runs'])
    print(f'{name}: vias={J["vias"]} runs: {runs}', flush=True)
print('=== extra ===', B['extra'], flush=True)
print('=== rip2 counts ===',
      {k: len(v) for k, v in B['rip2'].items()}, flush=True)
print('=== pads x[74,78] y[17,28] (esc pool) ===', flush=True)
seen = set()
for l in range(3):
    for it in pool[l]:
        if it[0] != 'pad':
            continue
        cx, cy = C(it)
        if 74 < cx < 78 and 17 < cy < 28 and (it[1], cx, cy) not in seen:
            seen.add((it[1], cx, cy))
            print(f'   {L.fmt_it(it)}', flush=True)
print('=== RBIAS items (66,74,14,24) ===', flush=True)
for l in range(3):
    for it in pool[l]:
        if it[1] != 'RBIAS':
            continue
        cx, cy = C(it)
        if 66 < cx < 74 and 14 < cy < 24:
            print(f'   L{l} {L.fmt_it(it)}', flush=True)
print('=== pads near (72.725,20.5) r3 ===', flush=True)
seen = set()
for l in range(3):
    for it in pool[l]:
        if it[0] != 'pad':
            continue
        cx, cy = C(it)
        if math.hypot(cx - 72.725, cy - 20.5) < 3.0 \
                and (it[1], cx, cy) not in seen:
            seen.add((it[1], cx, cy))
            print(f'   {L.fmt_it(it)}', flush=True)
print('done', flush=True)

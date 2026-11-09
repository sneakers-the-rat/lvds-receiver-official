"""t_av2: compact journey summaries from the au93-state model +
esc-native arrival copper + fence dumps for both joins."""
import wx
_app = wx.App(False)
import sys, json
sys.path.insert(0, 'scratch/work/au')
g = {'__name__': 'av2'}
src = open('scratch/work/au/t_au97_phase2y.py').read()
exec(src.split("# 1. RBIAS tail re-lay")[0], g)
pool = g['pool']
C = g['C']
import t_ai_lib as L

# items_full from the esc board, via the au71 head directly
g2 = {'__name__': 'av2b'}
src71 = open('scratch/work/au/t_au71_phase2b.py').read()
exec(src71.split("NEW = {")[0], g2)
items_full = g2['items_full']

print('=== journey summaries (au93 manifest, as loaded) ===', flush=True)
for name, J in sorted(g['JOURNEYS'].items()):
    runs = [(r['layer'], tuple(r['pts'][0]), tuple(r['pts'][-1]),
             len(r['pts'])) for r in J['runs']]
    print(f'{name}: vias={J["vias"]}', flush=True)
    for r in runs:
        print(f'    L{r[0]} {r[1]} -> {r[2]} ({r[3]} pts)', flush=True)

print('=== esc-native CAP_CLK items x[68,78] y[18,27] ===', flush=True)
for l in range(3):
    for it in items_full[l]:
        if it[1] != 'CAP_CLK':
            continue
        cx, cy = C(it)
        if 68 < cx < 78 and 18 < cy < 27:
            print(f'  L{l} {L.fmt_it(it)}', flush=True)
print('=== esc-native CAP_DATA items x[68,78] y[17,24] ===', flush=True)
for l in range(3):
    for it in items_full[l]:
        if it[1] != 'CAP_DATA':
            continue
        cx, cy = C(it)
        if 68 < cx < 78 and 17 < cy < 24:
            print(f'  L{l} {L.fmt_it(it)}', flush=True)

print('=== model-pool ULPI_NXT + REFCLK In2 items x[68,75] y[19,24] ===',
      flush=True)
for it in pool[1]:
    if it[1] not in ('ULPI_NXT', 'REFCLK'):
        continue
    cx, cy = C(it)
    if 68 < cx < 75 and 19 < cy < 24:
        print(f'  L1 {L.fmt_it(it)}', flush=True)

print('=== model-pool B items x[69.25,74.5] y[12,21.5] (RBIAS ride box) ===',
      flush=True)
for it in pool[2]:
    cx, cy = C(it)
    if 69.25 < cx < 74.5 and 12 < cy < 21.5:
        print(f'  L2 {L.fmt_it(it)}', flush=True)
print('=== model-pool F items x[73,74.6] y[12,14.5] (dive-via box) ===',
      flush=True)
for it in pool[0]:
    cx, cy = C(it)
    if 73 < cx < 74.6 and 12 < cy < 14.5:
        print(f'  L0 {L.fmt_it(it)}', flush=True)
print('=== model-pool In2 items x[73,74.6] y[12,14.5] ===', flush=True)
for it in pool[1]:
    cx, cy = C(it)
    if 73 < cx < 74.6 and 12 < cy < 14.5:
        print(f'  L1 {L.fmt_it(it)}', flush=True)
print('done', flush=True)

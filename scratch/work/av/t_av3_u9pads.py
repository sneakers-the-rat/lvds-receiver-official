"""t_av3: reproduce au71's U9PADS set and identify owning footprints."""
import wx
_app = wx.App(False)
import sys
sys.path.insert(0, 'scratch/work/au')
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
import pcbnew
import t_ai_lib as L

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
items_full = L.load_items(b)

# replicate the U9PADS collection from t_au71_phase2b.py lines ~44-55
src = open('scratch/work/au/t_au71_phase2b.py').read()
head = src.split('pool = {l:')[0]
print('--- au71 U9PADS collection source ---', flush=True)
i = head.index('U9PADS')
print(head[i - 600:], flush=True)

g = {'__name__': 'av3'}
exec(src.split("NEW = {")[0], g)
U9PADS = g['U9PADS']
print(f'--- U9PADS: {len(U9PADS)} items ---', flush=True)
for it in U9PADS:
    print(' ', L.fmt_it(it), flush=True)

print('--- footprints with pads in x[65,71] y[-0.5,6] ---', flush=True)
for fp in b.GetFootprints():
    hits = []
    for pad in fp.Pads():
        x, y = pcbnew.ToMM(pad.GetPosition())
        if 65 < x < 71 and -0.5 < y < 6:
            hits.append((pad.GetName(), pad.GetNetname(),
                         round(x, 3), round(y, 3)))
    if hits:
        fx, fy = pcbnew.ToMM(fp.GetPosition())
        print(f'{fp.GetReference()} at ({fx:.3f},{fy:.3f}):', flush=True)
        for h in sorted(hits):
            print(f'    pad {h[0]} {h[1]} ({h[2]},{h[3]})', flush=True)
print('done', flush=True)

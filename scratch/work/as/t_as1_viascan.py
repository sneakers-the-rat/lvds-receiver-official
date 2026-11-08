"""t_as1 v2: search SCK In2->B dive via + approach from saddle exit B.
Pool restricted via in_box_pool to the middle district (bounding-circle
inclusion, fixed version). Via gates on all 3 layers; approach = direct
seg or 1-bend on In2, scored by worst margin."""
import sys, wx, json
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
from t_ai_lib import load_items, pt_margin, seg_margin, apply_rip, in_box_pool

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp236.kicad_pcb')
items = load_items(board)
mods = json.load(open('scratch/work/ar/mods_v7.json'))
statics, nrip = apply_rip({l: list(items[l]) for l in range(3)},
                          [tuple(r) for r in mods['rips']])
BOX = (66.0, 79.0, -1.0, 10.5)
pool = in_box_pool(statics, BOX, pad=1.0)
pre = [(0,(71.425,6.75,70.1,6.78,0.1)), (0,(70.1,6.78,68.7,6.8,0.1)),
       (0,(68.7,6.8,67.8,8.1,0.1)),
       (1,(67.8,8.1,69.0,6.2,0.1)), (1,(69.0,6.2,69.45,5.45,0.1)),
       (1,(69.45,5.45,69.85,4.62,0.1)), (1,(69.85,4.62,70.294,4.204,0.1)),
       (1,(70.294,4.204,71.094,4.958,0.1))]
for l,g in pre: pool[l].append(('seg','SPI_SCK',g,0.2))
for l in range(3): pool[l].append(('via','SPI_SCK',(67.8,8.1,0.25),0.2))
print('pool sizes', {l: len(pool[l]) for l in range(3)}, flush=True)

B = (71.094,4.958)
results = []
x = 72.40
while x <= 76.001:
    y = 2.20
    while y <= 4.301:
        worst = 9
        for l in range(3):
            m,w = pt_margin(l, x, y, 'SPI_SCK', 0.25, pool[l])
            if m < worst: worst = m
        if worst >= 0.0: results.append((worst, round(x,3), round(y,3)))
        y += 0.025
    x += 0.025
results.sort(reverse=True)
print(f'{len(results)} via candidates margin>=0; top 12:', flush=True)
for r in results[:12]: print(f'  via ({r[1]},{r[2]}) worst {r[0]:+.3f}', flush=True)

def segm(ax,ay,bx,by,extra):
    return seg_margin(1,(ax,ay),(bx,by),'SPI_SCK',0.1,list(pool[1])+extra,step=0.05)[0]
for worst0,x,y in results[:8]:
    via_it = [('via','SPI_SCK',(x,y,0.25),0.2)]
    m_dir = segm(B[0],B[1],x,y,via_it)
    best = (min(worst0,m_dir), 'direct', None)
    bx = 71.3
    while bx <= 75.2:
        by = 3.0
        while by <= 5.3:
            m1 = segm(B[0],B[1],bx,by,via_it)
            if m1 > 0.0:
                m2 = segm(bx,by,x,y,via_it)
                sc = min(worst0,m1,m2)
                if sc > best[0]: best = (sc,'bend',(round(bx,2),round(by,2)))
            by += 0.15
        bx += 0.15
    print(f'via ({x},{y}) viamargin {worst0:+.3f} -> {best[1]} {best[2]} worst {best[0]:+.3f}', flush=True)

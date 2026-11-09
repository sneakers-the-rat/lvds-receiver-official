import wx
_app = wx.App(False)
import sys
sys.path.insert(0, 'scratch/work/au'); sys.path.insert(0, 'scratch/work/ai'); sys.path.insert(0, 'hw')
import pcbnew, t_ai_lib as L
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
items_full = L.load_items(b)
for net in ('CAP_DATA', 'CAP_CLK'):
    print(f'--- {net} F items x[68.5,72.5] y[1.0,4.0] ---', flush=True)
    for it in items_full[0]:
        if it[1] != net: continue
        cx, cy = L.item_centre(it) if hasattr(L, 'item_centre') else (None, None)
        d = it[2]
        if it[0] == 'seg':
            cx, cy = (d[0]+d[2])/2, (d[1]+d[3])/2
        else:
            cx, cy = d[0], d[1]
        if 68.5 < cx < 72.5 and 1.0 < cy < 4.0:
            print('  L0', L.fmt_it(it), flush=True)
    print(f'--- {net} vias all layers x[68.5,72.5] y[1.0,4.0] ---', flush=True)
    for it in items_full[1]:
        if it[1] == net and it[0] == 'via' and 68.5 < it[2][0] < 72.5 and 1.0 < it[2][1] < 4.0:
            print('  via', L.fmt_it(it), flush=True)
print('done', flush=True)

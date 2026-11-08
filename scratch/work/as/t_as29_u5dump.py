import wx
_app = wx.App(False)
import pcbnew, sys
sys.path.insert(0, 'scratch/work/ai')
import t_ai_lib as L
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
items = L.load_items(b)
def show(net):
    print(f"== {net}")
    for lay in (0, 1, 2):
        for it in items[lay]:
            if it[1] == net:
                print("  L%d" % lay, it)
for net in ('CDR_SQUELCH', 'CDR_DATP', 'CDR_DATN', 'CAP_CLK', 'CAP_DATA'):
    show(net)
print("== all items x[70.5,78] y[18.5,28.5]")
for lay in (0, 1, 2):
    for it in items[lay]:
        g = it[2]
        xs = [g[0], g[2]] if it[0] == 'seg' else [g[0]]
        ys = [g[1], g[3]] if it[0] == 'seg' else [g[1]]
        if all(70.5 <= x <= 78.0 for x in xs) and all(18.5 <= y <= 28.5 for y in ys):
            print("  L%d" % lay, it)

import wx
_app = wx.App(False)
import pcbnew, sys
sys.path.insert(0, 'scratch/work/ai')
import t_ai_lib as L
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
items = L.load_items(b)
for net in ('HV_SHDN', 'THR_DAC'):
    print(f"== {net} (all items)")
    for lay in (0, 1, 2):
        for it in items[lay]:
            if it[1] == net:
                print("  L%d" % lay, it)
print("== box x[64.5,72.5] y[-3.5,5.0] all nets")
for lay in (0, 1, 2):
    for it in items[lay]:
        g = it[2]
        if it[0] == 'seg':
            cx, cy = (g[0] + g[2]) / 2, (g[1] + g[3]) / 2
        else:
            cx, cy = g[0], g[1]
        if 64.5 <= cx <= 72.5 and -3.5 <= cy <= 5.0:
            print("  L%d" % lay, it)

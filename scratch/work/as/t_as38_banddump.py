import wx
_app = wx.App(False)
import pcbnew, sys
sys.path.insert(0, 'scratch/work/ai')
import t_ai_lib as L
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
items = L.load_items(b)
for lay in (0, 2):
    print(f"== layer {lay} box x[60.5,71] y[0.5,10.5]")
    for it in items[lay]:
        g = it[2]
        if it[0] == 'seg':
            pts = [(g[0], g[1]), (g[2], g[3])]
        else:
            pts = [(g[0], g[1])]
        if any(60.5 <= px <= 71 and 0.5 <= py <= 10.5 for px, py in pts):
            print("  ", it)

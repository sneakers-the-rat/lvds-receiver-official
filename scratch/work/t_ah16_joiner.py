import math, sys
sys.path.insert(0, 'hw')
import wx; _a=wx.App(False)
import pcbnew, repair
from router import netclass, dist_to_item
b = pcbnew.LoadBoard('scratch/work/ah/h9.kicad_pcb')
code = b.GetNetcodeFromNetname('+3V3A'); assert code >= 0
items, _ = repair.build_items(b)
A, C = (68.375, 17.5), (68.625, 17.5)
worst = (1e9, None, None)
for s in range(7):
    x = A[0] + (C[0]-A[0])*s/6; y = A[1]
    for it in items[2].near(2, x, y):
        if it[1] == '+3V3A': continue
        m = dist_to_item(it, x, y) - (0.1 + max(netclass('+3V3A')[1], netclass(it[1])[1]))
        if m < worst[0]: worst = (m, it, (round(x,3), round(y,3)))
print('joiner gate:', f"{worst[0]:+.3f}", 'vs', worst[1][1] if worst[1] else None, 'at', worst[2])
assert worst[0] >= 0
t = pcbnew.PCB_TRACK(b)
t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(A[0]), pcbnew.FromMM(A[1])))
t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(C[0]), pcbnew.FromMM(C[1])))
t.SetWidth(pcbnew.FromMM(0.2)); t.SetLayer(pcbnew.B_Cu); t.SetNetCode(code)
b.Add(t); b.Save('scratch/work/ah/h10.kicad_pcb'); print('saved h10')

import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import check_pcb
b = pcbnew.LoadBoard('hw/pdlvds_rx.expanded.kicad_pcb')
names = sorted({n.GetNetname() for n in b.GetNetInfo()})
hv = []
for n in names:
    if not n or n == 'GND':
        continue
    need = check_pcb.need_for(n, 'GND', {pcbnew.F_Cu})
    if need >= 0.99:
        hv.append((n, round(need, 2)))
print('nets needing >=1.0mm vs GND on F.Cu:', hv)

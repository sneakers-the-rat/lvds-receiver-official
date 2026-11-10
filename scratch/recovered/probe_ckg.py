import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import check_pcb
from hand_stub import build_items
from bridge import groups_of
check_pcb.SURFACE = {pcbnew.F_Cu, pcbnew.B_Cu}
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp101.kicad_pcb')
items = build_items(b)
groups = groups_of(items, 'ULPI_CK')
for gi, g in enumerate(groups):
    print(f'--- group {gi}: {len(g)} items ---')
    for kind, net, layers, shape, desc, ref in g:
        bb = shape.BBox()
        cx = pcbnew.ToMM((bb.GetLeft() + bb.GetRight()) // 2)
        cy = pcbnew.ToMM((bb.GetTop() + bb.GetBottom()) // 2)
        if 70 < cx < 86 and 14 < cy < 46:
            print('  ', kind, desc, f'@({cx:.2f},{cy:.2f})')

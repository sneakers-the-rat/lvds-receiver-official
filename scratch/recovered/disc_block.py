import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import check_pcb
from hand_stub import build_items
check_pcb.SURFACE = {pcbnew.F_Cu, pcbnew.B_Cu}
need_for = check_pcb.need_for
MM = pcbnew.FromMM
ALL = {pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu}
board = pcbnew.LoadBoard(sys.argv[1])
net = sys.argv[2]
items = build_items(board)
# args: x,y pairs
for a in sys.argv[3:]:
    x, y = [float(v) for v in a.split(',')]
    disc = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(x), MM(y)),
                                pcbnew.VECTOR2I(MM(x), MM(y)), MM(0.6))
    print(f"--- disc at ({x},{y}) for {net}:")
    hits = 0
    for kind, n2, l2, s2, desc in items:
        if n2 == net or kind == 'zone':
            continue
        shared = ALL & l2
        if not shared:
            continue
        need = need_for(net, n2, shared)
        if disc.Collide(s2, MM(need - 0.001 + 0.02)):
            bb = s2.BBox()
            print(f"    BLOCK {kind} {n2} {desc} layers={sorted(l2)} need={need} "
                  f"bbox=({pcbnew.ToMM(bb.GetX()):.2f},{pcbnew.ToMM(bb.GetY()):.2f}) "
                  f"{pcbnew.ToMM(bb.GetWidth()):.2f}x{pcbnew.ToMM(bb.GetHeight()):.2f}")
            hits += 1
    if not hits:
        print("    CLEAR")

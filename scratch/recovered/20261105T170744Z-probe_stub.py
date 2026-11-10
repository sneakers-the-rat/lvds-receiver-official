import sys, math
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import check_pcb
check_pcb.SURFACE = {pcbnew.F_Cu, pcbnew.B_Cu}
need_for = check_pcb.need_for
from hand_stub import build_items
MM = pcbnew.FromMM
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp82.kicad_pcb')
items = build_items(b)
net = 'SLICEN'
px, py, hx, hy = 52.562, -17.25, 0.44, 0.125
layers = {pcbnew.F_Cu}
for w in (0.2,):
    for ln in (0.5, 1.1, 2.0):
        for k in range(16):
            a = k * math.pi / 8
            ca, sa = math.cos(a), math.sin(a)
            ext = min(hx/abs(ca) if ca else 1e9, hy/abs(sa) if sa else 1e9)
            inset = min(0.08, 0.5*ext)
            sx, sy = px + (ext-inset)*ca, py + (ext-inset)*sa
            ex, ey = px + (ext+ln)*ca, py + (ext+ln)*sa
            seg = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(sx),MM(sy)), pcbnew.VECTOR2I(MM(ex),MM(ey)), MM(w))
            blockers = []
            for kind, n2, l2, s2, desc in items:
                if n2 == net or kind == 'zone': continue
                shared = layers & l2
                if not shared: continue
                need = need_for(net, n2, shared)
                if seg.Collide(s2, MM(need - 0.001)):
                    blockers.append((n2, desc, need))
            print(f"dir {k*22.5:6.1f} ln {ln}: blockers {blockers[:4]}")
        print()

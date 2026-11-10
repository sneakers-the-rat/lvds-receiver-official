import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.expanded.kicad_pcb')
bb = b.GetBoardEdgesBoundingBox()
print('edges bbox x:', pcbnew.ToMM(bb.GetX()), '..', pcbnew.ToMM(bb.GetRight()), ' y:', pcbnew.ToMM(bb.GetY()), '..', pcbnew.ToMM(bb.GetBottom()))
for i, z in enumerate(b.Zones()):
    zb = z.GetBoundingBox()
    print(f"zone{i} net={z.GetNetname()!r} layers={[pcbnew.LayerName(l) for l in z.GetLayerSet().Seq()]} bbox x {pcbnew.ToMM(zb.GetX()):.1f}..{pcbnew.ToMM(zb.GetRight()):.1f} y {pcbnew.ToMM(zb.GetY()):.1f}..{pcbnew.ToMM(zb.GetBottom()):.1f} clearance={pcbnew.ToMM(z.GetLocalClearance()):.2f} minwidth={pcbnew.ToMM(z.GetMinThickness()):.2f}")
# where are the moved clusters now?
for ref in ('U7','U4','U9','U10','U6','J1','J2','D1'):
    for fp in b.GetFootprints():
        if fp.GetReference() == ref:
            p = fp.GetPosition()
            print(ref, 'at', round(pcbnew.ToMM(p.x),1), round(pcbnew.ToMM(p.y),1))

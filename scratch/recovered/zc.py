import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard("hw/pdlvds_rx.exp82.kicad_pcb")
for z in b.Zones():
    ls = [l for l in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu) if z.IsOnLayer(l)]
    print(f"zone net={z.GetNetname()} firstlayer={z.GetLayer()} layers={ls} ownclr={pcbnew.ToMM(z.GetOwnClearance(ls[0])):.3f} priority={z.GetAssignedPriority()}")

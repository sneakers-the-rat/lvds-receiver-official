import wx
app = wx.App(False)
import pcbnew
MM = pcbnew.FromMM
board = pcbnew.BOARD(); board.SetCopperLayerCount(4)
ni = pcbnew.NETINFO_ITEM(board, "GND"); board.Add(ni)
fp = pcbnew.FootprintLoad("/usr/share/kicad/footprints/Resistor_SMD.pretty", "R_0603_1608Metric")
fp.SetReference("R1"); fp.SetPosition(pcbnew.VECTOR2I(MM(50), MM(40))); board.Add(fp)
for pad in fp.Pads(): pad.SetNet(ni)
z = pcbnew.ZONE(board); z.SetLayer(pcbnew.In1_Cu); z.SetNet(ni); z.SetNetCode(ni.GetNetCode())
out = z.Outline(); chain = pcbnew.SHAPE_LINE_CHAIN()
for (x, y) in [(0.3,0.3),(99.7,0.3),(99.7,79.7),(0.3,79.7)]: chain.Append(pcbnew.VECTOR2I(MM(x),MM(y)))
chain.SetClosed(True); out.AddOutline(chain)
board.Add(z)
print("before fill", flush=True)
filler = pcbnew.ZONE_FILLER(board); filler.Fill(board.Zones())
print("FILL OK under xvfb+wx", flush=True)
print("filled area polys:", z.GetFilledPolysList(pcbnew.In1_Cu).OutlineCount() if hasattr(z,'GetFilledPolysList') else 'n/a', flush=True)

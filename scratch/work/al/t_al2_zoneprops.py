import sys, wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
for z in b.Zones():
    if z.GetNetname() == 'GND':
        print('zone layer', z.GetLayerName() if hasattr(z,'GetLayerName') else z.GetFirstLayer(),
              'clearance', round(pcbnew.ToMM(z.GetLocalClearance()),3),
              'min_thickness', round(pcbnew.ToMM(z.GetMinThickness()),3),
              'pad_conn', z.GetPadConnection(), 'priority', z.GetAssignedPriority())

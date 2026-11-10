import wx
_app = wx.App(False)
import pcbnew, json
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp254.kicad_pcb')
try:
    pcbnew.FillZones(b)
except Exception:
    pass
out = []
err = pcbnew.WriteDRCReport(b, 'scratch/work/ba/drc254.json', out)
print('drc written', err)

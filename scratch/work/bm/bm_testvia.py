import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp266.kicad_pcb')
nc = b.GetNetcodeFromNetname('GND')
sites = [(77.2, 8.6)]
for x, y in sites:
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(pcbnew.VECTOR2I(int(x*1e6), int(y*1e6)))
    v.SetWidth(int(0.5e6)); v.SetDrill(int(0.3e6))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNetCode(nc)
    b.Add(v)
import build_lib as BL
zfill = pcbnew.ZONE_FILLER(b)
zfill.Fill(b.Zones())
b.Save('/tmp/testvia.kicad_pcb')
print('saved')

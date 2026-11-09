import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp241.kicad_pcb')
conn = b.GetConnectivity()
print([m for m in dir(conn) if 'onn' in m or 'lust' in m or 'ode' in m], flush=True)
zone = None
for z in b.Zones():
    if z.GetNetname() == 'GND' and z.IsOnLayer(pcbnew.F_Cu):
        zone = z
        break
try:
    items = conn.GetConnectedItems(zone, [pcbnew.PCB_TRACE_T, pcbnew.PCB_VIA_T, pcbnew.PCB_PAD_T])
    print('zone connected items:', len(items), flush=True)
except Exception as e:
    print('GetConnectedItems failed:', e, flush=True)

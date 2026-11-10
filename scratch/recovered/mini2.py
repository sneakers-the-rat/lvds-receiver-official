import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp211.kicad_pcb')
NETS = ('ULPI_CK', 'PHY_1V8', 'ULPI_NXT', 'ULPI_DIR', 'ULPI_STP', 'USB_RST')
CODE = {n: b.GetNetcodeFromNetname(n) for n in NETS}
print('codes', CODE)
print('tracks:', len(b.GetTracks()))

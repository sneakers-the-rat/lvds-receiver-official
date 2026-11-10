import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp211.kicad_pcb')
print('tracks direct:', len(b.GetTracks()))
c = b.GetNetcodeFromNetname('ULPI_CK')
print('code', c)
print('tracks after netcode:', len(b.GetTracks()))

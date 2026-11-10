import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp211.kicad_pcb')
def f1():
    return len(b.GetTracks())
print('f1:', f1())
def f2(net, lay, a, bb):
    n = 0
    for t in b.GetTracks():
        n += 1
    return n
print('f2:', f2('ULPI_CK', 'F', (0,0), (1,1)))

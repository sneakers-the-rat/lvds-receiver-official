import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp266.kicad_pcb')
b.BuildConnectivity()
conn = b.GetConnectivity()
try:
    unc = conn.GetUnconnectedItems()
    print('unconnected pairs:', len(unc))
    for a, bb in unc:
        for it in (a, bb):
            try:
                p = it.GetPosition()
                print(' ', type(it).__name__, it.GetNetname() if hasattr(it, 'GetNetname') else '',
                      p.x/1e6, p.y/1e6, it.GetLayer() if hasattr(it, 'GetLayer') else '')
            except Exception as e:
                print('  item err', e)
except Exception as e:
    print('GetUnconnectedItems failed:', e)
    print([m for m in dir(conn) if 'nconn' in m or 'tem' in m][:20])

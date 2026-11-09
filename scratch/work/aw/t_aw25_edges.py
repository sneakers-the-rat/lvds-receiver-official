import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp241.kicad_pcb')
conn = b.GetConnectivity()
nc = b.GetNetcodeFromNetname('GND')
print('GND unconnected count:', conn.GetUnconnectedCount(nc), flush=True)
edges = []
def cb(e):
    try:
        s = e.GetSourceNode(); t = e.GetTargetNode()
        sp = s.GetPoint() if hasattr(s, 'GetPoint') else s.GetPosition()
        tp = t.GetPoint() if hasattr(t, 'GetPoint') else t.GetPosition()
        edges.append(((pcbnew.ToMM(sp.x), pcbnew.ToMM(sp.y)),
                      (pcbnew.ToMM(tp.x), pcbnew.ToMM(tp.y))))
    except Exception as ex:
        edges.append(('ERR', str(ex)))
    return True
try:
    conn.RunOnUnconnectedEdges(cb)
    print('edges via callback:', len(edges), flush=True)
    for e in edges: print('  ', e, flush=True)
except Exception as ex:
    print('RunOnUnconnectedEdges failed:', ex, flush=True)
    algo = conn.GetConnectivityAlgo()
    print([m for m in dir(algo) if not m.startswith('_')], flush=True)

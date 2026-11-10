import sys, math
sys.path.insert(0, 'scratch/work/ax')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp251.kicad_pcb')

def mm(v):
    return (v.x / 1e6, v.y / 1e6)

mode = sys.argv[1]
if mode == 'via':
    x, y = float(sys.argv[2]), float(sys.argv[3])
    vs = [t for t in b.GetTracks() if isinstance(t, pcbnew.PCB_VIA)
          and t.GetNetname() == 'ULPI_STP'
          and abs(mm(t.GetPosition())[0] - x) < 0.01
          and abs(mm(t.GetPosition())[1] - y) < 0.01]
    assert len(vs) == 1, len(vs)
    b.Remove(vs[0])
    print(f'via deleted at ({x},{y})', flush=True)
elif mode == 'seg':
    x, y, lay = float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
    L = {'B': pcbnew.B_Cu, 'In2': pcbnew.In2_Cu, 'F': pcbnew.F_Cu}[lay]
    cs = [t for t in b.GetTracks()
          if not isinstance(t, pcbnew.PCB_VIA)
          and isinstance(t, pcbnew.PCB_TRACK)
          and t.GetNetname() == 'ULPI_STP' and t.GetLayer() == L
          and t.GetLength() / 1e6 <= 0.0751 + 1e-9
          and min(math.hypot(mm(t.GetStart())[0] - x,
                             mm(t.GetStart())[1] - y),
                  math.hypot(mm(t.GetEnd())[0] - x,
                             mm(t.GetEnd())[1] - y)) < 0.06]
    assert len(cs) == 1, (len(cs), x, y, lay)
    print(f'seg deleted {mm(cs[0].GetStart())} -> {mm(cs[0].GetEnd())}',
          flush=True)
    b.Remove(cs[0])
b.Save('hw/pdlvds_rx.exp251.kicad_pcb')
print('saved', flush=True)

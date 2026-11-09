import sys
sys.path.insert(0, 'scratch/work/ax')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp251.kicad_pcb')

def mm(v):
    return (v.x / 1e6, v.y / 1e6)

# 1. delete the dangling via (69.25,-3.6)
vs = [t for t in b.GetTracks() if isinstance(t, pcbnew.PCB_VIA)
      and t.GetNetname() == 'ULPI_STP'
      and abs(mm(t.GetPosition())[0] - 69.25) < 0.01
      and abs(mm(t.GetPosition())[1] + 3.6) < 0.01]
assert len(vs) == 1, len(vs)
b.Remove(vs[0])
print('via deleted', flush=True)
# 2. bulk-delete the fossil vertical: STP F segs with BOTH endpoints at
#    x=69.25 (+-0.011) and both y in [-3.61, -2.28]
vic = []
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA) or not isinstance(t, pcbnew.PCB_TRACK):
        continue
    if t.GetNetname() != 'ULPI_STP' or t.GetLayer() != pcbnew.F_Cu:
        continue
    s, e = mm(t.GetStart()), mm(t.GetEnd())
    if abs(s[0] - 69.25) < 0.011 and abs(e[0] - 69.25) < 0.011 \
            and -3.61 <= s[1] <= -2.28 and -3.61 <= e[1] <= -2.28:
        vic.append(t)
print(f'vertical segs to delete: {len(vic)}', flush=True)
assert 4 <= len(vic) <= 60, len(vic)
for v in vic:
    b.Remove(v)
b.Save('hw/pdlvds_rx.exp251.kicad_pcb')
print('saved', flush=True)

import sys, math, json
sys.path.insert(0, 'scratch/work/ax')
import wx
_app = wx.App(False)
import pcbnew
d = json.load(open(sys.argv[1]))
LAY = {'F.Cu': pcbnew.F_Cu, 'B.Cu': pcbnew.B_Cu, 'In2.Cu': pcbnew.In2_Cu}
todo = []
for x in d['violations']:
    if x['type'] != 'track_dangling':
        continue
    it = x['items'][0]
    desc = it.get('description', '')
    if 'ULPI_STP' not in desc:
        continue
    lay = desc.split('on ')[1].split(',')[0]
    todo.append((it['pos']['x'], it['pos']['y'], lay))
print('flagged STP segs:', todo, flush=True)
assert len(todo) == 1, todo
px, py, lay = todo[0]
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp251.kicad_pcb')

def mm(v):
    return (v.x / 1e6, v.y / 1e6)

cs = [t for t in b.GetTracks()
      if not isinstance(t, pcbnew.PCB_VIA)
      and isinstance(t, pcbnew.PCB_TRACK)
      and t.GetNetname() == 'ULPI_STP' and t.GetLayer() == LAY[lay]
      and abs(mm(t.GetStart())[0] - px) < 0.011
      and abs(mm(t.GetStart())[1] - py) < 0.011]
assert len(cs) == 1, (len(cs), px, py, lay)
print(f'deleting {mm(cs[0].GetStart())} -> {mm(cs[0].GetEnd())} on {lay}',
      flush=True)
b.Remove(cs[0])
b.Save('hw/pdlvds_rx.exp251.kicad_pcb')
print('saved', flush=True)

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
assert len(todo) >= 1, todo
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
if len(cs) != 1:
    # pick the candidate whose far end is free (endpoint degree 0)
    ends = []
    for t in b.GetTracks():
        if t.GetNetname() != 'ULPI_STP':
            continue
        if isinstance(t, pcbnew.PCB_VIA):
            ends.append(mm(t.GetPosition()))
        elif isinstance(t, pcbnew.PCB_TRACK) and t.GetLayer() == LAY[lay]:
            ends.append(mm(t.GetStart()))
            ends.append(mm(t.GetEnd()))

    def free(pt, skip):
        return sum(1 for q in ends
                   if math.hypot(q[0] - pt[0], q[1] - pt[1]) < 0.011
                   and q is not skip) == 1
    keep = []
    for t in cs:
        far = mm(t.GetEnd())
        deg = sum(1 for q in ends
                  if math.hypot(q[0] - far[0], q[1] - far[1]) < 0.011)
        if deg <= 1:
            keep.append(t)
    assert len(keep) == 1, ('disambig', len(keep), len(cs))
    cs = keep
assert len(cs) == 1, (len(cs), px, py, lay)
print(f'deleting {mm(cs[0].GetStart())} -> {mm(cs[0].GetEnd())} on {lay}',
      flush=True)
b.Remove(cs[0])
b.Save('hw/pdlvds_rx.exp251.kicad_pcb')
print('saved', flush=True)

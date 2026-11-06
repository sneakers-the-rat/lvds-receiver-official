import pcbnew, json, sys
b = pcbnew.LoadBoard(sys.argv[1])
spec = json.load(open(sys.argv[3]))
LAYERS = {'F': pcbnew.F_Cu, 'B': pcbnew.B_Cu, 'In1': pcbnew.In1_Cu, 'In2': pcbnew.In2_Cu}
def mm(v): return pcbnew.ToMM(v)
def key(t):
    s, e = t.GetStart(), t.GetEnd()
    return (t.GetNet().GetNetname(), t.GetLayer(),
            round(mm(s.x),3), round(mm(s.y),3), round(mm(e.x),3), round(mm(e.y),3))
want = {}
for netname, layer, segs in spec:
    for (x1,y1,x2,y2) in segs:
        for a, bb in [((x1,y1),(x2,y2)), ((x2,y2),(x1,y1))]:
            want[(netname, LAYERS[layer], a[0], a[1], bb[0], bb[1])] = (netname, layer)
found = {}
victims = []
for t in list(b.GetTracks()):
    k = key(t)
    if k in want and not isinstance(t, pcbnew.PCB_VIA):
        victims.append(t); found[want[k]] = found.get(want[k], 0) + 1
for t in victims:
    b.Remove(t)
for netname, layer, segs in spec:
    print(f'ripped {netname} {layer} {found.get((netname, layer), 0)} of {len(segs)}')
b.Save(sys.argv[2]); print('saved', sys.argv[2])

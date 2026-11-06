import sys, pcbnew
src, dst = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard(src)
def mm(v): return pcbnew.ToMM(v)
def M(x): return pcbnew.FromMM(x)
def key(t):
    s, e = t.GetStart(), t.GetEnd()
    return (round(mm(s.x),3), round(mm(s.y),3), round(mm(e.x),3), round(mm(e.y),3))
kill = {(22.75,-1.0,23.5,0.5), (24.75,0.625,25.375,0.125)}
kill |= {(k[2],k[3],k[0],k[1]) for k in list(kill)}
n = 0
for t in list(b.GetTracks()):
    if t.GetNetname() == 'GND' and key(t) in kill:
        b.Remove(t); n += 1
print('removed', n); assert n == 2
net = b.FindNet('GND')
for a, bb in [((22.5,-1.375),(23.5,0.5)), ((24.75,0.625),(25.825,-0.25))]:
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(M(a[0]), M(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(M(bb[0]), M(bb[1])))
    t.SetWidth(M(0.25)); t.SetLayer(pcbnew.F_Cu); t.SetNet(net)
    b.Add(t)
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
b.Save(dst); print('saved', dst)

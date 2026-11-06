import pcbnew, sys
def sig(b):
    s = {}
    for t in b.GetTracks():
        k = (t.GetNetname(), t.GetLayerName(), round(t.GetStart().x/1e6,3), round(t.GetStart().y/1e6,3), round(t.GetEnd().x/1e6,3), round(t.GetEnd().y/1e6,3), round(t.GetWidth()/1e6,3), t.Type())
        s[k] = s.get(k, 0) + 1
    return s
a = sig(pcbnew.LoadBoard(sys.argv[1])); bb = sig(pcbnew.LoadBoard(sys.argv[2]))
for k, v in bb.items():
    if a.get(k, 0) < v: print('ADDED:', k, 'x', v - a.get(k,0))
for k, v in a.items():
    if bb.get(k, 0) < v: print('REMOVED:', k, 'x', v - bb.get(k,0))

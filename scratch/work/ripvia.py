import pcbnew, json, sys
b = pcbnew.LoadBoard(sys.argv[1])
netname, xs, ys = sys.argv[3], float(sys.argv[4]), float(sys.argv[5])
n = 0
for v in list(b.GetTracks()):
    if isinstance(v, pcbnew.PCB_VIA) and v.GetNet().GetNetname() == netname:
        p = v.GetPosition()
        if abs(pcbnew.ToMM(p.x)-xs) < 0.01 and abs(pcbnew.ToMM(p.y)-ys) < 0.01:
            b.Remove(v); n += 1
print(f'ripped {n} via(s)')
b.Save(sys.argv[2])

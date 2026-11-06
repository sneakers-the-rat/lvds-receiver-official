import pcbnew, sys
b = pcbnew.LoadBoard(sys.argv[1])
def mm(v): return pcbnew.ToMM(v)
LAY={pcbnew.F_Cu:'F',pcbnew.In1_Cu:'In1',pcbnew.In2_Cu:'In2',pcbnew.B_Cu:'B'}
nets=sys.argv[2].split(',')
ts=b.Tracks(); ALL=[ts[i] for i in range(ts.size())]
for net in nets:
    print(f"== {net} ==")
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname()==net:
                pos=p.GetPosition(); sz=p.GetSize()
                print(f"  PAD {fp.GetReference()}.{p.GetNumber()} @({mm(pos.x):.3f},{mm(pos.y):.3f}) {mm(sz.x):.2f}x{mm(sz.y):.2f}")
    for t in ALL:
        if t.GetNetname()!=net: continue
        s,e=t.GetStart(),t.GetEnd()
        if t.Type()==pcbnew.PCB_VIA_T:
            v=pcbnew.PCB_VIA.Cast(t)
            print(f"  VIA @({mm(s.x):.3f},{mm(s.y):.3f}) d={mm(t.GetWidth()):.2f} drill={mm(v.GetDrillValue()):.2f}")
        else:
            print(f"  TRK {LAY.get(t.GetLayer(),t.GetLayer())} w={mm(t.GetWidth()):.2f} ({mm(s.x):.3f},{mm(s.y):.3f})->({mm(e.x):.3f},{mm(e.y):.3f})")
    for z in b.Zones():
        if z.GetNetname()==net:
            print(f"  ZONE on {LAY.get(z.GetLayer(), z.GetLayer())} prio={z.GetPriority()}")

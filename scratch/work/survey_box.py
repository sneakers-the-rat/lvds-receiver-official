import pcbnew, sys
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp203.kicad_pcb')
def mm(v): return pcbnew.ToMM(v)
LAY={pcbnew.F_Cu:'F',pcbnew.In1_Cu:'In1',pcbnew.In2_Cu:'In2',pcbnew.B_Cu:'B'}
x0,x1,y0,y1,layname = float(sys.argv[1]),float(sys.argv[2]),float(sys.argv[3]),float(sys.argv[4]),sys.argv[5]
LAYN={v:k for k,v in LAY.items()}
for fp in b.GetFootprints():
    for p in fp.Pads():
        pos=p.GetPosition(); px,py=mm(pos.x),mm(pos.y)
        if x0<=px<=x1 and y0<=py<=y1:
            sz=p.GetSize(); print(f"  PAD {fp.GetReference()}.{p.GetNumber()} [{p.GetNetname()}] @({px:.3f},{py:.3f}) {mm(sz.x):.2f}x{mm(sz.y):.2f}")
ts=b.Tracks()
for i in range(ts.size()):
    t=ts[i]
    if LAY.get(t.GetLayer())!=layname: continue
    s,e=t.GetStart(),t.GetEnd(); pts=[(mm(s.x),mm(s.y)),(mm(e.x),mm(e.y))]
    if any(x0-1<=x<=x1+1 and y0-1<=y<=y1+1 for x,y in pts):
        if t.Type()==pcbnew.PCB_VIA_T:
            print(f"  VIA [{t.GetNetname()}] @({pts[0][0]:.3f},{pts[0][1]:.3f}) d={mm(t.GetWidth()):.2f}")
        else:
            print(f"  TRK [{t.GetNetname()}] w={mm(t.GetWidth()):.2f} ({pts[0][0]:.3f},{pts[0][1]:.3f})->({pts[1][0]:.3f},{pts[1][1]:.3f})")

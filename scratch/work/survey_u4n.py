import pcbnew, sys
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp202.kicad_pcb')
def mm(v): return pcbnew.ToMM(v)
LAY = {pcbnew.F_Cu:'F', pcbnew.In1_Cu:'In1', pcbnew.In2_Cu:'In2', pcbnew.B_Cu:'B'}
x0,x1,y0,y1 = float(sys.argv[1]),float(sys.argv[2]),float(sys.argv[3]),float(sys.argv[4])
def inbox(x,y): return x0<=x<=x1 and y0<=y<=y1
print("== PADS in box ==")
for fp in b.GetFootprints():
    for p in fp.Pads():
        pos=p.GetPosition(); x,y=mm(pos.x),mm(pos.y)
        if inbox(x,y):
            sz=p.GetSize()
            print(f"  {fp.GetReference()}.{p.GetNumber()} [{p.GetNetname()}] @({x:.3f},{y:.3f}) size {mm(sz.x):.2f}x{mm(sz.y):.2f} layer={p.GetLayerSet().Seq() and ''} drill={mm(p.GetDrillSize().x):.2f}")
print("== TRACKS/VIAS in box ==")
for t in b.GetTracks():
    s=t.GetStart(); e=t.GetEnd()
    pts=[(mm(s.x),mm(s.y)),(mm(e.x),mm(e.y))]
    if any(inbox(*pt) for pt in pts) or (inbox(pts[0][0],pts[1][1]) and inbox(pts[1][0],pts[0][1])):
        lay=LAY.get(t.GetLayer(),str(t.GetLayer()))
        if t.Type()==pcbnew.PCB_VIA_T:
            print(f"  VIA [{t.GetNetname()}] @({pts[0][0]:.3f},{pts[0][1]:.3f}) d={mm(t.GetWidth()):.2f} drill={mm(t.GetDrill()):.2f}")
        else:
            print(f"  TRK [{t.GetNetname()}] {lay} w={mm(t.GetWidth()):.2f} ({pts[0][0]:.3f},{pts[0][1]:.3f})->({pts[1][0]:.3f},{pts[1][1]:.3f})")
print("== design rules ==")
ds=b.GetDesignSettings()
print("  min clearance:", mm(ds.GetDefault().GetClearance()))
print("  via min d/drill:", mm(ds.m_ViasMinSize), mm(ds.m_ViasMinDrill))
print("  track min w:", mm(ds.m_TrackMinWidth))

import pcbnew
SRC='hw/pdlvds_rx.exp208.kicad_pcb'
b=pcbnew.LoadBoard(SRC)
MM=pcbnew.ToMM
print("== ZONES ==")
for z in b.Zones():
    bb=z.GetBoundingBox()
    print(f"ZONE net={z.GetNetname()} lays={[b.GetLayerName(l) for l in z.GetLayerSet().Seq()]} bbox=({MM(bb.GetLeft()):.2f},{MM(bb.GetTop()):.2f})-({MM(bb.GetRight()):.2f},{MM(bb.GetBottom()):.2f})")
X0,X1,Y0,Y1=57.0,65.0,39.5,44.5
def inb(x,y): return X0<=x<=X1 and Y0<=y<=Y1
print("== FP pads in C51-new box ==")
for fp in b.GetFootprints():
    for pad in fp.Pads():
        p=pad.GetPosition()
        if inb(MM(p.x),MM(p.y)):
            sz=pad.GetSize(); print(f"PAD {pad.GetNetname()} {fp.GetReference()}.{pad.GetNumber()} ({MM(p.x):.3f},{MM(p.y):.3f}) {MM(sz.x):.3f}x{MM(sz.y):.3f}")
print("== TRACKS/VIAS in box ==")
for t in b.GetTracks():
    if t.Type()==pcbnew.PCB_VIA_T:
        p=t.GetPosition()
        if inb(MM(p.x),MM(p.y)): print(f"VIA {t.GetNetname()} ({MM(p.x):.3f},{MM(p.y):.3f}) d={MM(t.GetWidth()):.3f}")
    else:
        s,e=t.GetStart(),t.GetEnd()
        if inb(MM(s.x),MM(s.y)) or inb(MM(e.x),MM(e.y)):
            print(f"TRK {t.GetNetname()} {b.GetLayerName(t.GetLayer())} w={MM(t.GetWidth()):.3f} ({MM(s.x):.3f},{MM(s.y):.3f})->({MM(e.x):.3f},{MM(e.y):.3f})")
print("== In2 tracks in SLICEN swath x60-64 y34-41 ==")
for t in b.GetTracks():
    if t.Type()==pcbnew.PCB_VIA_T: continue
    if b.GetLayerName(t.GetLayer())!='In2.Cu': continue
    s,e=t.GetStart(),t.GetEnd()
    if (60<=MM(s.x)<=64 and 34<=MM(s.y)<=41) or (60<=MM(e.x)<=64 and 34<=MM(e.y)<=41):
        print(f"TRK {t.GetNetname()} In2 w={MM(t.GetWidth()):.3f} ({MM(s.x):.3f},{MM(s.y):.3f})->({MM(e.x):.3f},{MM(e.y):.3f})")

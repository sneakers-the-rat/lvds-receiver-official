import pcbnew
SRC='hw/pdlvds_rx.exp209.kicad_pcb'
b=pcbnew.LoadBoard(SRC)
MM=pcbnew.ToMM
def dump(x0,x1,y0,y1,lays=None):
    def inb(x,y): return x0<=x<=x1 and y0<=y<=y1
    for fp in b.GetFootprints():
        for pad in fp.Pads():
            p=pad.GetPosition()
            if inb(MM(p.x),MM(p.y)):
                sz=pad.GetSize(); print(f"PAD {pad.GetNetname()} {fp.GetReference()}.{pad.GetNumber()} ({MM(p.x):.3f},{MM(p.y):.3f}) {MM(sz.x):.3f}x{MM(sz.y):.3f}")
    for t in b.GetTracks():
        lay=b.GetLayerName(t.GetLayer())
        if lays and lay not in lays: continue
        if t.Type()==pcbnew.PCB_VIA_T:
            p=t.GetPosition()
            if inb(MM(p.x),MM(p.y)): print(f"VIA {t.GetNetname()} ({MM(p.x):.3f},{MM(p.y):.3f}) d={MM(t.GetWidth()):.3f} lay={lay}")
        else:
            s,e=t.GetStart(),t.GetEnd()
            if inb(MM(s.x),MM(s.y)) or inb(MM(e.x),MM(e.y)):
                print(f"TRK {t.GetNetname()} {lay} w={MM(t.GetWidth()):.3f} ({MM(s.x):.3f},{MM(s.y):.3f})->({MM(e.x):.3f},{MM(e.y):.3f})")
print("== In2 swath x50-63 y38-46 ==")
dump(50,63,38,46,lays=('In2.Cu',))
print("== C9 area all layers x48-54 y42-48 ==")
dump(48,54,42,48)

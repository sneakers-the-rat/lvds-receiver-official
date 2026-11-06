import pcbnew
SRC='hw/pdlvds_rx.exp211.kicad_pcb'
b=pcbnew.LoadBoard(SRC)
MM=pcbnew.ToMM
print("== trio/D5 pads ==")
for fp in b.GetFootprints():
    for pad in fp.Pads():
        if pad.GetNetname() in ('ULPI_DIR','ULPI_NXT','ULPI_STP','ULPI_D5'):
            p=pad.GetPosition(); sz=pad.GetSize()
            print(f"PAD {pad.GetNetname()} {fp.GetReference()}.{pad.GetNumber()} ({MM(p.x):.3f},{MM(p.y):.3f}) {MM(sz.x):.3f}x{MM(sz.y):.3f}")
print("== trio copper items ==")
for t in b.GetTracks():
    if t.GetNetname() in ('ULPI_DIR','ULPI_NXT','ULPI_STP'):
        if t.Type()==pcbnew.PCB_VIA_T:
            p=t.GetPosition(); print(f"VIA {t.GetNetname()} ({MM(p.x):.3f},{MM(p.y):.3f}) d={MM(t.GetWidth()):.3f}")
        else:
            s,e=t.GetStart(),t.GetEnd()
            print(f"TRK {t.GetNetname()} {b.GetLayerName(t.GetLayer())} w={MM(t.GetWidth()):.3f} ({MM(s.x):.3f},{MM(s.y):.3f})->({MM(e.x):.3f},{MM(e.y):.3f})")
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
print("== U7 south row F x73-79 y14-19 ==")
dump(73,79,14,19,lays=('F.Cu',))
print("== U7 south row In2+B x73-79 y14-19 ==")
dump(73,79,14,19,lays=('In2.Cu','B.Cu'))
print("== U6 west face F x66-71 y-5..2 ==")
dump(66,71,-5,2,lays=('F.Cu',))
print("== U6 west face In2+B x66-71 y-5..2 ==")
dump(66,71,-5,2,lays=('In2.Cu','B.Cu'))

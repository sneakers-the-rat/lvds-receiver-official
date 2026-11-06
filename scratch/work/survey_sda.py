import pcbnew
SRC='hw/pdlvds_rx.exp210.kicad_pcb'
b=pcbnew.LoadBoard(SRC)
MM=pcbnew.ToMM
def dump(x0,x1,y0,y1,lays=None,pads=True):
    def inb(x,y): return x0<=x<=x1 and y0<=y<=y1
    if pads:
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
print("== U4 east face F x66-71 y30-42 ==")
dump(66,71,30,42,lays=('F.Cu',))
print("== corridor In1 x67-76 y-4..40 ==")
dump(67,76,-4,40,lays=('In1.Cu',),pads=False)
print("== corridor In2 x67-76 y-4..40 ==")
dump(67,76,-4,40,lays=('In2.Cu',),pads=False)
print("== corridor B x67-76 y-4..40 ==")
dump(67,76,-4,40,lays=('B.Cu',),pads=False)
print("== pads corridor x67-76 y-4..40 ==")
dump(67,76,-4,40,lays=(),pads=True)

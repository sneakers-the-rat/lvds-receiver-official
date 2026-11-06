import pcbnew, sys
_app = pcbnew.wx.App(False) if hasattr(pcbnew, 'wx') else None
SRC='hw/pdlvds_rx.exp208.kicad_pcb'
b=pcbnew.LoadBoard(SRC)
MM=pcbnew.ToMM
# box of interest: U4 west side. Find U4 first.
for fp in b.GetFootprints():
    if fp.GetReference() in ('U4','C13','C51','U9'):
        p=fp.GetPosition()
        print(f"FP {fp.GetReference()} at ({MM(p.x):.3f},{MM(p.y):.3f}) rot {fp.GetOrientationDegrees():.0f}")
        for pad in fp.Pads():
            pp=pad.GetPosition(); sz=pad.GetSize()
            print(f"   pad {pad.GetNumber()} net={pad.GetNetname()} pos=({MM(pp.x):.3f},{MM(pp.y):.3f}) size=({MM(sz.x):.3f}x{MM(sz.y):.3f}) lay={pad.GetLayerSet()} drill={MM(pad.GetDrillSize().x):.3f}")
X0,X1,Y0,Y1=54.0,72.0,30.0,47.0
def inb(x,y): return X0<=x<=X1 and Y0<=y<=Y1
print("== TRACKS in box ==")
for t in b.GetTracks():
    if t.Type()==pcbnew.PCB_VIA_T: continue
    s,e=t.GetStart(),t.GetEnd()
    if inb(MM(s.x),MM(s.y)) or inb(MM(e.x),MM(e.y)):
        print(f"TRK net={t.GetNetname()} lay={b.GetLayerName(t.GetLayer())} w={MM(t.GetWidth()):.3f} ({MM(s.x):.3f},{MM(s.y):.3f})->({MM(e.x):.3f},{MM(e.y):.3f})")
print("== VIAS in box ==")
for t in b.GetTracks():
    if t.Type()!=pcbnew.PCB_VIA_T: continue
    p=t.GetPosition()
    if inb(MM(p.x),MM(p.y)):
        print(f"VIA net={t.GetNetname()} pos=({MM(p.x):.3f},{MM(p.y):.3f}) d={MM(t.GetWidth()):.3f} drill={MM(t.GetDrill()):.3f}")
print("== ZONES overlapping box ==")
for z in b.Zones():
    bb=z.GetBoundingBox()
    print(f"ZONE net={z.GetNetname()} lay={b.GetLayerName(z.GetFirstLayer())} bbox=({MM(bb.GetLeft()):.2f},{MM(bb.GetTop()):.2f})-({MM(bb.GetRight()):.2f},{MM(bb.GetBottom()):.2f})")

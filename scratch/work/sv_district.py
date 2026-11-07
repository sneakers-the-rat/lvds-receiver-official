import pcbnew, sys
SRC = sys.argv[1] if len(sys.argv) > 1 else 'hw/pdlvds_rx.exp211.kicad_pcb'
b = pcbnew.LoadBoard(SRC)
MM = pcbnew.ToMM
OUT = open('scratch/work/sv_district.txt', 'w')
def pr(*a):
    print(*a, file=OUT)

def padline(fp, pad):
    p = pad.GetPosition(); sz = pad.GetSize()
    lay = {pcbnew.F_Cu: 'F', pcbnew.B_Cu: 'B'}.get(pad.GetLayer(), 'thru' if pad.GetDrillSize().x > 0 else '?')
    return (f"PAD {pad.GetNetname():10s} {fp.GetReference()}.{pad.GetNumber()} "
            f"({MM(p.x):.3f},{MM(p.y):.3f}) {MM(sz.x):.3f}x{MM(sz.y):.3f} attr={lay}")

# Footprint positions in the district box
pr("== footprints x60-102 y-10..28 ==")
for fp in b.GetFootprints():
    p = fp.GetPosition()
    if 60 <= MM(p.x) <= 102 and -10 <= MM(p.y) <= 28:
        bb = fp.GetBoundingBox()
        pr(f"FP {fp.GetReference():6s} pos=({MM(p.x):.2f},{MM(p.y):.2f}) rot={fp.GetOrientationDegrees():.0f} "
           f"bbox=({MM(bb.GetX()):.2f},{MM(bb.GetY()):.2f})-({MM(bb.GetRight()):.2f},{MM(bb.GetBottom()):.2f}) layerside={'F' if fp.GetLayer()==pcbnew.F_Cu else 'B'}")

for ref in ('U6', 'U7', 'X1'):
    pr(f"== pads of {ref} ==")
    for fp in b.GetFootprints():
        if fp.GetReference() == ref:
            for pad in fp.Pads():
                pr('  ' + padline(fp, pad))

def dump(x0, x1, y0, y1, lays):
    def inb(x, y): return x0 <= x <= x1 and y0 <= y <= y1
    lines = []
    for fp in b.GetFootprints():
        for pad in fp.Pads():
            p = pad.GetPosition()
            if inb(MM(p.x), MM(p.y)):
                lines.append('  ' + padline(fp, pad))
    for t in b.GetTracks():
        lay = b.GetLayerName(t.GetLayer())
        if lay not in lays: continue
        if t.Type() == pcbnew.PCB_VIA_T:
            p = t.GetPosition()
            if inb(MM(p.x), MM(p.y)):
                lines.append(f"  VIA {t.GetNetname():10s} ({MM(p.x):.3f},{MM(p.y):.3f}) d={MM(t.GetWidth()):.3f} drill={MM(t.GetDrillValue()):.3f}")
        else:
            s, e = t.GetStart(), t.GetEnd()
            if inb(MM(s.x), MM(s.y)) or inb(MM(e.x), MM(e.y)):
                lines.append(f"  TRK {t.GetNetname():10s} {lay} w={MM(t.GetWidth()):.3f} ({MM(s.x):.3f},{MM(s.y):.3f})->({MM(e.x):.3f},{MM(e.y):.3f})")
    return lines

for lays, name in [(('F.Cu',), 'F'), (('In1.Cu',), 'In1'), (('In2.Cu',), 'In2'), (('B.Cu',), 'B')]:
    pr(f"== district box x66-100 y-8..24 layer {name} ==")
    for ln in dump(66, 100, -8, 24, lays):
        pr(ln)

# Nets of interest: every item board-wide
for net in ('ULPI_CK', 'ULPI_D4', 'ULPI_D6', 'ULPI_D7', 'PHY_1V8', 'XO', 'XI', 'USB_RST', 'SWCLK', 'I2C_SCL', 'DM_PHY', 'DP_PHY'):
    pr(f"== net {net} all items ==")
    for t in b.GetTracks():
        if t.GetNetname() != net: continue
        if t.Type() == pcbnew.PCB_VIA_T:
            p = t.GetPosition()
            pr(f"  VIA ({MM(p.x):.3f},{MM(p.y):.3f}) d={MM(t.GetWidth()):.3f}")
        else:
            s, e = t.GetStart(), t.GetEnd()
            pr(f"  TRK {b.GetLayerName(t.GetLayer())} w={MM(t.GetWidth()):.3f} ({MM(s.x):.3f},{MM(s.y):.3f})->({MM(e.x):.3f},{MM(e.y):.3f})")
    for fp in b.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname() == net:
                pr('  ' + padline(fp, pad))
OUT.close()
print("done")

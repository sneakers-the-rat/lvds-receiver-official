import pcbnew
SRC='hw/pdlvds_rx.exp208.kicad_pcb'
b=pcbnew.LoadBoard(SRC)
MM=pcbnew.ToMM
NETS=('SLICEP','SLICEN','CDR_NIN','CDR_PIN','CDR_VREF','I2C_SDA')
for fp in b.GetFootprints():
    for pad in fp.Pads():
        if pad.GetNetname() in NETS:
            p=pad.GetPosition(); sz=pad.GetSize()
            print(f"PAD {pad.GetNetname()} {fp.GetReference()}.{pad.GetNumber()} ({MM(p.x):.3f},{MM(p.y):.3f}) size {MM(sz.x):.3f}x{MM(sz.y):.3f}")
print("== TRACKS of these nets ==")
for t in b.GetTracks():
    if t.GetNetname() in NETS:
        if t.Type()==pcbnew.PCB_VIA_T:
            p=t.GetPosition(); print(f"VIA {t.GetNetname()} ({MM(p.x):.3f},{MM(p.y):.3f}) d={MM(t.GetWidth()):.3f}")
        else:
            s,e=t.GetStart(),t.GetEnd()
            print(f"TRK {t.GetNetname()} {b.GetLayerName(t.GetLayer())} w={MM(t.GetWidth()):.3f} ({MM(s.x):.3f},{MM(s.y):.3f})->({MM(e.x):.3f},{MM(e.y):.3f})")

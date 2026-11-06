import pcbnew, sys
SRC=sys.argv[1]; OUT=sys.argv[2] if len(sys.argv)>2 else SRC
b=pcbnew.LoadBoard(SRC)
zr=pcbnew.ZONE_FILLER(b); zr.Fill(b.Zones())
b.Save(OUT); print("refilled", OUT)

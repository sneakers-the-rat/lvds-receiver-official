import pcbnew, sys
b = pcbnew.LoadBoard(sys.argv[1])
print("BOARD", sys.argv[1])
bb = b.GetBoardEdgesBoundingBox()
print("edges bbox mm: x %.2f..%.2f y %.2f..%.2f" % (bb.GetLeft()/1e6, bb.GetRight()/1e6, bb.GetTop()/1e6, bb.GetBottom()/1e6))
fps = {}
for fp in b.GetFootprints():
    r = fp.GetReference()
    p = fp.GetPosition()
    fps[r] = (fp.GetFPID().GetLibItemName(), p.x/1e6, p.y/1e6, fp.GetOrientationDegrees())
for ref in sorted(sys.argv[2].split(',')):
    if ref in fps: print(ref, fps[ref])
    else: print(ref, "MISSING")
# all footprints sorted by position
print("--- all footprints (ref x y) ---")
for r in sorted(fps, key=lambda r: (fps[r][2], fps[r][1])):
    print("%s %.2f %.2f %s" % (r, fps[r][1], fps[r][2], fps[r][0]))

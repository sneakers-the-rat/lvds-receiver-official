"""t_ae5: debug t_ae4's courtyard test at C20's CURRENT site
(76.5,18.5) rot pad1dir (-1,0), which KiCad DRC proves has
zero courtyard overlaps on exp216. If the test blames anyone,
the test is wrong, not the board. Prints the blamed ref and
the intersection area."""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import check_pcb

board = pcbnew.LoadBoard(sys.argv[1])
fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
c20 = fps['C20']
c20_poly = c20.GetCourtyard(pcbnew.F_CrtYd)
print('direct self-check: C20 poly vs others, no rebuild')
for ref, fp in fps.items():
    if ref == 'C20':
        continue
    layer = pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd
    if fp.IsFlipped():
        continue
    poly = None
    try:
        poly = fp.GetCourtyard(layer)
    except Exception:
        poly = None
    if poly is None or poly.OutlineCount() == 0:
        poly = check_pcb._fallback_courtyard(fp, fp.IsFlipped())
    inter = pcbnew.SHAPE_POLY_SET(c20_poly)
    inter.BooleanIntersection(poly, pcbnew.SHAPE_POLY_SET.PM_FAST)
    area = 0.0
    for k in range(inter.OutlineCount()):
        area += inter.Outline(k).Area()
    if area / 1e12 > 0.001:
        print(f'  OVERLAP vs {ref}: {area/1e12:.4f} mm^2')

# now the rebuilt-polygon path from t_ae4 at the same site
chain = c20_poly.Outline(0)
pts = []
for i in range(chain.PointCount()):
    p = chain.GetPoint(i)
    pts.append((pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)))
c = pcbnew.ToMM(c20.GetPosition())
poly2 = pcbnew.SHAPE_POLY_SET()
ch = pcbnew.SHAPE_LINE_CHAIN()
for (lx, ly) in pts:
    ch.Append(pcbnew.VECTOR2I(pcbnew.FromMM(76.5 + (lx - c[0])),
                              pcbnew.FromMM(18.5 + (ly - c[1]))))
ch.SetClosed(True)
poly2.AddOutline(ch)
print('rebuilt poly area mm^2:', poly2.Outline(0).Area() / 1e12,
      'orig:', c20_poly.Outline(0).Area() / 1e12)

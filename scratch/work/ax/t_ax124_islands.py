import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
path = sys.argv[1]
b = pcbnew.LoadBoard(path)
for z in b.Zones():
    if z.GetNetname() == 'GND' and z.GetLayer() == pcbnew.F_Cu:
        polys = z.GetFilledPolysList(pcbnew.F_Cu)
        print(path, 'GND F outlines:', polys.OutlineCount(), flush=True)
        for i in range(polys.OutlineCount()):
            bx = polys.Outline(i).BBox()
            print('  island', i,
                  (round(bx.GetLeft() / 1e6, 2), round(bx.GetTop() / 1e6, 2),
                   round(bx.GetRight() / 1e6, 2),
                   round(bx.GetBottom() / 1e6, 2)), flush=True)

import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
b = pcbnew.LoadBoard(BOARD)
for fp in b.GetFootprints():
    bb = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
    l, t, r, bo = bb.GetLeft()/1e6, bb.GetTop()/1e6, bb.GetRight()/1e6, bb.GetBottom()/1e6
    # R20 rot90 courtyard at (69.5,4.0): x68.72..70.28, y2.47..5.53
    if l < 70.28 and r > 68.72 and t < 5.53 and bo > 2.47:
        print(f'{fp.GetReference()} courtyard {l:.2f},{t:.2f}..{r:.2f},{bo:.2f}', flush=True)

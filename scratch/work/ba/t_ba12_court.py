"""t_ba12: exact courtyard bboxes (harness coords) for every
footprint whose courtyard intersects x[70,84] y[6,13.5], plus
C23's own courtyard size. Uses GetCourtyard polys."""
import sys
sys.path.insert(0, 'scratch/work/ax')
import wx
_app = wx.App(False)
import pcbnew

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp252.kicad_pcb')
MM = 1e6


def court_bbox(fp):
    xs, ys = [], []
    for lyr in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
        ps = fp.GetCourtyard(lyr)
        if ps is None:
            continue
        for oi in range(ps.OutlineCount()):
            ch = ps.Outline(oi)
            for i in range(ch.PointCount()):
                p = ch.CPoint(i)
                xs.append(p.x / MM)
                ys.append(-p.y / MM)
    if not xs:
        return None
    return (min(xs), max(xs), min(ys), max(ys))


for fp in b.GetFootprints():
    bb = court_bbox(fp)
    if bb is None:
        continue
    if bb[0] < 84 and bb[1] > 70 and bb[2] < 13.5 and bb[3] > 6:
        pos = fp.GetPosition()
        print(f'{fp.GetReference()} pos ({pos.x/MM:.2f},{-pos.y/MM:.2f}) '
              f'courtyard x[{bb[0]:.2f},{bb[1]:.2f}] y[{bb[2]:.2f},{bb[3]:.2f}]')
    if fp.GetReference() == 'C23':
        print(f'C23 own courtyard x[{bb[0]:.2f},{bb[1]:.2f}] '
              f'y[{bb[2]:.2f},{bb[3]:.2f}] (w {bb[1]-bb[0]:.2f} '
              f'h {bb[3]-bb[2]:.2f})')
print('=== done ===')

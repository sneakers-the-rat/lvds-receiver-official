import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import check_pcb
from hand_stub import build_items
from bridge import groups_of, gapf
check_pcb.SURFACE = {pcbnew.F_Cu, pcbnew.B_Cu}
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp103.kicad_pcb')
items = build_items(b)
net = 'APD_K'
groups = groups_of(items, net)
def ctr(it):
    bb = it[3].BBox()
    return (pcbnew.ToMM((bb.GetLeft()+bb.GetRight())//2),
            pcbnew.ToMM((bb.GetTop()+bb.GetBottom())//2))
for i in range(len(groups)):
    for j in range(i+1, len(groups)):
        best = None
        for a in groups[i]:
            for c in groups[j]:
                g = gapf(a[3], a[2], c[3], c[2])
                if g is not None and (best is None or g < best[0]):
                    best = (g, a, c)
        if best:
            g, a, c = best
            print(f"APD_K g{i}({groups[i][0][4]}) <-> g{j}({groups[j][0][4]}): gap {g:.2f}  {a[4]}@{ctr(a)} <-> {c[4]}@{ctr(c)}")
        else:
            print(f"APD_K g{i} <-> g{j}: no pair within 3mm shape range")
for fp in b.GetFootprints():
    for pad in fp.Pads():
        if (fp.GetReference(), pad.GetNumber()) in (('R32','2'), ('C34','2'), ('R31','1')):
            p = pad.GetPosition()
            print('PAD', fp.GetReference(), pad.GetNumber(), pad.GetNetname(),
                  round(pcbnew.ToMM(p.x),2), round(pcbnew.ToMM(p.y),2))

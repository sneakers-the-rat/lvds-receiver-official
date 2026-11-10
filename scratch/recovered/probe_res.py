import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
import check_pcb
from hand_stub import build_items
from bridge import groups_of, gapf
check_pcb.SURFACE = {pcbnew.F_Cu, pcbnew.B_Cu}
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp99.kicad_pcb')
items = build_items(b)
NETS = sys.argv[1:]
for net in NETS:
    pads = []
    for fp in b.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname() == net:
                p = pad.GetPosition()
                pads.append(f"{fp.GetReference()}.{pad.GetNumber()}@({pcbnew.ToMM(p.x):.2f},{pcbnew.ToMM(p.y):.2f})")
    groups = groups_of(items, net)
    print(f"{net}: {len(groups)} groups; pads: {' '.join(pads)}")
    # closest cross-group pair
    best = None
    for i in range(len(groups)):
        for j in range(i+1, len(groups)):
            for a in groups[i]:
                for c in groups[j]:
                    g = gapf(a[3], a[2], c[3], c[2])
                    if g is not None and (best is None or g < best[0]):
                        best = (g, a, c)
    if best:
        g, a, c = best
        print(f"   closest gap {g:.2f}: {a[0]} {a[4]} <-> {c[0]} {c[4]}")

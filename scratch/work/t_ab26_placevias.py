"""t_ab26: place the two window vias on exp213 (fixed copper).

DIR via (67.50,28.90), NXT via (66.85,29.60), both d0.5.
Hand-verified against the DM<->REFCLK channel with staircase
STEP CORNERS (the t_ab25 fault: DP step corner (66.12,29.88)
erodes the sliver; centre distances, need via-to-track 0.575,
via-to-via 0.70):
  DIR (67.50,28.90): DM line y28.9 x~66.85 (+0.075), REFCLK
    F' (68.125,29.125) (+0.05), NXT via 0.955, FB_3V3 F far
  NXT (66.85,29.60): DP/DM corner (66.12,29.88) 0.78,
    REFCLK I'/J' joint (67.125,30.125) 0.59 (+0.015),
    DIR via 0.955, DIR seg2b endpoint-governed 0.955
Then t_ab2 threads each net; the placed via is the only
channel crossing available to its net.
"""
import wx
_app = wx.App(False)
import pcbnew

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp213.kicad_pcb')
M = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(M(x), M(y))
for net, (x, y) in {'ULPI_DIR': (67.50, 28.90),
                    'ULPI_NXT': (66.85, 29.60)}.items():
    code = b.GetNetcodeFromNetname(net)
    assert code > 0, net
    v = pcbnew.PCB_VIA(b); v.SetPosition(V(x, y))
    v.SetWidth(M(0.5)); v.SetDrill(M(0.3))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetNetCode(code)
    b.Add(v)
    print(f'placed {net} via at ({x},{y})')
zr = pcbnew.ZONE_FILLER(b); zr.Fill(b.Zones())
b.Save('scratch/work/t_ab26.kicad_pcb')
print('saved scratch/work/t_ab26.kicad_pcb')

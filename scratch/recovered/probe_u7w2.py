import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp99.kicad_pcb')
for layer, name in ((0, 'F'), (31, 'B')):
    print(f'--- {name} tracks x 71.5..80, y 9..24 (excl CAP_CLK) ---')
    for t in b.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA) or t.GetLayer() != layer:
            continue
        if t.GetNetname() == 'CAP_CLK':
            continue
        bb = t.GetBoundingBox()
        x0, x1 = pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetRight())
        y0, y1 = pcbnew.ToMM(bb.GetTop()), pcbnew.ToMM(bb.GetBottom())
        if x1 < 71.5 or x0 > 80 or y1 < 9 or y0 > 24:
            continue
        s, e = t.GetStart(), t.GetEnd()
        print('TRK', t.GetNetname(),
              (round(pcbnew.ToMM(s.x),2), round(pcbnew.ToMM(s.y),2)), '->',
              (round(pcbnew.ToMM(e.x),2), round(pcbnew.ToMM(e.y),2)))

import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp241.kicad_pcb')
victims = []
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == 'CAP_CLK':
        p = pcbnew.ToMM(t.GetPosition())
        if abs(p[0] - 70.2) < 0.01 and abs(p[1] - 1.8) < 0.01:
            victims.append(t)
assert len(victims) == 1, f'clk via victims: {len(victims)}'
for t in victims:
    b.Remove(t)
print('removed redundant clk_via (70.2,1.8)', flush=True)
filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())
b.Save('hw/pdlvds_rx.exp241.kicad_pcb')
print('saved exp241 v3', flush=True)

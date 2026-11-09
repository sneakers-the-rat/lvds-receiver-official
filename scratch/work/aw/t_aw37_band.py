import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
print('--- GND items (any layer) in (65.5,69,3.0,7.0) ---', flush=True)
for t in b.GetTracks():
    if t.GetNetname() != 'GND':
        continue
    if isinstance(t, pcbnew.PCB_VIA):
        p = pcbnew.ToMM(t.GetPosition())
        if 65.5 < p[0] < 69 and 3.0 < p[1] < 7.0:
            print(f'  via ({p[0]:.3f},{p[1]:.3f}) d{pcbnew.ToMM(t.GetWidth()):.2f}', flush=True)
    else:
        a = pcbnew.ToMM(t.GetStart()); c = pcbnew.ToMM(t.GetEnd())
        cx, cy = (a[0]+c[0])/2, (a[1]+c[1])/2
        if 65.5 < cx < 69 and 3.0 < cy < 7.0:
            print(f'  seg L{t.GetLayer()} ({a[0]:.3f},{a[1]:.3f})->({c[0]:.3f},{c[1]:.3f}) w{pcbnew.ToMM(t.GetWidth()):.2f}', flush=True)
print('--- CDR_LOL B items in (66.5,69.5,3.0,8.5) ---', flush=True)
for t in b.GetTracks():
    if t.GetNetname() != 'CDR_LOL' or isinstance(t, pcbnew.PCB_VIA):
        continue
    if t.GetLayer() != pcbnew.B_Cu:
        continue
    a = pcbnew.ToMM(t.GetStart()); c = pcbnew.ToMM(t.GetEnd())
    cx, cy = (a[0]+c[0])/2, (a[1]+c[1])/2
    if 66.5 < cx < 69.5 and 3.0 < cy < 8.5:
        print(f'  seg ({a[0]:.3f},{a[1]:.3f})->({c[0]:.3f},{c[1]:.3f}) w{pcbnew.ToMM(t.GetWidth()):.2f}', flush=True)
print('--- CDR_LOL vias in (66.5,69.5,3.0,8.5) ---', flush=True)
for t in b.GetTracks():
    if t.GetNetname() != 'CDR_LOL' or not isinstance(t, pcbnew.PCB_VIA):
        continue
    p = pcbnew.ToMM(t.GetPosition())
    if 66.5 < p[0] < 69.5 and 3.0 < p[1] < 8.5:
        print(f'  via ({p[0]:.3f},{p[1]:.3f})', flush=True)

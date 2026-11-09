import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA) or t.GetNetname() != 'PG_3V3':
        continue
    a = pcbnew.ToMM(t.GetStart()); c = pcbnew.ToMM(t.GetEnd())
    if abs(a[0]-68.625) < 0.01 and abs(a[1]-1.875) < 0.01:
        print(f'PG seg from joint: L{t.GetLayer()} -> ({c[0]:.3f},{c[1]:.3f}) w{pcbnew.ToMM(t.GetWidth()):.2f}', flush=True)
    if abs(c[0]-68.625) < 0.01 and abs(c[1]-1.875) < 0.01:
        print(f'PG seg into joint: L{t.GetLayer()} ({a[0]:.3f},{a[1]:.3f}) -> w{pcbnew.ToMM(t.GetWidth()):.2f}', flush=True)
# all PG B segs with centre in box (68,76,0.5,2.6)
print('--- PG B segs E of joint ---', flush=True)
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA) or t.GetNetname() != 'PG_3V3' or t.GetLayer() != pcbnew.B_Cu:
        continue
    a = pcbnew.ToMM(t.GetStart()); c = pcbnew.ToMM(t.GetEnd())
    cx, cy = (a[0]+c[0])/2, (a[1]+c[1])/2
    if 68.0 < cx < 76.0 and 0.5 < cy < 2.6:
        print(f'  ({a[0]:.3f},{a[1]:.3f})->({c[0]:.3f},{c[1]:.3f})', flush=True)

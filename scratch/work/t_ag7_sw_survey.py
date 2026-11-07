"""t_ag7: U7 south-west district survey on exp218.
Full track lists for the district nets, all U7 pads, and layer
rasters over x[69,80] y[8,19]."""
import sys, math
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
MM = pcbnew.ToMM
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp218.kicad_pcb')
LAY = {pcbnew.F_Cu: 'F', pcbnew.In1_Cu: 'In1', pcbnew.In2_Cu: 'In2',
       pcbnew.B_Cu: 'B'}
print('=== U7 pads ===')
for fp in b.GetFootprints():
    if fp.GetReference() == 'U7':
        for pad in fp.Pads():
            p = MM(pad.GetPosition())
            s = MM(pad.GetSize())
            print(f'  U7.{pad.GetNumber()} {pad.GetNetname()} '
                  f'({p[0]:.3f},{p[1]:.3f}) {s[0]:.2f}x{s[1]:.2f}')
for net in ('+3V3A', 'PHY_1V8', 'PHY_1V8A', 'ULPI_CK', 'ULPI_D0'):
    print(f'=== {net} (items with any point in x[68,84] y[4,22]) ===')
    for t in b.GetTracks():
        if t.GetNetname() != net:
            continue
        if isinstance(t, pcbnew.PCB_VIA):
            p = MM(t.GetPosition())
            if 68 <= p[0] <= 84 and 4 <= p[1] <= 22:
                print(f'  via ({p[0]:.3f},{p[1]:.3f}) '
                      f'd{MM(t.GetWidth()):.2f}')
        else:
            a, c = MM(t.GetStart()), MM(t.GetEnd())
            if (68 <= a[0] <= 84 and 4 <= a[1] <= 22) or \
               (68 <= c[0] <= 84 and 4 <= c[1] <= 22):
                print(f'  {LAY[t.GetLayer()]} ({a[0]:.3f},{a[1]:.3f})'
                      f'->({c[0]:.3f},{c[1]:.3f}) '
                      f'w{MM(t.GetWidth()):.2f}')
print('=== pads in box x[69,80] y[8,19] ===')
for fp in b.GetFootprints():
    for pad in fp.Pads():
        p = MM(pad.GetPosition())
        if 69 <= p[0] <= 80 and 8 <= p[1] <= 19:
            s = MM(pad.GetSize())
            print(f'  {fp.GetReference()}.{pad.GetNumber()} '
                  f'{pad.GetNetname()} ({p[0]:.3f},{p[1]:.3f}) '
                  f'{s[0]:.2f}x{s[1]:.2f}')

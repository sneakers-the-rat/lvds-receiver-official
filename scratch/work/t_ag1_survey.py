"""t_ag1: full dump of the D5/XO district from exp217.
All tracks/vias of the district nets anywhere on the board,
all pads in the box, XO/XI endpoint census."""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
MM = pcbnew.ToMM
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp217.kicad_pcb')
LAY = {pcbnew.F_Cu: 'F', pcbnew.In1_Cu: 'In1', pcbnew.In2_Cu: 'In2',
       pcbnew.B_Cu: 'B'}
NETS = ('XO', 'XI', 'ULPI_D4', 'ULPI_D5', 'ULPI_D6', 'ULPI_D7',
        'ULPI_D3', 'I2C_SCL', 'I2C_SDA', '+3V3D', 'NRST')
for net in NETS:
    print(f'=== {net} ===')
    for t in b.GetTracks():
        if t.GetNetname() != net:
            continue
        if isinstance(t, pcbnew.PCB_VIA):
            p = MM(t.GetPosition())
            print(f'  via ({p[0]:.3f},{p[1]:.3f}) d{MM(t.GetWidth()):.2f}')
        else:
            a, c = MM(t.GetStart()), MM(t.GetEnd())
            print(f'  {LAY[t.GetLayer()]} ({a[0]:.3f},{a[1]:.3f})'
                  f'->({c[0]:.3f},{c[1]:.3f}) w{MM(t.GetWidth()):.2f}')
print('=== pads of XO/XI/D5 nets (all footprints) ===')
for fp in b.GetFootprints():
    for pad in fp.Pads():
        if pad.GetNetname() in ('XO', 'XI', 'ULPI_D5'):
            p = MM(pad.GetPosition())
            s = MM(pad.GetSize())
            print(f'  {fp.GetReference()}.{pad.GetNumber()} '
                  f'{pad.GetNetname()} ({p[0]:.3f},{p[1]:.3f}) '
                  f'size {s[0]:.2f}x{s[1]:.2f}')
print('=== all pads in box x[76,97] y[0,21] ===')
for fp in b.GetFootprints():
    for pad in fp.Pads():
        p = MM(pad.GetPosition())
        if 76 <= p[0] <= 97 and 0 <= p[1] <= 21:
            s = MM(pad.GetSize())
            print(f'  {fp.GetReference()}.{pad.GetNumber()} '
                  f'{pad.GetNetname()} ({p[0]:.3f},{p[1]:.3f}) '
                  f'{s[0]:.2f}x{s[1]:.2f}')

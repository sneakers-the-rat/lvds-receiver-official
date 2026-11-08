"""t_ah1: FULL dump of the U7 south-west district on exp218.
Every pad and every track/via (F/In2/B) with any point in
x[66,84] y[2,22], printed exactly (no pad-only survey).
Also: complete item lists for the district nets board-wide
(ULPI_CK, +3V3A, PHY_1V8, PHY_1V8A, XO, ULPI_D0) so chains can
be walked without re-dumping."""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
MM = pcbnew.ToMM
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp218.kicad_pcb')
LAY = {pcbnew.F_Cu: 'F', pcbnew.In1_Cu: 'In1', pcbnew.In2_Cu: 'In2',
       pcbnew.B_Cu: 'B'}
X0, X1, Y0, Y1 = 66, 84, 2, 22

def inbox(x, y):
    return X0 <= x <= X1 and Y0 <= y <= Y1

print('=== PADS in box ===')
for fp in b.GetFootprints():
    for pad in fp.Pads():
        p = MM(pad.GetPosition())
        if inbox(*p):
            s = MM(pad.GetSize())
            print(f'  {fp.GetReference()}.{pad.GetNumber()} '
                  f'[{pad.GetNetname()}] ({p[0]:.3f},{p[1]:.3f}) '
                  f'{s[0]:.2f}x{s[1]:.2f}')
print('=== TRACKS/VIAS touching box (F/In2/B only) ===')
for t in b.GetTracks():
    net = t.GetNetname()
    if isinstance(t, pcbnew.PCB_VIA):
        p = MM(t.GetPosition())
        if inbox(*p):
            print(f'  via [{net}] ({p[0]:.3f},{p[1]:.3f}) '
                  f'd{MM(t.GetWidth()):.2f} drill{MM(t.GetDrill()):.2f}')
    else:
        ln = LAY.get(t.GetLayer())
        if ln not in ('F', 'In2', 'B'):
            continue
        a, c = MM(t.GetStart()), MM(t.GetEnd())
        if inbox(*a) or inbox(*c):
            print(f'  {ln} [{net}] ({a[0]:.3f},{a[1]:.3f})->'
                  f'({c[0]:.3f},{c[1]:.3f}) w{MM(t.GetWidth()):.2f}')
print('=== district nets: ALL items board-wide ===')
for net in ('ULPI_CK', '+3V3A', 'PHY_1V8', 'PHY_1V8A', 'XO',
            'ULPI_D0'):
    print(f'--- {net} ---')
    for t in b.GetTracks():
        if t.GetNetname() != net:
            continue
        if isinstance(t, pcbnew.PCB_VIA):
            p = MM(t.GetPosition())
            print(f'  via ({p[0]:.3f},{p[1]:.3f}) '
                  f'd{MM(t.GetWidth()):.2f}')
        else:
            ln = LAY.get(t.GetLayer())
            a, c = MM(t.GetStart()), MM(t.GetEnd())
            print(f'  {ln} ({a[0]:.3f},{a[1]:.3f})->'
                  f'({c[0]:.3f},{c[1]:.3f}) w{MM(t.GetWidth()):.2f}')
    for fp in b.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname() == net:
                p = MM(pad.GetPosition())
                print(f'  PAD {fp.GetReference()}.{pad.GetNumber()} '
                      f'({p[0]:.3f},{p[1]:.3f})')

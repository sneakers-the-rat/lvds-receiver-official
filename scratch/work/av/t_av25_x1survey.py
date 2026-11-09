"""t_av25: X1/C20/C21 geometry from exp240 + footprint survey of
the W/NW candidate district (x[50,72] y[10,36])."""
import wx
_app = wx.App(False)
import pcbnew

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp240.kicad_pcb')
lay = {0: 'F', 31: 'B'}
for fp in b.GetFootprints():
    ref = fp.GetReference()
    if ref in ('X1', 'C20', 'C21', 'X2'):
        p = fp.GetPosition()
        print(f'{ref}: centre=({p.x/1e6:.3f},{p.y/1e6:.3f}) '
              f'rot={fp.GetOrientationDegrees():.1f}')
        for pad in fp.Pads():
            pp = pad.GetPosition()
            sz = pad.GetSize()
            print(f'   pad {pad.GetNumber()} net={pad.GetNetname()} '
                  f'({pp.x/1e6:.3f},{pp.y/1e6:.3f}) '
                  f'size=({sz.x/1e6:.3f}x{sz.y/1e6:.3f}) '
                  f'layer={pad.GetLayer()}')
print('--- footprints in x[50,72] y[10,36] ---')
for fp in b.GetFootprints():
    p = fp.GetPosition()
    x, y = p.x / 1e6, p.y / 1e6
    if 50 <= x <= 72 and 10 <= y <= 36:
        bb = fp.GetBoundingBox()
        print(f'{fp.GetReference()}: centre=({x:.2f},{y:.2f}) '
              f'bbox x[{bb.GetLeft()/1e6:.2f},{bb.GetRight()/1e6:.2f}] '
              f'y[{bb.GetTop()/1e6:.2f},{bb.GetBottom()/1e6:.2f}]')
print('done')

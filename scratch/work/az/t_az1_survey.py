"""t_az1: survey the STP/XI/USB_RST quadrant on exp251 as-built.
Dumps: (a) all pads in region, (b) all tracks/vias of the nets of
interest, (c) every via in the region (fence inventory).
Region: x in [64, 92], y in [-2, 27]. Read-only."""
import sys
sys.path.insert(0, 'hw')
import pcbnew

_app = None
try:
    import wx
    _app = wx.App(False)
except Exception:
    pass

B = pcbnew.LoadBoard('hw/pdlvds_rx.exp251.kicad_pcb')
MM = 1e6
LAY = {pcbnew.F_Cu: 'F', pcbnew.In1_Cu: 'In1', pcbnew.In2_Cu: 'In2',
       pcbnew.B_Cu: 'B'}

def mm(v):
    return (v.x / MM, v.y / MM)

def inreg(x, y):
    return 64 <= x <= 92 and -2 <= y <= 27

NETS = ['PHY_1V8', 'XI', 'XO', 'USB_RST', 'DM_PHY', 'DP_PHY', 'ULPI_STP',
        '+3V3A', 'I2C_SCL', 'I2C_SDA', 'ULPI_DIR', 'ULPI_NXT', 'ULPI_CK',
        'REFCLK', 'RBIAS', 'GND', '+3V3D']

print('=== PADS in region ===')
for fp in B.GetFootprints():
    ref = fp.GetReference()
    for pad in fp.Pads():
        x, y = mm(pad.GetPosition())
        if inreg(x, y):
            sx, sy = pcbnew.ToMM(pad.GetSize())
            lays = ''.join(LAY[l] + ' ' for l in LAY if pad.IsOnLayer(l))
            print(f'{ref}.{pad.GetNumber()} net={pad.GetNetname()} '
                  f'({x:.3f},{y:.3f}) size=({sx:.2f}x{sy:.2f}) '
                  f'rot={pad.GetOrientationDegrees():.0f} layers={lays}')

print('=== FOOTPRINT positions in region ===')
for fp in B.GetFootprints():
    x, y = mm(fp.GetPosition())
    if inreg(x, y):
        print(f'{fp.GetReference()} at ({x:.2f},{y:.2f}) '
              f'rot={fp.GetOrientationDegrees():.0f} '
              f'fp={fp.GetFPID().GetLibItemName()}')

print('=== TRACKS/VIAS of interest ===')
for t in B.GetTracks():
    net = t.GetNetname()
    if isinstance(t, pcbnew.PCB_VIA):
        x, y = mm(t.GetPosition())
        if net in NETS or inreg(x, y):
            print(f'VIA {net} ({x:.3f},{y:.3f}) d={pcbnew.ToMM(t.GetWidth()):.2f}')
    else:
        if net not in NETS:
            continue
        a, b = mm(t.GetStart()), mm(t.GetEnd())
        if inreg(*a) or inreg(*b):
            print(f'SEG {net} {LAY.get(t.GetLayer(), "?")} '
                  f'({a[0]:.3f},{a[1]:.3f})->({b[0]:.3f},{b[1]:.3f}) '
                  f'w={pcbnew.ToMM(t.GetWidth()):.3f}')
print('=== done ===')

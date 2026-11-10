"""obs_south: exact-geometry census of the USB_RST south district
on exp257. Dumps raw items only (no margin model): U6 pads, full
ULPI_CK + USB_RST item lists, and every via / selected-net track /
pad intersecting x[70,78.5] y[2.5,10.5].
"""
import wx
wx.App(False)
import pcbnew

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp257.kicad_pcb')
LN = {pcbnew.F_Cu: 'F', pcbnew.In1_Cu: 'In1', pcbnew.In2_Cu: 'In2',
      pcbnew.B_Cu: 'B'}
BOX = (70.0, 2.5, 78.5, 10.5)


def mm(v):
    return v / 1e6


def in_box(x, y):
    return BOX[0] <= x <= BOX[2] and BOX[1] <= y <= BOX[3]


print('==== U6 pads (all) ====')
for fp in b.GetFootprints():
    if fp.GetReference() == 'U6':
        for p in fp.Pads():
            bb = p.GetBoundingBox()
            print(f"U6.{p.GetNumber():>3s} {p.GetNetname():12s} "
                  f"rect x[{mm(bb.GetLeft()):.3f},{mm(bb.GetRight()):.3f}] "
                  f"y[{mm(bb.GetTop()):.3f},{mm(bb.GetBottom()):.3f}]")

print('==== ULPI_CK + USB_RST items (whole board) ====')
for t in b.GetTracks():
    n = t.GetNetname()
    if n not in ('ULPI_CK', 'USB_RST'):
        continue
    if t.Type() == pcbnew.PCB_VIA_T:
        p = t.GetPosition()
        print(f"{n:10s} VIA ({mm(p.x):.3f},{mm(p.y):.3f}) "
              f"dia={mm(t.GetWidth()):.2f} drill={mm(t.GetDrillValue()):.2f}")
    else:
        s, e = t.GetStart(), t.GetEnd()
        print(f"{n:10s} {LN[t.GetLayer()]:3s} ({mm(s.x):.3f},{mm(s.y):.3f})"
              f"->({mm(e.x):.3f},{mm(e.y):.3f}) w={mm(t.GetWidth()):.3f}")

print('==== vias in box (any net) ====')
for t in b.GetTracks():
    if t.Type() == pcbnew.PCB_VIA_T:
        p = t.GetPosition()
        x, y = mm(p.x), mm(p.y)
        if in_box(x, y):
            print(f"{t.GetNetname():12s} VIA ({x:.3f},{y:.3f}) "
                  f"dia={mm(t.GetWidth()):.2f}")

print('==== tracks in box (fence nets) ====')
KEEP = ('ULPI_D0', 'ULPI_D1', 'ULPI_D2', 'ULPI_D3', 'ULPI_D4',
        'ULPI_D5', 'ULPI_D6', 'ULPI_D7', 'DAC_SYNC', 'SPI_MOSI',
        'SPI_SCK', 'I2C_SCL', 'I2C_SDA', 'BIST_DRV', 'GND')
for t in b.GetTracks():
    n = t.GetNetname()
    if n not in KEEP or t.Type() == pcbnew.PCB_VIA_T:
        continue
    s, e = t.GetStart(), t.GetEnd()
    a, c = (mm(s.x), mm(s.y)), (mm(e.x), mm(e.y))
    if in_box(*a) or in_box(*c):
        print(f"{n:10s} {LN[t.GetLayer()]:3s} ({a[0]:.3f},{a[1]:.3f})"
              f"->({c[0]:.3f},{c[1]:.3f}) w={mm(t.GetWidth()):.3f}")

print('==== pads intersecting box (any footprint) ====')
for fp in b.GetFootprints():
    for p in fp.Pads():
        bb = p.GetBoundingBox()
        r = (mm(bb.GetLeft()), mm(bb.GetTop()),
             mm(bb.GetRight()), mm(bb.GetBottom()))
        if r[0] <= BOX[2] and r[2] >= BOX[0] and \
           r[1] <= BOX[3] and r[3] >= BOX[1]:
            print(f"{fp.GetReference()}.{p.GetNumber():>3s} "
                  f"{p.GetNetname():12s} rect x[{r[0]:.3f},{r[2]:.3f}] "
                  f"y[{r[1]:.3f},{r[3]:.3f}]")

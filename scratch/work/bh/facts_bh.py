#!/usr/bin/env python3
"""bh facts: exact items in the USB_RST arrival district of exp257."""
import wx
_app = wx.App(False)
import pcbnew

B = '/home/hatch/workspace/pdlvds-route/hw/pdlvds_rx.exp257.kicad_pcb'
OUT = '/home/hatch/workspace/pdlvds-route/scratch/work/bh/facts_bh_out.txt'
IU = 1e6
b = pcbnew.LoadBoard(B)
LN = {pcbnew.F_Cu: 'F', pcbnew.In1_Cu: 'In1', pcbnew.In2_Cu: 'In2', pcbnew.B_Cu: 'B'}
lines = []


def mm(v):
    return v / IU


lines.append('== U6/U7 pads of interest:')
for fp in b.GetFootprints():
    if fp.GetReference() in ('U6', 'U7'):
        for p in fp.Pads():
            if p.GetNetname() in ('USB_RST', 'ULPI_CK', '+3V3D', 'ULPI_D0', 'I2C_SCL'):
                pos = p.GetPosition()
                lines.append(f"  {fp.GetReference()}.{p.GetNumber()} {p.GetNetname()} "
                             f"@({mm(pos.x):.3f},{mm(pos.y):.3f}) "
                             f"size {mm(p.GetSize().x):.2f}x{mm(p.GetSize().y):.2f}")

BOX = (73.8, 3.4, 76.4, 8.2)
lines.append(f'== tracks/vias touching box x[{BOX[0]},{BOX[2]}] y[{BOX[1]},{BOX[3]}]:')
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        p = t.GetPosition()
        x, y = mm(p.x), mm(p.y)
        if BOX[0] - 0.4 <= x <= BOX[2] + 0.4 and BOX[1] - 0.4 <= y <= BOX[3] + 0.4:
            lines.append(f"  VIA {t.GetNetname()} @({x:.3f},{y:.3f}) d{mm(t.GetWidth()):.2f}")
    else:
        s, e = t.GetStart(), t.GetEnd()
        pts = [(mm(s.x), mm(s.y)), (mm(e.x), mm(e.y))]
        lo_x, hi_x = min(p[0] for p in pts), max(p[0] for p in pts)
        lo_y, hi_y = min(p[1] for p in pts), max(p[1] for p in pts)
        if hi_x >= BOX[0] - 0.4 and lo_x <= BOX[2] + 0.4 and \
           hi_y >= BOX[1] - 0.4 and lo_y <= BOX[3] + 0.4:
            lines.append(f"  {LN[t.GetLayer()]} {t.GetNetname()} "
                         f"({pts[0][0]:.3f},{pts[0][1]:.3f})->({pts[1][0]:.3f},{pts[1][1]:.3f}) "
                         f"w{mm(t.GetWidth()):.2f}")

lines.append('== ULPI_CK all tracks/vias:')
for t in b.GetTracks():
    if t.GetNetname() != 'ULPI_CK':
        continue
    if isinstance(t, pcbnew.PCB_VIA):
        p = t.GetPosition()
        lines.append(f"  VIA @({mm(p.x):.3f},{mm(p.y):.3f}) d{mm(t.GetWidth()):.2f}")
    else:
        s, e = t.GetStart(), t.GetEnd()
        lines.append(f"  {LN[t.GetLayer()]} ({mm(s.x):.3f},{mm(s.y):.3f})->"
                     f"({mm(e.x):.3f},{mm(e.y):.3f}) w{mm(t.GetWidth()):.2f}")

with open(OUT, 'w') as f:
    f.write('\n'.join(lines) + '\n')
print('wrote', OUT, len(lines), 'lines')

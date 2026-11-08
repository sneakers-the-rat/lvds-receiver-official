"""t_as10: build exp239 from exp238 - GND strip heal + dangling-via removal.
Heal v2 (subtractive): rip 4 +3V3D F segs fencing the GND fill corridor east
of SCK's dive via (73.475,2.1): the tap (74.375,2.375)->(74.125,2.625),
(74.125,2.625)->(74.25,3.162) and bus segs (74.625,2.125)->(74.375,2.375),
(74.875,1.875)->(74.625,2.125). Via (74.25,3.5) stays fed by its pad column
and the In2 hop. Also delete SPI_SCK's dangling B-B via (77.05,-8.5).
Exact board rips, victim-asserted. Zone refill before save."""
import wx
_app = wx.App(False)
import pcbnew

SRC = 'hw/pdlvds_rx.exp238.kicad_pcb'
OUT = 'hw/pdlvds_rx.exp239.kicad_pcb'
board = pcbnew.LoadBoard(SRC)

def mm(v): return pcbnew.FromMM(v)

RIP_SEGS = [  # (net, x1, y1, x2, y2) on F.Cu
    ('+3V3D', 74.375, 2.375, 74.125, 2.625),
    ('+3V3D', 74.125, 2.625, 74.25, 3.162),
    ('+3V3D', 74.625, 2.125, 74.375, 2.375),
    ('+3V3D', 74.875, 1.875, 74.625, 2.125),
]
RIP_VIAS = [('SPI_SCK', 77.05, -8.5)]

def close(a, b): return abs(a - b) < 0.002

victims = []
for tr in board.GetTracks():
    net = tr.GetNetname()
    if isinstance(tr, pcbnew.PCB_VIA):
        for (n, x, y) in RIP_VIAS:
            if net == n and close(pcbnew.ToMM(tr.GetStart().x), x) and \
               close(pcbnew.ToMM(tr.GetStart().y), y):
                victims.append(('via', n, x, y, tr))
    else:
        sx, sy = pcbnew.ToMM(tr.GetStart().x), pcbnew.ToMM(tr.GetStart().y)
        ex, ey = pcbnew.ToMM(tr.GetEnd().x), pcbnew.ToMM(tr.GetEnd().y)
        for (n, x1, y1, x2, y2) in RIP_SEGS:
            if net == n and ((close(sx, x1) and close(sy, y1) and close(ex, x2) and close(ey, y2)) or
                             (close(sx, x2) and close(sy, y2) and close(ex, x1) and close(ey, y1))):
                victims.append(('seg', n, x1, y1, tr))

assert len(victims) == 5, f'expected 5 victims, found {len(victims)}: {victims[:6]}'
for v in victims:
    board.Remove(v[-1])
print(f'ripped {len(victims)} board items '
      f'({sum(1 for v in victims if v[0]=="seg")} segs + '
      f'{sum(1 for v in victims if v[0]=="via")} vias)')

filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(OUT)
print('saved', OUT)

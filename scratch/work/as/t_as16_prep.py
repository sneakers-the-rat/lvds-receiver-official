"""t_as16: build exp241prep from exp240 - rip the 12 fence segs fencing the
U6 CAP district (SDA In2 diagonal+staircase 6, SCL B staircase 3, +3V3A F
vertical+diagonal+horizontal 3). Exact board rips, victim-asserted."""
import wx
_app = wx.App(False)
import pcbnew

SRC = 'hw/pdlvds_rx.exp240.kicad_pcb'
OUT = 'hw/pdlvds_rx.exp241prep.kicad_pcb'
LAY = {0: pcbnew.F_Cu, 1: pcbnew.In2_Cu, 2: pcbnew.B_Cu}
board = pcbnew.LoadBoard(SRC)

RIPS = [  # (net, layer, x1, y1, x2, y2)
    ('I2C_SDA', 1, 69.375, 2.125, 71.125, 1.875),
    ('I2C_SDA', 1, 71.125, 1.875, 70.875, 1.625),
    ('I2C_SDA', 1, 70.875, 1.625, 70.625, 1.375),
    ('I2C_SDA', 1, 70.625, 1.375, 70.375, 1.125),
    ('I2C_SDA', 1, 70.375, 1.125, 70.125, 0.875),
    ('I2C_SDA', 1, 70.125, 0.875, 69.900, 0.820),
    ('I2C_SCL', 2, 70.125, 1.875, 70.375, 2.125),
    ('I2C_SCL', 2, 70.375, 2.125, 70.625, 2.375),
    ('I2C_SCL', 2, 70.625, 2.375, 70.875, 2.625),
    ('+3V3A', 0, 70.125, 2.625, 70.125, 1.875),
    ('+3V3A', 0, 70.125, 1.875, 70.338, 1.250),
    ('+3V3A', 0, 70.338, 1.250, 71.338, 1.250),
]

def close(a, b): return abs(a - b) < 0.002

victims = []
for tr in board.GetTracks():
    if isinstance(tr, pcbnew.PCB_VIA):
        continue
    net = tr.GetNetname()
    sx, sy = pcbnew.ToMM(tr.GetStart().x), pcbnew.ToMM(tr.GetStart().y)
    ex, ey = pcbnew.ToMM(tr.GetEnd().x), pcbnew.ToMM(tr.GetEnd().y)
    for (n, li, x1, y1, x2, y2) in RIPS:
        if net == n and tr.GetLayer() == LAY[li] and \
           ((close(sx, x1) and close(sy, y1) and close(ex, x2) and close(ey, y2)) or
            (close(sx, x2) and close(sy, y2) and close(ex, x1) and close(ey, y1))):
            victims.append(tr)
assert len(victims) == len(RIPS), \
    f'expected {len(RIPS)} victims, found {len(victims)}'
for v in victims:
    board.Remove(v)
print(f'ripped {len(victims)} board items')
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
board.Save(OUT)
print('saved', OUT)

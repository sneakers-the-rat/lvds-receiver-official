"""t_as20: build exp241esc from exp240: 22 exact rips + CAP escapes
(CLK via (70.02,1.83) + F approach; DATA via (69.9,3.18) + F approach)
+ CDR_LOL B jog (5 segs). Victim-asserted rips; reload census printed."""
import wx
_app = wx.App(False)
import pcbnew

SRC = 'hw/pdlvds_rx.exp240.kicad_pcb'
OUT = 'hw/pdlvds_rx.exp241esc.kicad_pcb'
LAY = {0: pcbnew.F_Cu, 1: pcbnew.In2_Cu, 2: pcbnew.B_Cu}
board = pcbnew.LoadBoard(SRC)

RIPS = [
    ('I2C_SDA', 1, 69.375, 2.125, 71.125, 1.875),
    ('I2C_SDA', 1, 71.125, 1.875, 70.875, 1.625),
    ('I2C_SDA', 1, 70.875, 1.625, 70.625, 1.375),
    ('I2C_SDA', 1, 70.625, 1.375, 70.375, 1.125),
    ('I2C_SDA', 1, 70.375, 1.125, 70.125, 0.875),
    ('I2C_SDA', 1, 70.125, 0.875, 69.900, 0.820),
    ('I2C_SCL', 2, 69.375, 1.375, 69.625, 1.625),
    ('I2C_SCL', 2, 69.625, 1.625, 69.875, 1.625),
    ('I2C_SCL', 2, 69.875, 1.625, 70.125, 1.875),
    ('I2C_SCL', 2, 70.125, 1.875, 70.375, 2.125),
    ('I2C_SCL', 2, 70.375, 2.125, 70.625, 2.375),
    ('I2C_SCL', 2, 70.625, 2.375, 70.875, 2.625),
    ('+3V3A', 0, 70.125, 2.625, 70.125, 1.875),
    ('+3V3A', 0, 70.125, 1.875, 70.338, 1.250),
    ('+3V3A', 0, 70.338, 1.250, 71.338, 1.250),
    ('+3V3A', 0, 69.875, 2.875, 70.125, 2.625),
    ('+3V3A', 0, 69.475, 2.750, 69.875, 2.875),
    ('+3V3A', 0, 69.875, 3.625, 69.875, 2.875),
    ('+3V3A', 0, 69.625, 3.875, 69.875, 3.625),
    ('+3V3A', 0, 69.375, 4.125, 69.625, 3.875),
    ('CDR_LOL', 2, 69.125, 3.375, 69.875, 3.375),
    ('CDR_LOL', 2, 69.875, 3.375, 70.625, 3.375),
]

def close(a, b): return abs(a - b) < 0.002

def census(b):
    c = {}
    for tr in b.GetTracks():
        c[tr.GetNetname()] = c.get(tr.GetNetname(), 0) + 1
    return c

before = census(board)
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

codes = {}
for n in ('CAP_CLK', 'CAP_DATA', 'CDR_LOL'):
    codes[n] = board.GetNetcodeFromNetname(n)

def add_seg(net, li, a, b, w=0.2):
    t = pcbnew.PCB_TRACK(board)
    t.SetNetCode(codes[net])
    t.SetLayer(LAY[li])
    t.SetWidth(pcbnew.FromMM(w))
    t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(a[0]), pcbnew.FromMM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(b[0]), pcbnew.FromMM(b[1])))
    board.Add(t)

def add_via(net, x, y):
    v = pcbnew.PCB_VIA(board)
    v.SetNetCode(codes[net])
    v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
    v.SetWidth(pcbnew.FromMM(0.5))
    v.SetDrill(pcbnew.FromMM(0.3))
    board.Add(v)

add_via('CAP_CLK', 70.02, 1.83)
add_seg('CAP_CLK', 0, (70.6, 1.78), (70.02, 1.83))
add_via('CAP_DATA', 69.9, 3.18)
add_seg('CAP_DATA', 0, (70.6, 2.2), (69.98, 2.6))
add_seg('CAP_DATA', 0, (69.98, 2.6), (69.9, 3.18))
for a, b in [((69.125, 3.375), (69.3, 3.58)), ((69.3, 3.58), (69.75, 3.78)),
             ((69.75, 3.78), (70.3, 3.85)), ((70.3, 3.85), (70.5, 3.6)),
             ((70.5, 3.6), (70.625, 3.375))]:
    add_seg('CDR_LOL', 2, a, b, 0.25)
print('adds done')
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
board.Save(OUT)
b2 = pcbnew.LoadBoard(OUT)
after = census(b2)
for n in sorted(set(before) | set(after)):
    if before.get(n, 0) != after.get(n, 0):
        print(f'census {n}: {before.get(n, 0)} -> {after.get(n, 0)}')
print('saved', OUT)

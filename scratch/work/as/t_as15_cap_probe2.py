"""t_as15: CLK via probe with the full U6-west fence rip set in the model
(+3V3A diagonal+horizontal, SDA In2 diagonal+staircase (5 segs), SCL B
staircase (4 segs)). Prints worst fence per candidate point."""
import sys, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
from t_ai_lib import load_items, pt_margin, seg_margin, apply_rip

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp240.kicad_pcb')
items = load_items(board)
RIPS = [
    ('seg', '+3V3A', 70.125, 1.875), ('seg', '+3V3A', 70.338, 1.25),
    ('seg', 'I2C_SDA', 69.375, 2.125), ('seg', 'I2C_SDA', 71.125, 1.875),
    ('seg', 'I2C_SDA', 70.875, 1.625), ('seg', 'I2C_SDA', 70.625, 1.375),
    ('seg', 'I2C_SCL', 69.875, 1.625), ('seg', 'I2C_SCL', 70.125, 1.875),
    ('seg', 'I2C_SCL', 70.375, 2.125), ('seg', 'I2C_SCL', 70.625, 2.375),
]
statics, nrip = apply_rip({l: list(items[l]) for l in range(3)}, RIPS)
print('model rips applied:', nrip)
PTS = [(70.1, 1.5), (70.0, 1.45), (70.2, 1.55), (69.95, 1.6), (70.3, 1.45),
       (70.1, 1.35), (70.25, 1.6), (69.9, 1.45), (70.15, 1.4), (70.05, 1.55)]
for (x, y) in PTS:
    worst = (9, None, None)
    for l in range(3):
        m, w = pt_margin(l, x, y, 'CAP_CLK', 0.25, statics[l])
        if m < worst[0]:
            worst = (m, l, w)
    mapp, wapp = seg_margin(0, (70.60, 1.75), (x, y), 'CAP_CLK', 0.1,
                            statics[0], step=0.04)
    print(f'CLK via ({x},{y}): via {worst[0]:+.3f} L{worst[1]} {worst[2]} | '
          f'approach {mapp:+.3f} {wapp}')

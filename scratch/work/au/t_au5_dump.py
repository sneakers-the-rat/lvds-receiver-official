"""t_au5: dump district items for the heal nets + CAP endpoints from
exp241esc, box x[60,80] y[-2,28]."""
import wx
_app = wx.App(False)
import pcbnew, sys
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
import t_ai_lib as L

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
items = L.load_items(board)
NETS = {'CAP_CLK', 'CAP_DATA', 'I2C_SDA', 'I2C_SCL', '+3V3A', 'CDR_LOL'}
LAY = {0: 'F', 1: 'In2', 2: 'B'}
for l in range(3):
    out = []
    for it in items[l]:
        if it[1] not in NETS:
            continue
        d = it[2]
        if it[0] == 'seg':
            cx, cy = (d[0] + d[2]) / 2, (d[1] + d[3]) / 2
        else:
            cx, cy = d[0], d[1]
        if 60 < cx < 80 and -2 < cy < 28:
            out.append(it)
    print(f'--- L{l} ({LAY[l]}): {len(out)} items')
    for it in sorted(out, key=lambda t: (t[1], t[2][1])):
        print(f'   {L.fmt_it(it)}')

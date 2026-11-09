"""t_au14: U9 pad map (exp241esc) + exp240 pocket items for
SCL/SDA/+3V3A/GND/TMP_ALERT/HV_SHDN in box x[62,72.5] y[-1,7.5]."""
import wx
_app = wx.App(False)
import pcbnew, sys
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
import t_ai_lib as L

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
for fp in board.GetFootprints():
    if fp.GetReference() == 'U9':
        print(f'U9 at {pcbnew.ToMM(fp.GetPosition())} '
              f'rot {fp.GetOrientationDegrees()}')
        for pad in fp.Pads():
            x, y = pcbnew.ToMM(pad.GetPosition())
            sx, sy = pcbnew.ToMM(pad.GetSize())
            print(f'   pad {pad.GetNumber()} {pad.GetNetname()} '
                  f'({x:.3f},{y:.3f}) {sx:.3f}x{sy:.3f} '
                  f'layers F={pad.IsOnLayer(pcbnew.F_Cu)} '
                  f'B={pad.IsOnLayer(pcbnew.B_Cu)}')

NETS = {'I2C_SCL', 'I2C_SDA', '+3V3A', 'GND', 'TMP_ALERT', 'HV_SHDN',
        'CDR_LOL', 'THR_DAC'}
board2 = pcbnew.LoadBoard('hw/pdlvds_rx.exp240.kicad_pcb')
items = L.load_items(board2)
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
        if 62 < cx < 72.5 and -1 < cy < 7.5:
            out.append(it)
    print(f'--- exp240 L{l} ({LAY[l]}): {len(out)} items')
    for it in sorted(out, key=lambda t: (t[1], t[2][1], t[2][0])):
        print(f'   {L.fmt_it(it)}')

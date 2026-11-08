"""t_at2b: verify each planned removal matches exactly one board item."""
import wx
_app = wx.App(False)
import pcbnew, sys
sys.path.insert(0, 'scratch/work/ai')
import t_ai_lib as L

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
items = L.load_items(board)

def key_seg(d):
    a = (round(d[0], 3), round(d[1], 3), round(d[2], 3), round(d[3], 3))
    b = (round(d[2], 3), round(d[3], 3), round(d[0], 3), round(d[1], 3))
    return a, b

REM = {
    1: [('HV_SHDN', s) for s in [
        (68.875, 0.625, 69.125, 0.375), (69.125, 0.375, 69.375, 0.125),
        (69.375, 0.125, 69.625, -0.125), (69.625, -0.125, 69.875, -0.375),
        (67.375, 2.125, 67.125, 2.375), (67.125, 2.375, 66.875, 2.625),
        (66.875, 2.625, 66.625, 2.875), (66.625, 2.875, 66.375, 3.125),
        (66.375, 3.125, 66.125, 3.375), (66.125, 3.375, 65.875, 3.625),
        (65.875, 3.625, 65.625, 3.875)]],
    2: [('I2C_SDA', s) for s in [
        (69.900, 0.820, 69.875, 0.625), (69.875, 0.625, 69.875, -9.125)]],
    0: [('GND', s) for s in [
        (71.000, 0.270, 69.600, 0.250), (69.600, 0.250, 68.900, 0.850),
        (68.900, 0.850, 68.200, 1.150), (68.200, 1.150, 67.850, 1.220),
        (67.850, 1.220, 67.500, 0.950)]],
}
for li, lst in REM.items():
    for n, s in lst:
        a, b = key_seg(s)
        hits = [it for it in items[li]
                if it[0] == 'seg' and it[1] == n
                and key_seg(it[2])[0] in (a, b)]
        print(f'L{li} {n} {s}: {len(hits)} match',
              '' if len(hits) == 1 else f'  ACTUAL: {[it[2] for it in items[li] if it[0]=="seg" and it[1]==n and abs(it[2][0]-s[0])<0.3 and abs(it[2][1]-s[1])<0.3]}')

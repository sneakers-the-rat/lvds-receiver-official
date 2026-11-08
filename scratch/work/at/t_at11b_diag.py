"""t_at11b: diagnostics for the joint via search — where do SDA
candidates survive, and what kills SCL candidates (gate / chord gate /
slot / chord-SDA distance)? Wider grids, P0 variants."""
import wx
_app = wx.App(False)
import pcbnew, sys, math
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
import t_ai_lib as L
from router import netclass
exec(open('scratch/work/at/t_at11_joint.py').read().split('results = []')[0]
     .split('board = ')[0].replace("P0 = (68.3, 3.1)",
                                  "P0 = (68.3, 3.1)"))
board = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
items = L.load_items(board)
def key_seg(d):
    a = (round(d[0], 3), round(d[1], 3), round(d[2], 3), round(d[3], 3))
    b = (round(d[2], 3), round(d[3], 3), round(d[0], 3), round(d[1], 3))
    return a, b
REM_SEGS = {
    1: [('HV_SHDN', s) for s in [
        (68.875, 0.625, 69.125, 0.375), (69.125, 0.375, 69.375, 0.125),
        (69.375, 0.125, 69.625, -0.125), (69.625, -0.125, 69.875, -0.375),
        (69.875, -0.375, 70.125, -0.625)]] + [
        ('I2C_SCL', (67.875, 5.125, 68.875, 1.625)),
        ('I2C_SCL', (68.875, 1.625, 69.375, 1.375))],
    2: [('I2C_SDA', s) for s in [
        (69.900, 0.820, 69.875, 0.625), (69.875, 0.625, 69.875, -9.125)]],
    0: [('GND', s) for s in [
        (71.000, 0.270, 69.600, 0.250), (69.600, 0.250, 68.900, 0.850),
        (68.900, 0.850, 68.200, 1.150), (68.200, 1.150, 67.850, 1.220),
        (67.850, 1.220, 67.500, 0.950)]] + [
        ('I2C_SCL', s) for s in [
            (68.625, 1.625, 68.875, 1.625), (68.875, 1.625, 69.125, 1.375),
            (69.125, 1.375, 69.375, 1.375)]],
}
REM_VIAS = [(69.9, 0.82, 'I2C_SDA'), (69.32, 2.14, 'I2C_SDA'),
            (69.375, 1.375, 'I2C_SCL')]
pool = {0: [], 1: [], 2: []}
for li in range(3):
    remkeys = set()
    for n, s in REM_SEGS.get(li, []):
        a, b = key_seg(s)
        remkeys.add((n, a)); remkeys.add((n, b))
    for it in items[li]:
        if it[0] == 'via':
            skip = False
            for vx, vy, vn in REM_VIAS:
                if it[1] == vn and abs(it[2][0] - vx) < 0.01 and \
                   abs(it[2][1] - vy) < 0.01:
                    skip = True
            if skip:
                continue
            if it[1] == '+3V3D' and abs(it[2][0] - 74.625) < 0.01 and \
               abs(it[2][1] - 24.375) < 0.01:
                pool[li].append(('via', '+3V3D', (74.625, 24.375, 0.25),
                                 it[3]))
                continue
        if it[0] == 'seg':
            a, b = key_seg(it[2])
            if (it[1], a) in remkeys:
                continue
            cx = (it[2][0] + it[2][2]) / 2
            cy = (it[2][1] + it[2][3]) / 2
            if li == 0 and it[1] == '+3V3D' and 70 < cx < 76 and 20 < cy < 26:
                continue
            if li == 1 and it[1] == 'XO' and 66 < cx < 76 and 16 < cy < 23:
                continue
        pool[li].append(it)
def add_via(net, x, y, r=0.25):
    for li in range(3):
        pool[li].append(('via', net, (x, y, r), netclass(net)[1]))
def add_seg(li, net, a, b, w):
    pool[li].append(('seg', net, (a[0], a[1], b[0], b[1], w / 2),
                     netclass(net)[1]))
BANDV = [(68.625, 0.875), (68.75, 0.5), (69.0, 0.25), (69.25, 0.0),
         (69.5, -0.25), (69.75, -0.5), (70.125, -0.625)]
for i in range(len(BANDV) - 1):
    add_seg(1, 'HV_SHDN', BANDV[i], BANDV[i + 1], 0.25)
add_via('I2C_SDA', 70.05, 0.82)
add_seg(2, 'I2C_SDA', (69.875, -1.5), (69.875, -9.125), 0.25)
add_seg(2, 'I2C_SDA', (69.875, -1.5), (70.05, 0.82), 0.25)
BOX = (65.5, 73.0, -0.5, 5.5)
local = L.in_box_pool(pool, BOX, pad=0.6)
def via_gate(net, x, y):
    worst = (9.9, None)
    for l in range(3):
        mm, w = L.pt_margin(l, x, y, net, 0.25, local[l])
        if mm < worst[0]:
            worst = (mm, w)
    return worst
def rect_dist(px, py, r):
    cx, cy, hw, hh = r
    return math.hypot(max(abs(px - cx) - hw, 0.0),
                      max(abs(py - cy) - hh, 0.0))
U96 = (69.225, 2.1, 0.225, 0.15)
print('--- SDA via scan (gate >= -0.05 shown, stub<=1.3):')
for i in range(41):
    for j in range(33):
        x, y = 68.3 + 0.05 * i, 1.3 + 0.05 * j
        if rect_dist(x, y, U96) > 1.3:
            continue
        g, w = via_gate('I2C_SDA', x, y)
        if g >= -0.05:
            print(f'  ({x:.2f},{y:.2f}) gate {g:+.3f} stub '
                  f'{rect_dist(x, y, U96):.2f} worst {L.fmt_it(w)}')
print('--- SCL via scan (gate >= -0.05):')
for i in range(33):
    for j in range(29):
        x, y = 68.7 + 0.05 * i, 0.85 + 0.05 * j
        g, w = via_gate('I2C_SCL', x, y)
        if g >= -0.05:
            print(f'  ({x:.2f},{y:.2f}) gate {g:+.3f} worst {L.fmt_it(w)}')

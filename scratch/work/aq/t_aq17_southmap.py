"""t_aq17: margin map for a d0.5 via (net SPI_MOSI) over the U6
south pocket x[87.4,91.2] y[-19.6,-16.6] on exp235 statics with
DBG_RX re-lay x88.10 applied. Prints worst margin per 0.1 cell
(x10) and the binding fence for the best cells."""
import sys, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai')
sys.path.insert(0, 'hw')
from t_ai_lib import load_items, pt_margin, in_box_pool, fmt_it

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp235.kicad_pcb')
items = load_items(b)
sr = set()
for (net, ax, ay, bx, by) in [
        ('DBG_RX', 89.125, -15.125, 88.875, -15.375),
        ('DBG_RX', 88.875, -15.375, 88.875, -19.875),
        ('DBG_RX', 88.875, -19.875, 88.875, -20.125)]:
    sr.add((net, round(ax, 3), round(ay, 3), round(bx, 3), round(by, 3)))
    sr.add((net, round(bx, 3), round(by, 3), round(ax, 3), round(ay, 3)))
statics = {li: [] for li in range(3)}
for li in range(3):
    for it in items[li]:
        if it[0] == 'seg':
            d = it[2]
            if (it[1], round(d[0], 3), round(d[1], 3), round(d[2], 3),
                    round(d[3], 3)) in sr:
                continue
        statics[li].append(it)
for a, c in [((89.125, -15.125), (88.100, -15.375)),
             ((88.100, -15.375), (88.100, -19.875)),
             ((88.100, -19.875), (88.875, -19.875))]:
    statics[1].append(('seg', 'DBG_RX',
                       (a[0], a[1], c[0], c[1], 0.1), 0.2))
pool = in_box_pool(statics, (85.0, 93.0, -21.5, -14.5), pad=1.2)

best = []
print('margin map (x100, . = <-0.05): rows y -16.6 (top) .. -19.6')
print('cols x 87.4 .. 91.2 step 0.2')
hdr = '      ' + ''.join(f'{(87.4 + 0.2 * i) % 10:.0f}' for i in range(20))
print(hdr)
yi = -16.6
while yi >= -19.61:
    row = f'{yi:6.2f}'
    xi = 87.4
    while xi <= 91.21:
        m = 9.9
        for l in range(3):
            mm, _w = pt_margin(l, xi, yi, 'SPI_MOSI', 0.25, pool[l])
            m = min(m, mm)
        if m >= -0.05:
            row += str(min(9, int((m + 0.05) * 20)))
            if m >= 0:
                best.append((m, xi, yi))
        else:
            row += '.'
        xi += 0.2
    print(row)
    yi -= 0.2
best.sort(reverse=True)
print('best cells:')
for (m, x, y) in best[:15]:
    fences = []
    for l in range(3):
        mm, w = pt_margin(l, x, y, 'SPI_MOSI', 0.25, pool[l])
        fences.append((mm, l, fmt_it(w)))
    fences.sort()
    print(f'  ({x:.2f},{y:.2f}) worst {m:+.3f} :: '
          + ' | '.join(f'L{fl} {fm:+.3f} {fw}' for fm, fl, fw in fences[:2]))

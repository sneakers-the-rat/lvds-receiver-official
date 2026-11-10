import sys
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/hw')
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/scratch/work/bm')
sys.path.insert(0, '/home/hatch/workspace/pdlvds-route/scratch/work/bn')
import gridroute as G
import bm_gate as BG
import bn_fix3 as F3
BG.clr = lambda net: 0.20
items = G.load_items(F3.SRC)
for it in items:
    it.layer = {'F': 'F.Cu', 'In2': 'In2.Cu', 'B': 'B.Cu'}.get(it.layer, it.layer)
C19_OLD = [(80.775, 12.0), (82.375, 12.0)]
C19_NEW = [('NRST', (80.815, 11.54, 81.375, 12.16)), ('GND', (81.775, 11.54, 82.335, 12.16))]
pool = []
for it in items:
    if F3.is_victim(it):
        continue
    if it.kind == 'trk' and it.net == 'NRST' and {F3.rk(it.a), F3.rk(it.b)} == {(80.775, 12.0), (80.55, 10.65)}:
        continue
    if it.kind == 'pad':
        cx = (it.rect[0] + it.rect[2]) / 2; cy = (it.rect[1] + it.rect[3]) / 2
        if any(abs(cx - ox) < 0.01 and abs(cy - oy) < 0.01 for ox, oy in F3.C48_OLD + C19_OLD):
            continue
    pool.append(it)
for net, rect in F3.C48_NEW + C19_NEW:
    pool.append(G.Item(net, 'pad', layer='F.Cu', rect=rect))

def show_trk(a, b, layer, net, hw):
    ms = BG.margin_trk(a, b, layer, net, pool, hw=hw)
    neg = sorted([(m, d) for m, d in ms if m < 0.06])
    print(f'{net} {layer} {a}->{b}: min={min([m for m, d in ms], default=9.9):+.3f} near={neg[:4]}')

def show_via(at, net):
    ms = BG.margin_via(at, net, pool, r=0.25)
    neg = sorted([(m, d) for m, d in ms if m < 0.06])
    print(f'via {net} {at}: min={min([m for m, d in ms], default=9.9):+.3f} near={neg[:4]}')

# candidate: V3 pocket, bow (81.05,12.85); V2 (80.55,12.55)
show_via((79.95, 13.75), 'ULPI_D3')
show_trk((79.95, 13.75), (81.05, 12.85), 'In2.Cu', 'ULPI_D3', 0.125)
show_trk((81.05, 12.85), (82.2, 11.6), 'In2.Cu', 'ULPI_D3', 0.125)
show_via((80.55, 12.55), 'ULPI_D2')
print('leg1 vs V2:', BG.pt_seg((80.55, 12.55), (79.95, 13.75), (81.05, 12.85)) - 0.125 - 0.25 - 0.20)
print('leg2 vs V2:', BG.pt_seg((80.55, 12.55), (81.05, 12.85), (82.2, 11.6)) - 0.125 - 0.25 - 0.20)
# straight leg for comparison
show_trk((79.95, 13.75), (82.2, 11.6), 'In2.Cu', 'ULPI_D3', 0.125)

print('--- V2 candidates ---')
for at in [(80.525, 12.5), (80.5, 12.55), (80.54, 12.56), (80.45, 12.6)]:
    show_via(at, 'ULPI_D2')

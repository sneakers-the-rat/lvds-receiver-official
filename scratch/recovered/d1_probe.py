import sys
sys.path.insert(0, 'hw')
import pcbnew, check_pcb
from hand_stub import build_items
check_pcb.SURFACE = {pcbnew.F_Cu, pcbnew.B_Cu}
MM = pcbnew.FromMM
b = pcbnew.LoadBoard('hw/pdlvds_rx.fr15.kicad_pcb')
items = build_items(b)
ALL = {pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu}

def blockers(net, shape, layers, safety=0.0):
    out = []
    for kind, n2, l2, s2, d2 in items:
        if n2 == net: continue
        shared = layers & l2
        if not shared: continue
        need = check_pcb.need_for(net, n2, shared)
        if shape.Collide(s2, MM(need - 0.001 + safety)):
            out.append(f'{n2}({d2},need{need:.2f})')
    return out

def seg(x1, y1, x2, y2, w):
    return pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(x1), MM(y1)),
                                pcbnew.VECTOR2I(MM(x2), MM(y2)), MM(w))
def disc(x, y, d=0.6):
    return pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(x), MM(y)),
                                pcbnew.VECTOR2I(MM(x), MM(y)), MM(d))

print('A: APD_A D1.4 neck (9.45,41.35)->(9.9,42.0) w0.25:',
      blockers('APD_A', seg(9.45, 41.35, 9.9, 42.0, 0.25), {pcbnew.F_Cu}))
print('A: via disc @(9.9,42.0):', blockers('APD_A', disc(9.9, 42.0), ALL))
for (ex, ey) in ((9.0, 43.2), (10.8, 43.2), (9.9, 44.0), (8.6, 41.2)):
    print(f'A: In2 tail ->({ex},{ey}):',
          blockers('APD_A', seg(9.9, 42.0, ex, ey, 0.25), {pcbnew.In2_Cu}))
print('B: APD_K D1.5 neck (9.52,40.0)->(10.6,40.0) w0.2:',
      blockers('APD_K', seg(9.52, 40.0, 10.6, 40.0, 0.2), {pcbnew.F_Cu}))
print('B: via disc @(10.6,40.0):', blockers('APD_K', disc(10.6, 40.0), ALL))
for (ex, ey) in ((10.6, 36.0), (10.6, 32.0), (12.5, 36.0), (9.0, 35.0)):
    print(f'B: In2 tail ->({ex},{ey}):',
          blockers('APD_K', seg(10.6, 40.0, ex, ey, 0.25), {pcbnew.In2_Cu}))

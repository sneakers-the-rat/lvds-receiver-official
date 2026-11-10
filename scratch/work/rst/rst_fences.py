import sys
sys.path.insert(0, 'hw')
import gridroute as GR

items = GR.load_items('hw/pdlvds_rx.exp272.kicad_pcb')

def show(net, pred, label):
    print(f'--- {label}')
    for it in items:
        if it.net == net and pred(it):
            b = f'->({it.b[0]:.3f},{it.b[1]:.3f})' if it.b else ''
            r = f' rect={tuple(round(v, 2) for v in it.rect)}' if it.rect else ''
            a = f'({it.a[0]:.3f},{it.a[1]:.3f})' if it.a else '(rect)'
            print(f'   {it.kind} {it.layer} {a}{b} hw={it.hw:.3f}{r}')

show('+3V3A', lambda it: it.kind == 'via', '+3V3A vias (all)')
show('+3V3A', lambda it: it.kind == 'trk' and it.layer in ('F', 'In2') and it.a and 71 < it.a[0] < 78 and 4 < it.a[1] < 17, '+3V3A F/In2 tracks x71-78 y4-17')
show('RBIAS', lambda it: it.kind == 'trk' and it.layer == 'In2' and it.a and 73.4 < it.a[0] < 74.4 and 5 < it.a[1] < 17.5, 'RBIAS In2 column zone')
show('RBIAS', lambda it: it.kind == 'via', 'RBIAS vias (all)')
show('DM_PHY', lambda it: it.a and 72 < it.a[0] < 78 and 15.5 < it.a[1] < 21, 'DM_PHY items x72-78 y15.5-21')
show('DP_PHY', lambda it: it.a and 72 < it.a[0] < 78 and 15.5 < it.a[1] < 21, 'DP_PHY items x72-78 y15.5-21')
show('ULPI_DIR', lambda it: True, 'ULPI_DIR all')
show('ULPI_NXT', lambda it: True, 'ULPI_NXT all')

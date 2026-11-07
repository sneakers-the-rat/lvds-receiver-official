"""t_af3: diagnostic for t_af2 -- print individually feasible via
candidates per net and, for the top combinations, which joint
check (stub / connector / mutual / launch) fails and by how much.
Imports t_af2's model by exec with the search section cut off.
"""
import math, sys
sys.path.insert(0, 'hw')

sys.argv = ['t_af2_d5opt.py', 'hw/pdlvds_rx.exp216.kicad_pcb']
src = open('scratch/work/t_af2_d5opt.py').read()
head = src.split('def stub_m')[0]
g = {'__name__': 'af2model'}
exec(compile(head, 't_af2_head', 'exec'), g)

# re-add the helpers from t_af2 (they were after the cut point too)
src2 = src[src.index('def stub_m'):src.index('sols = []')]
exec(compile(src2, 't_af2_helpers', 'exec'), g)

feas = g['feas']; PAD = g['PAD']; ANCH = g['ANCH']; RAD = g['RAD']
stub_m, conn_m, launch_m = g['stub_m'], g['conn_m'], g['launch_m']
seg_item = g['seg_item']
for net in ('ULPI_D4', 'ULPI_D6', 'ULPI_D5'):
    print(f"{net} feasible vias ({len(feas[net])}):")
    for m, V in feas[net]:
        print(f"   {V} margin {m:+.3f}")

print('\n--- pairwise diagnostics (all combos of feasible sets) ---')
best = []
for m4, V4 in feas['ULPI_D4']:
    s4 = stub_m('ULPI_D4', V4)
    c4 = conn_m('ULPI_D4', V4)
    stub4 = seg_item('ULPI_D4', PAD['ULPI_D4'], V4)
    conn4 = seg_item('ULPI_D4', V4, ANCH['ULPI_D4'])
    for m6, V6 in feas['ULPI_D6']:
        d46 = math.hypot(V4[0]-V6[0], V4[1]-V6[1]) - (RAD['ULPI_D4']+RAD['ULPI_D6']+0.2)
        s6 = stub_m('ULPI_D6', V6, (stub4,))
        c6 = conn_m('ULPI_D6', V6, (conn4,))
        stub6 = seg_item('ULPI_D6', PAD['ULPI_D6'], V6)
        for m5, V5 in feas['ULPI_D5']:
            d45 = math.hypot(V5[0]-V4[0], V5[1]-V4[1]) - (RAD['ULPI_D5']+RAD['ULPI_D4']+0.2)
            d65 = math.hypot(V5[0]-V6[0], V5[1]-V6[1]) - (RAD['ULPI_D5']+RAD['ULPI_D6']+0.2)
            s5 = stub_m('ULPI_D5', V5, (stub4, stub6))
            l5 = launch_m(V5, (conn4, seg_item('ULPI_D6', V6, ANCH['ULPI_D6'])), ())
            worst = min(m4, m6, m5, s4, c4, s6, c6, s5, l5, d46, d45, d65)
            best.append((worst, V4, V6, V5,
                         dict(m4=m4, s4=s4, c4=c4, m6=m6, s6=s6, c6=c6,
                              m5=m5, s5=s5, l5=l5, d46=d46, d45=d45, d65=d65)))
best.sort(key=lambda b: -b[0])
print(f'{len(best)} combos total; top 12 by worst-margin:')
for b in best[:12]:
    print(f"  worst {b[0]:+.3f} V4={b[1]} V6={b[2]} V5={b[3]}")
    print(f"      {b[4]}")

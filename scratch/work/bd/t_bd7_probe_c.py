"""t_bd7: direct element-by-element probe of family C's centre
config on exp256: NV=(75.10,17.30), DV=(74.80,18.00), DIR stub bend
(75.85,17.35). No scan machinery -- each gate called and printed."""
import sys
sys.path.insert(0, 'hw')
src = open('scratch/work/bd/t_bd4_famc.py').read()
src = src[:src.index('t0 = time.time()')]
D = type(sys)('D')
exec(compile(src, 't_bd4_defs', 'exec'), D.__dict__)

nv = (75.10, 17.30)
dv = (74.80, 18.00)
sb = (75.85, 17.35)
nv_it = ('via', 'ULPI_NXT', (nv[0], nv[1], 0.25), 0.2)
dv_it = ('via', 'ULPI_DIR', (dv[0], dv[1], 0.25), 0.2)
nxt_stub = ('seg', 'ULPI_NXT', (D.NXT_HEAD[0], D.NXT_HEAD[1], nv[0], nv[1], 0.1), 0.2)

print('nxt_via :', D.via_gate(nv[0], nv[1], 'ULPI_NXT',
                            extra_by_layer={0: [dv_it], 1: [dv_it], 2: [dv_it]}))
print('nxt_stub:', D.seg_gate(0, D.NXT_HEAD, nv, 'ULPI_NXT', 0.1, extra=[dv_it]))
print('nxt_in2 :', D.seg_gate(1, nv, D.NXT_VIA_OLD, 'ULPI_NXT', 0.1, extra=[dv_it]))
print('dir_via :', D.via_gate(dv[0], dv[1], 'ULPI_DIR',
                            extra_by_layer={0: [nv_it, nxt_stub], 1: [nv_it], 2: [nv_it]}))
stub_pts = [D.DIR_HEAD, sb, dv]
for p, q in zip(stub_pts, stub_pts[1:]):
    print('dir_stub', p, '->', q, ':',
          D.seg_gate(0, p, q, 'ULPI_DIR', 0.1, extra=[nv_it, nxt_stub]))
print('dir_bseg:', D.seg_gate(2, dv, D.DIR_B_END, 'ULPI_DIR', 0.1, extra=[nv_it]))

# ride shape from the brief: arc -> waist -> east lane -> jogs -> PV
pts = [(75.625, 18.625), (75.45, 18.25), (75.43, 17.98), (75.62, 16.90),
       (75.62, 16.30), (75.02, 15.95), (75.02, 13.40), (75.32, 12.75),
       (75.82, 10.30)]
dv_bseg = ('seg', 'ULPI_DIR', (dv[0], dv[1], D.DIR_B_END[0], D.DIR_B_END[1], 0.1), 0.2)
for p, q in zip(pts, pts[1:]):
    print('ride', p, '->', q, ':',
          D.seg_gate(2, p, q, 'XI', 0.1, extra=[nv_it, dv_it, dv_bseg]))

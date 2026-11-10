"""t_bd5: probe t_bd3's top config element-by-element to find which
gate really binds at -0.078 (the diag print showed inconsistent arg
tuples -- a via_gate-shaped arg under the 'nxt' key and arg=None
under 'dir_via'; verify before trusting any of it).
Loads t_bd3_diag's definitions only (source up to its scan loop)."""
import sys
sys.path.insert(0, 'hw')
src = open('scratch/work/bd/t_bd3_diag.py').read()
src = src[:src.index('t0 = time.time()')]
D = type(sys)('D')
exec(compile(src, 't_bd3_diag_defs', 'exec'), D.__dict__)

vx, vy, wx, wy, mx, sb = 74.90, 17.50, 74.52, 16.98, 74.50, (75.48, 17.22)
nxt = D.nxt_items(wx, wy, mx)
dm = D.dm_items()
print('via_gate DIR:', D.via_gate(vx, vy, 'ULPI_DIR', extra_by_layer={0: nxt + dm}))
stub_pts = [D.DIR_HEAD, sb, (vx, vy)]
for p, q in zip(stub_pts, stub_pts[1:]):
    print('stub leg', p, q, D.seg_gate(0, p, q, 'ULPI_DIR', 0.1, extra=nxt + dm))
print('dir_bseg:', D.seg_gate(2, (vx, vy), D.DIR_B_END, 'ULPI_DIR', 0.1))
dir_via_it = ('via', 'ULPI_DIR', (vx, vy, 0.25), 0.2)
for it in nxt:
    d = it[2]
    print('nxt leg', (d[0], d[1], d[2], d[3]),
          D.seg_gate(0, (d[0], d[1]), (d[2], d[3]), 'ULPI_NXT', 0.1,
                     extra=[dir_via_it] + dm))
for it in dm:
    d = it[2]
    print('dm leg', (d[0], d[1], d[2], d[3]),
          D.seg_gate(0, (d[0], d[1]), (d[2], d[3]), 'DM_PHY', 0.125,
                     extra=[dir_via_it] + nxt))
print('full_detail:', D.full_detail(vx, vy, wx, wy, mx, sb))

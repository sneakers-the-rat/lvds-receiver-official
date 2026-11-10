"""t_bd6: order-dependence test for the bd gate machinery.

t_bd3's printed detail for config (74.90,17.50 / bow 74.52,16.98 /
mx 74.50 / stub (75.48,17.22)) disagrees with t_bd5's direct probe of
the same config in a fresh process (-0.078/odd args vs -0.247/clean
args). If the gates are order-dependent (e.g. Items.near() state),
t_bd2's 'no positive config' verdict is also suspect. Test: call
full_detail for the config (a) first thing, (b) after a batch of
unrelated pre-gate via_gate calls mimicking the diag loop, and
(c) again -- compare."""
import sys
sys.path.insert(0, 'hw')
src = open('scratch/work/bd/t_bd3_diag.py').read()
src = src[:src.index('t0 = time.time()')]
D = type(sys)('D')
exec(compile(src, 't_bd3_defs', 'exec'), D.__dict__)

CFG = (74.90, 17.50, 74.52, 16.98, 74.50, (75.48, 17.22))
print('cold      :', D.full_detail(*CFG))
# mimic diag loop traffic: many via_gate pre-gates + full_details
for wx in (74.40, 74.44, 74.48):
    for vx in (74.78, 74.84, 74.90, 74.96):
        nxt = D.nxt_items(wx, 17.04, 74.58)
        D.via_gate(vx, 17.60, 'ULPI_DIR', extra_by_layer={0: nxt}, floor=-0.60)
        D.full_detail(vx, 17.60, wx, 17.04, 74.58, None)
print('after junk:', D.full_detail(*CFG))
print('again     :', D.full_detail(*CFG))

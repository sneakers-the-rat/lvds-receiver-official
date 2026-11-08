"""t_aj1: regression test for the in_box_pool large-pad drop.

Bug: with box y1=12.5 and pad=1.2, U7's EP (GND pad at (76,14),
half-size 1.55) was excluded from the pool because its CENTRE lies
14.0 > 12.5+1.2, even though its copper reaches y12.45 -- inside the
box's via reach. A viascan over that box then reported XO via
points at y12.5 as feasible (+0.015) when the true margin against
the EP is -0.450.

Asserts: (1) the EP pad is in the F pool for that box; (2) the
pool-based margin for an XO d0.5 via at (75.5,12.5) is negative;
(3) sanity: a genuinely clear point still scans positive (XO via
at its own existing location (76.0,10.625) is same-net, so use
PHY_1V8A at (69.9375,15.375), the known goal cluster, margin>0
against a pool built on the goal box).
"""
import sys
sys.path.insert(0, 'hw')
sys.path.insert(0, 'scratch/work/ai')
import wx
_app = wx.App(False)
import pcbnew
import t_ai_lib as L

board = pcbnew.LoadBoard('hw/pdlvds_rx.exp221.kicad_pcb')
items = L.load_items(board)

pool = L.in_box_pool(items, (74.0, 80.0, 8.5, 12.5), pad=1.2)
ep = [it for it in pool[0] if it[0] == 'pad' and it[1] == 'GND'
      and abs(it[2][0] - 76.0) < 0.01 and abs(it[2][1] - 14.0) < 0.01]
assert ep, 'FAIL: U7 EP pad missing from F pool (bug present)'
print('PASS: EP pad present in F pool for the y12.5 box')

m, worst = L.pt_margin(0, 75.5, 12.5, 'XO', 0.25, pool[0])
assert m < 0, f'FAIL: XO via at (75.5,12.5) margin {m:+.3f} >= 0'
print(f'PASS: XO via at (75.5,12.5) correctly blocked, margin {m:+.3f} '
      f'vs {L.fmt_it(worst)}')

pool2 = L.in_box_pool(items, (68.0, 72.0, 13.5, 17.0), pad=1.2)
m2 = min(L.pt_margin(li, 69.9375, 15.375, 'PHY_1V8A', 0.25, pool2[li])[0]
         for li in range(3))
assert m2 > 0, f'FAIL: goal-cluster via margin {m2:+.3f} <= 0'
print(f'PASS: PHY_1V8A goal dive (69.9375,15.375) margin {m2:+.3f} > 0')
print('ALL PASS')

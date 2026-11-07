"""t_ac9: move ULPI_DIR's window via SW — unkeystone NXT's wall.

On the DM-shifted board (t_ac7) NXT's start flood pours through the
canyon gate and down the DM<->REFCLK channel to y29.12, then dies:
at y29.25-29.75 the channel is walled by three overlapping shadows
— DM's staircase (west), REFCLK's zigzag (east), and the keystone,
DIR's window via at (67.25,29.625), whose 0.45 exclusion disc spans
the whole channel width at that row. Without it the slot at
(67.05,29.5) passes with margin +0.07.

Fix: move DIR's via 0.51 SW along its own B line to (66.9,30.0)
(probed legal for net ULPI_DIR on all layers: worst margins
FB_3V3 F +0.026, DM/DP/REFCLK +0.061). DIR's B approach extends
parallel to DP's B band (lines x+y=96.9 vs 96.0, 0.64 centrelines);
its F exit re-joins the existing F run at (66.875,28.75). DIR stays
connected by construction; DRC referees.

Ripped (ULPI_DIR): via (67.25,29.625) d0.5;
  B seg (69.25,27.625)-(67.25,29.625); F seg (67.25,29.625)-(66.875,28.75)
Added: via (66.9,30.0) d0.5/drill0.3;
  B seg (69.25,27.625)-(66.9,30.0); F seg (66.9,30.0)-(66.875,28.75), w0.2

Usage: xvfb-run -a python3 scratch/work/t_ac9_dir_via.py IN OUT
"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew

src, out = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(src)
MM = pcbnew.FromMM

code = board.GetNetcodeFromNetname('ULPI_DIR')
assert code > 0

def key(a, b):
    return tuple(sorted([(round(a[0], 3), round(a[1], 3)),
                         (round(b[0], 3), round(b[1], 3))]))

RIPSEG = {key((69.25, 27.625), (67.25, 29.625)),
          key((67.25, 29.625), (66.875, 28.75))}
ripped_s = ripped_v = 0
for t in list(board.GetTracks()):
    if t.GetNetname() != 'ULPI_DIR':
        continue
    if t.Type() == pcbnew.PCB_VIA_T:
        p = pcbnew.ToMM(t.GetPosition())
        if (round(p[0], 3), round(p[1], 3)) == (67.25, 29.625):
            board.Remove(t)
            ripped_v += 1
    else:
        a = pcbnew.ToMM(t.GetStart()); b = pcbnew.ToMM(t.GetEnd())
        if key(a, b) in RIPSEG:
            board.Remove(t)
            ripped_s += 1
print(f'ripped {ripped_s} segs, {ripped_v} vias')
assert ripped_s == 2 and ripped_v == 1

for lay, a, b in ((pcbnew.B_Cu, (69.25, 27.625), (66.9, 30.0)),
                  (pcbnew.F_Cu, (66.9, 30.0), (66.875, 28.75))):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(MM(b[0]), MM(b[1])))
    t.SetWidth(MM(0.2))
    t.SetLayer(lay)
    t.SetNetCode(code)
    board.Add(t)
v = pcbnew.PCB_VIA(board)
v.SetPosition(pcbnew.VECTOR2I(MM(66.9), MM(30.0)))
v.SetWidth(MM(0.5))
v.SetDrill(MM(0.3))
v.SetViaType(pcbnew.VIATYPE_THROUGH)
v.SetNetCode(code)
board.Add(v)
print('added 2 segs, 1 via')

zr = pcbnew.ZONE_FILLER(board)
zr.Fill(board.Zones())
board.Save(out)
print('saved', out)

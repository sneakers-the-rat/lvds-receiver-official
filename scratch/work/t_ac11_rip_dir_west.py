"""t_ac11: rip ULPI_DIR's copper west of its B-lobe run.

Keeps: F stub U7.12 -> dive via (75.875,17.375), B seg
(75.875,17.375)->(71.375,19.125), and the pad-side of everything
east of that point. Rips: the B seg (71.375,19.125)->(69.25,27.625),
window via, F legs, via (66.25,24.625), B legs, via (62.625,12.75),
In2 legs, mouth via (69.25,-1.375), F mouth seg — the entire
western journey, so the grid router can re-plan it around
ULPI_NXT's channel claim (see t_ac9 header for the via-in-channel
proof: channel perp width 1.17 < 0.575+0.45+0.425 needed for a via
plus a passing track).

Identification: every ULPI_DIR track/via whose BOTH endpoints (or
via centre) lie at x < 71.0. The kept B seg ends at x71.375; the
ripped B seg starts there but ends at 69.25 — the rule uses the
MINIMUM x of the item: rip iff min-x < 71.0 keeps (75.875..71.375)
and takes everything else.

Usage: xvfb-run -a python3 scratch/work/t_ac11_rip_dir_west.py IN OUT
"""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew

src, out = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(src)

ripped = kept = 0
for t in list(board.GetTracks()):
    if t.GetNetname() != 'ULPI_DIR':
        continue
    if t.Type() == pcbnew.PCB_VIA_T:
        x = pcbnew.ToMM(t.GetPosition())[0]
        take = x < 71.0
    else:
        a = pcbnew.ToMM(t.GetStart()); b = pcbnew.ToMM(t.GetEnd())
        take = min(a[0], b[0]) < 71.0
    if take:
        board.Remove(t)
        ripped += 1
    else:
        kept += 1
print(f'ULPI_DIR: ripped {ripped}, kept {kept}')

zr = pcbnew.ZONE_FILLER(board)
zr.Fill(board.Zones())
board.Save(out)
print('saved', out)

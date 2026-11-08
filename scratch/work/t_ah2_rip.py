"""t_ah2: district rip for the U7 south-west joint re-fanout.
Removes ONLY the two In2 verticals that wall the district:
- ULPI_CK  In2 (74.625,13.500)->(74.625,6.375) w0.25
- +3V3A    In2 (75.625,11.375)->(75.625,10.125) w0.20
- +3V3A    In2 (75.625,10.125)->(75.625,8.625)  w0.60
Both nets are re-joined afterwards by t_ab2_groute through the
freed field (their remaining webs stay as same-net targets).
Everything else is untouched. No adds, no refill (track removal
does not change zone geometry)."""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
MMf = pcbnew.ToMM
SRC = 'hw/pdlvds_rx.exp218.kicad_pcb'
OUT = sys.argv[1] if len(sys.argv) > 1 else \
    'scratch/work/ah/rip1.kicad_pcb'
board = pcbnew.LoadBoard(SRC)

def key(a, b):
    ka = (round(a[0], 3), round(a[1], 3))
    kb = (round(b[0], 3), round(b[1], 3))
    return min(ka, kb), max(ka, kb)

RIP = {
    ('ULPI_CK', key((74.625, 13.500), (74.625, 6.375))),
    ('+3V3A', key((75.625, 11.375), (75.625, 10.125))),
    ('+3V3A', key((75.625, 10.125), (75.625, 8.625))),
}
# capture netcodes before any Remove (standing tooling law)
codes = {n: board.GetNetcodeFromNetname(n)
         for n in ('ULPI_CK', '+3V3A')}
print('netcodes captured:', codes)
kill = []
for t in list(board.GetTracks()):
    if isinstance(t, pcbnew.PCB_VIA):
        continue
    if t.GetLayer() != pcbnew.In2_Cu:
        continue
    a, c = MMf(t.GetStart()), MMf(t.GetEnd())
    if (t.GetNetname(), key(a, c)) in RIP:
        kill.append(t)
print(f'ripping {len(kill)} segs (expect 3)')
assert len(kill) == 3, 'rip set mismatch — aborting'
for t in kill:
    board.Remove(t)
board.Save(OUT)
print(f'saved {OUT}')

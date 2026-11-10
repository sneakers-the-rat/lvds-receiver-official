"""t_ba4: prep252c = exp252 with ALL ULPI_STP tracks/vias ripped ONLY
(control for the groute experiment: PHY left exactly as banked)."""
import pcbnew

SRC = 'hw/pdlvds_rx.exp252.kicad_pcb'
OUT = 'scratch/work/ba/prep252c.kicad_pcb'


def census(b):
    c = {}
    for t in b.GetTracks():
        n = t.GetNetname()
        c[n] = c.get(n, 0) + 1
    return c


b = pcbnew.LoadBoard(SRC)
before = census(b)
stp = [t for t in list(b.GetTracks()) if t.GetNetname() == 'ULPI_STP']
print('STP victims:', len(stp))
for t in stp:
    b.Remove(t)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(OUT)
b2 = pcbnew.LoadBoard(OUT)
after = census(b2)
for n in sorted(set(before) | set(after)):
    if before.get(n, 0) != after.get(n, 0):
        print(f'census diff {n}: {before.get(n, 0)} -> {after.get(n, 0)}')
print('saved', OUT)

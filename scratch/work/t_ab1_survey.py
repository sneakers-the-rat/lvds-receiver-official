"""t_ab1: fresh exact survey of exp212 district box for the trio job.

Prints: U6/U7 full pad rows, all pads in box, all vias in box,
track counts per net/layer in box. Dumps full item list to
t_ab1_survey.txt (pads with OBB data, segs, vias) for design work.
"""
import wx
_app = wx.App(False)
import pcbnew, math

SRC = 'hw/pdlvds_rx.exp212.kicad_pcb'
b = pcbnew.LoadBoard(SRC)
MM = pcbnew.ToMM
X0, X1, Y0, Y1 = 58.0, 86.0, -14.0, 26.0

def inb(x, y): return X0 <= x <= X1 and Y0 <= y <= Y1

lines = []
pads = []
for fp in b.GetFootprints():
    ref = fp.GetReference()
    for pad in fp.Pads():
        p = MM(pad.GetPosition()); s = MM(pad.GetSize())
        if inb(p[0], p[1]):
            lays = []
            for nm, l in (('F', pcbnew.F_Cu), ('In1', pcbnew.In1_Cu),
                          ('In2', pcbnew.In2_Cu), ('B', pcbnew.B_Cu)):
                if pad.IsOnLayer(l): lays.append(nm)
            pads.append((ref, pad.GetNumber(), pad.GetNetname(), p[0], p[1],
                         s[0], s[1], pad.GetOrientationDegrees(),
                         ''.join(lays)))
pads.sort(key=lambda r: (r[0], r[3], r[4]))
for r in pads:
    lines.append(f"PAD {r[0]}.{r[1]} net={r[2]} c=({r[3]:.3f},{r[4]:.3f}) "
                 f"size=({r[5]:.3f}x{r[6]:.3f}) rot={r[7]:.1f} lays={r[8]}")

segs, vias = [], []
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        p = MM(t.GetPosition())
        if inb(p[0], p[1]):
            try:
                w = MM(t.GetWidth(pcbnew.F_Cu))
            except Exception:
                w = MM(t.GetWidth())
            vias.append((t.GetNetname(), p[0], p[1], w, MM(t.GetDrill())))
    else:
        a = MM(t.GetStart()); e = MM(t.GetEnd())
        if inb(a[0], a[1]) or inb(e[0], e[1]):
            ln = {pcbnew.F_Cu: 'F', pcbnew.In1_Cu: 'In1',
                  pcbnew.In2_Cu: 'In2', pcbnew.B_Cu: 'B'}[t.GetLayer()]
            segs.append((t.GetNetname(), ln, a[0], a[1], e[0], e[1],
                         MM(t.GetWidth())))
for v in sorted(vias, key=lambda r: (r[1], r[2])):
    lines.append(f"VIA {v[0]} c=({v[1]:.3f},{v[2]:.3f}) d={v[3]:.2f} drill={v[4]:.2f}")
for s in sorted(segs, key=lambda r: (r[1], r[0])):
    lines.append(f"SEG {s[0]} {s[1]} w={s[6]:.2f} ({s[2]:.3f},{s[3]:.3f})->({s[4]:.3f},{s[5]:.3f})")

open('scratch/work/t_ab1_survey.txt', 'w').write('\n'.join(lines) + '\n')
print(f"pads={len(pads)} vias={len(vias)} segs={len(segs)} -> t_ab1_survey.txt")
print("\n== U6 pads (all) ==")
for r in pads:
    if r[0] == 'U6':
        print(f"U6.{r[1]} net={r[2]} c=({r[3]:.3f},{r[4]:.3f}) size=({r[5]:.2f}x{r[6]:.2f}) {r[8]}")
print("\n== U7 pads (all) ==")
for r in pads:
    if r[0] == 'U7':
        print(f"U7.{r[1]} net={r[2]} c=({r[3]:.3f},{r[4]:.3f}) size=({r[5]:.2f}x{r[6]:.2f}) {r[8]}")

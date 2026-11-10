"""Plant one deliberate HV clearance violation on a COPY of the final
board: a track on APD_A (Default class) laid parallel to the long
APD_K (HV class) F.Cu run at a 0.50 mm gap -- legal under the old
Default-only rules (0.20), a violation only if the HV netclass in
the project file actually binds. Proof is the A/B DRC contrast."""
import wx
_app = wx.App(False)
import pcbnew

SRC = 'scratch/work/final/plant/pdlvds_rx.kicad_pcb'
b = pcbnew.LoadBoard(SRC)
best = None
for t in b.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA):
        continue
    if t.GetNetname() == 'APD_K' and t.GetLayer() == pcbnew.F_Cu:
        if best is None or t.GetLength() > best.GetLength():
            best = t
assert best is not None
a, e = best.GetStart(), best.GetEnd()
import math
dx, dy = e.x - a.x, e.y - a.y
L = math.hypot(dx, dy)
nx, ny = -dy / L, dx / L
hw = best.GetWidth() / 2.0
off = hw + pcbnew.FromMM(0.50) + pcbnew.FromMM(0.10)  # new track hw 0.10
nc = b.GetNetcodeFromNetname('APD_A')
assert nc > 0
t = pcbnew.PCB_TRACK(b)
t.SetStart(pcbnew.VECTOR2I(int(a.x + nx * off), int(a.y + ny * off)))
t.SetEnd(pcbnew.VECTOR2I(int(e.x + nx * off), int(e.y + ny * off)))
t.SetWidth(pcbnew.FromMM(0.20))
t.SetLayer(pcbnew.F_Cu)
t.SetNetCode(nc)
b.Add(t)
b.Save(SRC)
print(f'planted APD_A track parallel to APD_K run, gap 0.50 mm, '
      f'len {pcbnew.ToMM(L):.2f} mm')

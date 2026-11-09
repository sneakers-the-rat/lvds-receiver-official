"""t_aw21: esc/exp240 forensics for the remaining exp241 defects."""
import wx
_app = wx.App(False)
import pcbnew

esc = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
e240 = pcbnew.LoadBoard('hw/pdlvds_rx.exp240.kicad_pcb')

def vias_at(board, x, y, tol=0.06):
    out = []
    for t in board.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            p = pcbnew.ToMM(t.GetPosition())
            if abs(p[0] - x) < tol and abs(p[1] - y) < tol:
                out.append((t.GetNetname(), tuple(round(v, 3) for v in p),
                            round(pcbnew.ToMM(t.GetWidth()), 2)))
    return out

def tracks_touching(board, x, y, tol=0.06, net=None):
    out = []
    for t in board.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            continue
        if net and t.GetNetname() != net:
            continue
        a = pcbnew.ToMM(t.GetStart())
        b = pcbnew.ToMM(t.GetEnd())
        for (px, py) in (a, b):
            if abs(px - x) < tol and abs(py - y) < tol:
                out.append((t.GetNetname(), t.GetLayer(),
                            tuple(round(v, 3) for v in a),
                            tuple(round(v, 3) for v in b),
                            round(pcbnew.ToMM(t.GetWidth()), 2)))
                break
    return out

print('via at (68.375,17.5): esc', vias_at(esc, 68.375, 17.5),
      'exp240', vias_at(e240, 68.375, 17.5), flush=True)
print('tracks touching (68.375,17.5) esc:',
      tracks_touching(esc, 68.375, 17.5), flush=True)
print('--- SCL seg ends ---', flush=True)
print('touching (66.875,6.75) esc:', tracks_touching(esc, 66.875, 6.75),
      flush=True)
print('via at (66.875,6.75) esc:', vias_at(esc, 66.875, 6.75), flush=True)
print('touching (65.25,8.5) esc:', tracks_touching(esc, 65.25, 8.5),
      flush=True)
print('via at (65.25,8.5) esc:', vias_at(esc, 65.25, 8.5), flush=True)
print('--- CAP_CLK F tracks near (70.6,1.78) esc ---', flush=True)
for t in esc.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA) or t.GetNetname() != 'CAP_CLK':
        continue
    a = pcbnew.ToMM(t.GetStart())
    b = pcbnew.ToMM(t.GetEnd())
    cx, cy = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    if abs(cx - 70.8) < 1.1 and abs(cy - 1.8) < 0.9:
        print(f'   L{t.GetLayer()} ({a[0]:.3f},{a[1]:.3f})->'
              f'({b[0]:.3f},{b[1]:.3f}) w{pcbnew.ToMM(t.GetWidth()):.2f}',
              flush=True)
print('--- PG_3V3 B tracks box (67.3,70.6,1.1,2.9) esc ---', flush=True)
for t in esc.GetTracks():
    if isinstance(t, pcbnew.PCB_VIA) or t.GetNetname() != 'PG_3V3':
        continue
    a = pcbnew.ToMM(t.GetStart())
    b = pcbnew.ToMM(t.GetEnd())
    cx, cy = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    if 67.3 < cx < 70.6 and 1.1 < cy < 2.9:
        print(f'   L{t.GetLayer()} ({a[0]:.3f},{a[1]:.3f})->'
              f'({b[0]:.3f},{b[1]:.3f}) w{pcbnew.ToMM(t.GetWidth()):.2f}',
              flush=True)
print('--- XO B chain in esc ---', flush=True)
print('via at (71.875,19.625) esc:', vias_at(esc, 71.875, 19.625),
      flush=True)
print('touching (72.625,20.375) esc:', tracks_touching(esc, 72.625, 20.375),
      flush=True)
print('via at (72.625,20.375) esc:', vias_at(esc, 72.625, 20.375),
      flush=True)
print('T_AW21 DIAG3 COMPLETE', flush=True)

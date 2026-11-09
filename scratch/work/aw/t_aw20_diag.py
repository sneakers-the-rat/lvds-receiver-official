"""t_aw20: board-side diagnostics for exp241 DRC failures."""
import wx
_app = wx.App(False)
import pcbnew, json

esc = pcbnew.LoadBoard('hw/pdlvds_rx.exp241esc.kicad_pcb')
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp241.kicad_pcb')
B = json.load(open('scratch/work/aw/build_aw1.json'))

def vias(board):
    out = {}
    for t in board.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            p = tuple(round(v, 3) for v in pcbnew.ToMM(t.GetPosition()))
            out.setdefault((t.GetNetname(), p), []).append(t)
    return out

ve, vb = vias(esc), vias(b)
print('--- hole_near_hole pairs: pre-existing in esc? ---', flush=True)
for (net, p) in [(('+3V3A'), (69.15, 4.65)), (('+3V3A'), (69.125, 4.375)),
                 (('+3V3A'), (75.5, 8.25)), (('+3V3A'), (75.625, 8.625)),
                 (('+3V3D'), (71.25, 24.325)), (('+3V3D'), (75.85, 1.3)),
                 (('+3V3D'), (75.825, 1.275)), (('+3V3D'), (78.375, 20.125)),
                 (('+3V3D'), (78.25, 20.25)), (('+3V3D'), (78.25, 20.225)),
                 (('+3V3D'), (72.85, 3.4)), (('+3V3D'), (72.875, 3.375)),
                 (('I2C_SCL'), (69.3, 1.25)), (('I2C_SCL'), (69.35, 1.4)),
                 (('RBIAS'), (69.925, 20.475)), (('ULPI_DIR'), (67.5, 0.125)),
                 (('XO'), (71.625, 25.625))]:
    print(f'  {net} {p}: esc={((net, p) in ve)} exp241={((net, p) in vb)}',
          flush=True)

print('--- U9 pads exp241 (net, pos, size) ---', flush=True)
for fp in b.GetFootprints():
    if fp.GetReference() == 'U9':
        print(f'  U9 at {pcbnew.ToMM(fp.GetPosition())} '
              f'rot {fp.GetOrientationDegrees()}', flush=True)
        for pd in fp.Pads():
            print(f'   pad {pd.GetNumber()} {pd.GetNetname()} '
                  f'{tuple(round(v,3) for v in pcbnew.ToMM(pd.GetPosition()))} '
                  f'size {tuple(round(v,3) for v in pcbnew.ToMM(pd.GetSize()))}',
                  flush=True)

print('--- model journeys of interest ---', flush=True)
for nm in ('clk_exit_frun', 'clk9', 'scl_ffan', 'bheal', 'v3a_heal1',
           'v3a_heal2'):
    J = B['journeys'][nm]
    print(f'  {nm}: vias={J["vias"]}', flush=True)
    for r in J['runs']:
        print(f'    L{r["layer"]} first={r["pts"][0]} last={r["pts"][-1]} '
              f'n={len(r["pts"])}', flush=True)
J = B['journeys']['refclk_relay']
print(f'  refclk_relay: vias={J["vias"]}', flush=True)
for r in J['runs'][:3]:
    print(f'    L{r["layer"]} first={r["pts"][0]} last={r["pts"][-1]} '
          f'n={len(r["pts"])}', flush=True)

print('--- board tracks near points ---', flush=True)
def near_tracks(board, x, y, rad=1.2, nets=None):
    for t in board.GetTracks():
        if isinstance(t, pcbnew.PCB_VIA):
            p = pcbnew.ToMM(t.GetPosition())
            if abs(p[0] - x) < rad and abs(p[1] - y) < rad:
                print(f'    via {t.GetNetname()} ({p[0]:.3f},{p[1]:.3f}) '
                      f'w{pcbnew.ToMM(t.GetWidth()):.2f}', flush=True)
        else:
            a = pcbnew.ToMM(t.GetStart())
            bb = pcbnew.ToMM(t.GetEnd())
            cx, cy = (a[0] + bb[0]) / 2, (a[1] + bb[1]) / 2
            if abs(cx - x) < rad and abs(cy - y) < rad:
                if nets and t.GetNetname() not in nets:
                    continue
                print(f'    seg {t.GetNetname()} L{t.GetLayer()} '
                      f'({a[0]:.3f},{a[1]:.3f})->({bb[0]:.3f},{bb[1]:.3f}) '
                      f'w{pcbnew.ToMM(t.GetWidth()):.2f}', flush=True)

print(' [XO stub (71.875,19.625)]', flush=True)
near_tracks(b, 71.875, 19.625, 1.3, nets={'XO'})
print(' [+3V3A B seg (71.4,0.9)]', flush=True)
near_tracks(b, 71.37, 0.95, 1.2, nets={'+3V3A'})
print(' [+3V3A heal (68.5,16.5)]', flush=True)
near_tracks(b, 68.5, 16.5, 1.6, nets={'+3V3A'})
print(' [SCL In2 W (65.25,8.5)]', flush=True)
near_tracks(b, 65.6, 7.6, 1.8, nets={'I2C_SCL'})
print(' [PG_3V3 B vs SDA via (68.7,2.0)]', flush=True)
near_tracks(b, 68.7, 2.0, 1.3, nets={'PG_3V3', 'I2C_SDA'})
print(' [U5 CAP pads W edge]', flush=True)
for fp in b.GetFootprints():
    if fp.GetReference() == 'U5':
        for pd in fp.Pads():
            if pd.GetNetname() in ('CAP_CLK', 'CAP_DATA'):
                print(f'   pad {pd.GetNumber()} {pd.GetNetname()} '
                      f'{tuple(round(v,3) for v in pcbnew.ToMM(pd.GetPosition()))} '
                      f'size {tuple(round(v,3) for v in pcbnew.ToMM(pd.GetSize()))}',
                      flush=True)
print('T_AW20 DIAG COMPLETE', flush=True)

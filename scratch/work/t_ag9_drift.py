"""t_ag9: pin the pass-185 clearance-census +1.
Find GND tracks near (71.0,0.27) on exp214 vs exp215 and measure
the exact U6.32 pad -> GND track gap on F in both boards."""
import sys, math
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
MM = pcbnew.ToMM
for path in ('hw/pdlvds_rx.exp214.kicad_pcb',
             'hw/pdlvds_rx.exp215.kicad_pcb'):
    b = pcbnew.LoadBoard(path)
    pad = None
    for fp in b.GetFootprints():
        if fp.GetReference() == 'U6':
            for pd in fp.Pads():
                if pd.GetNumber() == '32':
                    p = MM(pd.GetPosition())
                    s = MM(pd.GetSize())
                    pad = (p[0], p[1], s[0] / 2, s[1] / 2,
                           pd.GetNetname())
    print(f'--- {path}: U6.32 pad {pad}')
    best = (9e9, None)
    for t in b.GetTracks():
        if t.GetNetname() != 'GND' or isinstance(t, pcbnew.PCB_VIA):
            continue
        if t.GetLayer() != pcbnew.F_Cu:
            continue
        a, c = MM(t.GetStart()), MM(t.GetEnd())
        if max(a[0], c[0]) < 69 or min(a[0], c[0]) > 73 or \
           max(a[1], c[1]) < -1.5 or min(a[1], c[1]) > 2:
            continue
        # distance from pad rect (axis aligned) to segment
        def pdist(px, py):
            dx, dy = c[0] - a[0], c[1] - a[1]
            L2 = dx * dx + dy * dy
            tt = 0.0 if L2 == 0 else max(0.0, min(1.0,
                        ((px - a[0]) * dx + (py - a[1]) * dy) / L2))
            return math.hypot(px - (a[0] + tt * dx),
                              py - (a[1] + tt * dy))
        d = 9e9
        for i in range(41):
            tt = i / 40
            x = a[0] + (c[0] - a[0]) * tt
            y = a[1] + (c[1] - a[1]) * tt
            ex = max(abs(x - pad[0]) - pad[2], 0.0)
            ey = max(abs(y - pad[1]) - pad[3], 0.0)
            d = min(d, math.hypot(ex, ey) - MM(t.GetWidth()) / 2)
        print(f'   GND F seg ({a[0]:.3f},{a[1]:.3f})->({c[0]:.3f},'
              f'{c[1]:.3f}) w{MM(t.GetWidth()):.2f} gap-to-pad '
              f'{d:+.3f}')
        if d < best[0]:
            best = (d, (a, c))
    print(f'   NEAREST GND F gap to U6.32 pad: {best[0]:+.3f} '
          f'(check_pcb power class needs 0.25; KiCad flat 0.20)')

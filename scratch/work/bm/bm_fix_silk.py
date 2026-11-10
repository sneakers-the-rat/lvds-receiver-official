import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp265.kicad_pcb')
fp = b.FindFootprintByReference('C22')
r = fp.Reference()
def openings(cx, cy):
    r.SetPosition(pcbnew.VECTOR2I(int(cx * 1e6), int(cy * 1e6)))
    bb = r.GetBoundingBox()
    x0, y0 = bb.GetX()/1e6 - 0.05, bb.GetY()/1e6 - 0.05
    x1, y1 = x0 + bb.GetWidth()/1e6 + 0.1, y0 + bb.GetHeight()/1e6 + 0.1
    bad = []
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            p = t.GetPosition(); rad = t.GetWidth()/2e6
            if x0 - rad < p.x/1e6 < x1 + rad and y0 - rad < p.y/1e6 < y1 + rad:
                bad.append(('via', p.x/1e6, p.y/1e6))
    for f2 in b.GetFootprints():
        for p in f2.Pads():
            pp = p.GetPosition(); sz = p.GetSize()
            if x0 - sz.x/2e6 < pp.x/1e6 < x1 + sz.x/2e6 and y0 - sz.y/2e6 < pp.y/1e6 < y1 + sz.y/2e6:
                bad.append(('pad', f2.GetReference(), pp.x/1e6, pp.y/1e6))
    return bad

for cand in [(77.2, 3.5), (70.0, 2.0), (85.0, 20.0), (60.0, 25.0), (77.2, 22.5), (88.0, 5.0), (68.0, -2.0), (90.0, 25.0)]:
    bad = openings(*cand)
    print('candidate', cand, 'openings:', bad)
    if not bad:
        print('chosen', cand)
        break
else:
    raise SystemExit('no clear candidate')
b.Save('hw/pdlvds_rx.exp266.kicad_pcb')
print('saved exp266')

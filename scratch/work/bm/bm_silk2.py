import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew
for f in ('exp264', 'exp265'):
    b = pcbnew.LoadBoard(f'hw/pdlvds_rx.{f}.kicad_pcb')
    fp = b.FindFootprintByReference('C22')
    r = fp.Reference()
    print(f, 'C22 fp at', fp.GetPosition().x/1e6, fp.GetPosition().y/1e6,
          'ref at', r.GetPosition().x/1e6, r.GetPosition().y/1e6)
    for fp2 in b.GetFootprints():
        for p in fp2.Pads():
            pp = p.GetPosition()
            if abs(pp.x/1e6 - 64.04) < 1.2 and abs(pp.y/1e6 - 17.35) < 1.2:
                print('   pad near:', fp2.GetReference(), p.GetPadName(), pp.x/1e6, pp.y/1e6)

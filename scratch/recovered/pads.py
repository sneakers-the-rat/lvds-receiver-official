import sys, wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp221.kicad_pcb')
for fp in b.GetFootprints():
    for pad in fp.Pads():
        p = pcbnew.ToMM(pad.GetPosition())
        if 73.5 < p[0] < 78.5 and 7.5 < p[1] < 11.0:
            print(f'{fp.GetReference()}.{pad.GetNumber()} [{pad.GetNetname()}] '
                  f'({p[0]:.3f},{p[1]:.3f}) fp_ref={fp.GetReference()} '
                  f'fp_pos={tuple(round(v,3) for v in pcbnew.ToMM(fp.GetPosition()))}')

import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp250.kicad_pcb')
for fp in b.GetFootprints():
    if fp.GetReference() in ('C22', 'C24', 'C28', 'C20', 'U5'):
        p = fp.GetPosition()
        print(f"{fp.GetReference()}: centre ({p.x/1e6:.3f},{p.y/1e6:.3f}) "
              f"rot {fp.GetOrientationDegrees():.0f} fp {fp.GetFPID().GetLibItemName() if hasattr(fp,'GetFPID') else ''}", flush=True)
        for pad in fp.Pads():
            pp = pad.GetPosition()
            print(f"   pad {pad.GetNumber()} net {pad.GetNetname()} "
                  f"({pp.x/1e6:.3f},{pp.y/1e6:.3f}) "
                  f"size ({pad.GetSize().x/1e6:.2f}x{pad.GetSize().y/1e6:.2f})",
                  flush=True)

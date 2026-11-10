import sys, wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard("hw/pdlvds_rx.exp79.kicad_pcb")
ds = b.GetDesignSettings()
print("DS attrs:", [a for a in dir(ds) if 'et' in a][:20])
try:
    ncs = ds.GetNetClasses()
    print("GetNetClasses ->", type(ncs))
except Exception as e:
    print("GetNetClasses err:", e)
try:
    print("AllNetClasses:", b.GetAllNetClasses() if hasattr(b, 'GetAllNetClasses') else 'n/a')
except Exception as e:
    print("err", e)
ni = b.FindNet("HV_RAW")
print("netinfo class:", ni.GetNetClass().GetName() if ni else None)

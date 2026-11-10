"""t_bb1: recovery re-referee of exp254 (pass 217 candidate) — KiCad DRC via
pcbnew.WriteDRCReport after zone refill, JSON to scratch/work/bb/drc254_bb.json.
Also dumps per-net fragment/group counts for XI and USB_RST."""
import wx
_app = wx.App(False)
import pcbnew, json

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp254.kicad_pcb')
filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())
b.BuildConnectivity()
out = []
err = pcbnew.WriteDRCReport(b, 'scratch/work/bb/drc254_bb.json', out)
print('drc written, err=', err)

d = json.load(open('scratch/work/bb/drc254_bb.json'))
viol = d.get('violations', [])
unc = d.get('unconnected_items', [])
from collections import Counter
print('violations:', len(viol), Counter(v['type'] for v in viol))
print('unconnected items:', len(unc))
for u in unc:
    print('  UNC:', u.get('type'), [ (i.get('description') or '')[:60] for i in u.get('items',[])])

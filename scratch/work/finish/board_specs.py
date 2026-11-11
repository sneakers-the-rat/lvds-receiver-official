import wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.kicad_pcb')
bb = b.GetBoardEdgesBoundingBox()
print('bbox mm: x %.2f..%.2f y %.2f..%.2f  size %.2f x %.2f' % (bb.GetLeft()/1e6, bb.GetRight()/1e6, bb.GetTop()/1e6, bb.GetBottom()/1e6, bb.GetWidth()/1e6, bb.GetHeight()/1e6))
ds = b.GetDesignSettings()
layers=[]
for lid in range(64):
    if b.IsLayerEnabled(lid) and 'Cu' in (pcbnew.LayerName(lid) or ''):
        layers.append(pcbnew.LayerName(lid))
print('enabled Cu layers:', layers)
print('footprints:', len(list(b.GetFootprints())), 'tracks:', len(list(b.GetTracks())))
vias=[t for t in b.GetTracks() if t.GetClass()=='PCB_VIA']
print('vias:', len(vias))
drills=sorted({round(v.GetDrillValue()/1e6,3) for v in vias})
print('via drill sizes mm:', drills)
th=[t for t in b.GetTracks() if t.GetClass()=='PCB_TRACK']
print('min track width mm:', min(t.GetWidth() for t in th)/1e6)

import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp201.kicad_pcb')
for z in b.Zones():
    print(z.GetNetname(), z.GetLayerSet().ConvertToStringList() if hasattr(z.GetLayerSet(),'ConvertToStringList') else '', "name", z.GetZoneName())
    bb = z.GetBoundingBox()
    print('   bbox mm: x %.2f..%.2f y %.2f..%.2f' % (bb.GetX()/1e6, (bb.GetX()+bb.GetWidth())/1e6, bb.GetY()/1e6, (bb.GetY()+bb.GetHeight())/1e6))

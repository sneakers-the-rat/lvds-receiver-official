import pcbnew, wx
app = wx.App(False)
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp250.kicad_pcb')
MM = 1000000
def mm(v): return (round(v.x/MM,3), round(v.y/MM,3))
for fp in b.GetFootprints():
    for p in fp.Pads():
        q = mm(p.GetPosition())
        if abs(q[1]-18.6)<0.05 and q[0] in (79.12, 80.08):
            print('FOUND', fp.GetReference(), fp.GetValue(), 'pad', p.GetNumber(), p.GetNetname(), q, 'fp at', mm(fp.GetPosition()))
print('--- all footprints centred near (79.6,18.6) ---')
for fp in b.GetFootprints():
    q = mm(fp.GetPosition())
    if abs(q[0]-79.6)<1.2 and abs(q[1]-18.6)<1.2:
        print(fp.GetReference(), fp.GetValue(), q, fp.GetFPID().GetLibItemName())

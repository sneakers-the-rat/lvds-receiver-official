"""t_bb25: ULPI_DIR full census: pads (ref.pin, pos, layer) +
all tracks/vias on exp256."""
import wx
_app = wx.App(False)
import pcbnew

b = pcbnew.LoadBoard('hw/pdlvds_rx.exp256.kicad_pcb')
MM = pcbnew.FromMM

def mm(v):
    return v / 1e6

nc = b.GetNetcodeFromNetname('ULPI_DIR')
print('pads:')
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetNetCode() == nc:
            pos = p.GetPosition()
            print(f'  {fp.GetReference()}.{p.GetNumber()} at '
                  f'({mm(pos.x):.3f},{mm(pos.y):.3f})')
print('tracks/vias:')
for t in b.GetTracks():
    if t.GetNetCode() == nc:
        if t.Type() == pcbnew.PCB_VIA_T:
            pos = t.GetPosition()
            print(f'  via ({mm(pos.x):.3f},{mm(pos.y):.3f}) w{mm(t.GetWidth()):.2f}')
        else:
            s, e = t.GetStart(), t.GetEnd()
            lay = {pcbnew.F_Cu: 'F', pcbnew.In2_Cu: 'In2',
                   pcbnew.B_Cu: 'B'}.get(t.GetLayer(), str(t.GetLayer()))
            print(f'  {lay} seg ({mm(s.x):.3f},{mm(s.y):.3f})->'
                  f'({mm(e.x):.3f},{mm(e.y):.3f}) w{mm(t.GetWidth()):.2f}')

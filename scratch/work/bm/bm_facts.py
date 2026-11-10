import wx; wx.App(False)
import pcbnew, sys
b=pcbnew.LoadBoard('hw/pdlvds_rx.exp261.kicad_pcb')
IU=1e6
BOX=(74.5,9.5,82.2,19.5)
NETS=['PHY_1V8','+3V3A','PHY_1V8A','XI','XO','ULPI_D0','ULPI_D1','ULPI_D2','ULPI_D3','ULPI_D4','ULPI_D5','ULPI_D6','ULPI_D7','ULPI_DIR','ULPI_STP','ULPI_NXT','ULPI_CK','I2C_SCL','+3V3D']
LN={pcbnew.F_Cu:'F',pcbnew.In1_Cu:'In1',pcbnew.In2_Cu:'In2',pcbnew.B_Cu:'B'}
def inb(x,y): return BOX[0]<=x<=BOX[2] and BOX[1]<=y<=BOX[3]
for fp in b.GetFootprints():
    if fp.GetReference() in ('U7','C22','C48','C19'):
        for pad in fp.Pads():
            p=pad.GetPosition()
            if pad.GetNetname() in NETS or fp.GetReference()!='U7':
                print(f"PAD {fp.GetReference()}.{pad.GetNumber()} {pad.GetNetname()} ({p.x/IU:.3f},{p.y/IU:.3f}) {pad.GetSize().x/IU:.2f}x{pad.GetSize().y/IU:.2f}")
for net in NETS:
    print(f"== {net}")
    for t in b.GetTracks():
        if t.GetNetname()!=net: continue
        if t.Type()==pcbnew.PCB_VIA_T:
            p=t.GetPosition()
            if inb(p.x/IU,p.y/IU): print(f"  VIA ({p.x/IU:.3f},{p.y/IU:.3f}) d{t.GetWidth()/IU:.2f}")
        else:
            s,e=t.GetStart(),t.GetEnd()
            if inb(s.x/IU,s.y/IU) or inb(e.x/IU,e.y/IU):
                print(f"  {LN[t.GetLayer()]} ({s.x/IU:.3f},{s.y/IU:.3f})->({e.x/IU:.3f},{e.y/IU:.3f}) w{t.GetWidth()/IU:.2f}")

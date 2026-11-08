"""t_ap1: J1 district dump (exp233). J1/D3 pads, all copper of the
USB-C signal nets board-wide, and every item in the J1 box."""
import sys, wx
_app = wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp233.kicad_pcb')
NETS = ('DP_CON', 'DM_CON', 'CC1', 'CC2', 'DN_CON', 'VBUS', 'USB_DP', 'USB_DM')
print('--- J1 / D3 pads ---')
for fp in b.GetFootprints():
    if fp.GetReference() in ('J1', 'D3'):
        pos = pcbnew.ToMM(fp.GetPosition())
        print(f'{fp.GetReference()} at ({pos[0]:.3f},{pos[1]:.3f}) rot {fp.GetOrientationDegrees()}')
        for p in fp.Pads():
            pp = pcbnew.ToMM(p.GetPosition())
            sz = pcbnew.ToMM(p.GetSize())
            print(f'  PAD {fp.GetReference()}.{p.GetPadName()} {p.GetNetname()} ({pp[0]:.3f},{pp[1]:.3f}) {sz[0]:.2f}x{sz[1]:.2f} layersFB={p.GetLayerSet().Contains(pcbnew.F_Cu)}/{p.GetLayerSet().Contains(pcbnew.B_Cu)} drill={pcbnew.ToMM(p.GetDrillSize())[0]:.2f}')
print('--- tracks/vias of USB nets ---')
LN = {0: 'F', 2: 'In2', 31: 'B'}
for t in b.GetTracks():
    if t.GetNetname() in NETS or 'CON' in t.GetNetname() or t.GetNetname().startswith('CC'):
        if isinstance(t, pcbnew.PCB_VIA):
            p = pcbnew.ToMM(t.GetPosition())
            print(f'VIA {t.GetNetname()} ({p[0]:.3f},{p[1]:.3f}) d{pcbnew.ToMM(t.GetWidth()):.2f}')
        else:
            a = pcbnew.ToMM(t.GetStart()); c = pcbnew.ToMM(t.GetEnd())
            print(f'SEG {t.GetNetname()} L{t.GetLayer()} ({a[0]:.3f},{a[1]:.3f})->({c[0]:.3f},{c[1]:.3f}) w{pcbnew.ToMM(t.GetWidth()):.2f}')

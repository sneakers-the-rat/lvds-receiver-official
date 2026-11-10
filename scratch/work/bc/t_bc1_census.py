"""t_bc1: census of XI net items + B-layer foreign items in the pocket district
on exp256. Ground truth for the hand-gated B ride into PV."""
import sys
sys.path.insert(0, 'hw')
import wx
_app = wx.App(False)
import pcbnew

MM = pcbnew.ToMM
src = 'hw/pdlvds_rx.exp256.kicad_pcb'
board = pcbnew.LoadBoard(src)
LAY = {pcbnew.F_Cu: 'F', pcbnew.In1_Cu: 'In1', pcbnew.In2_Cu: 'In2', pcbnew.B_Cu: 'B'}

print('== XI tracks ==')
for t in board.GetTracks():
    if t.GetNetname() != 'XI':
        continue
    if isinstance(t, pcbnew.PCB_VIA):
        p = MM(t.GetPosition())
        print(f'  VIA ({p[0]:.3f},{p[1]:.3f}) d={MM(t.GetWidth()):.2f} drill={MM(t.GetDrillValue()):.2f}')
    else:
        s, e = MM(t.GetStart()), MM(t.GetEnd())
        if 68 < s[0] < 90 and 0 < s[1] < 26 or 68 < e[0] < 90 and 0 < e[1] < 26:
            print(f'  {LAY[t.GetLayer()]} ({s[0]:.3f},{s[1]:.3f})->({e[0]:.3f},{e[1]:.3f}) w={MM(t.GetWidth()):.2f}')

print('== XI pads ==')
for fp in board.GetFootprints():
    for pad in fp.Pads():
        if pad.GetNetname() == 'XI':
            p = MM(pad.GetPosition())
            print(f'  {fp.GetReference()}.{pad.GetNumber()} ({p[0]:.3f},{p[1]:.3f}) size={MM(pad.GetSize())[0]:.2f}x{MM(pad.GetSize())[1]:.2f}')

print('== foreign B items in box x[72,80] y[7,21] ==')
for t in board.GetTracks():
    if t.GetNetname() == 'XI':
        continue
    if isinstance(t, pcbnew.PCB_VIA):
        p = MM(t.GetPosition())
        if 72 < p[0] < 80 and 7 < p[1] < 21:
            print(f'  VIA {t.GetNetname()} ({p[0]:.3f},{p[1]:.3f}) d={MM(t.GetWidth()):.2f}')
    elif t.GetLayer() == pcbnew.B_Cu:
        s, e = MM(t.GetStart()), MM(t.GetEnd())
        if (72 < s[0] < 80 and 7 < s[1] < 21) or (72 < e[0] < 80 and 7 < e[1] < 21):
            print(f'  B {t.GetNetname()} ({s[0]:.3f},{s[1]:.3f})->({e[0]:.3f},{e[1]:.3f}) w={MM(t.GetWidth()):.2f}')
for fp in board.GetFootprints():
    for pad in fp.Pads():
        if pad.GetNetname() == 'XI':
            continue
        ls = pad.GetLayerSet()
        if not ls.Contains(pcbnew.B_Cu):
            continue
        p = MM(pad.GetPosition())
        if 72 < p[0] < 80 and 7 < p[1] < 21:
            print(f'  PAD B {fp.GetReference()}.{pad.GetNumber()} {pad.GetNetname()} ({p[0]:.3f},{p[1]:.3f})')

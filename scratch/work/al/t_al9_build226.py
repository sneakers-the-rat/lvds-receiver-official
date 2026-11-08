"""t_al9: SWCLK connection via DAC_SYNC west-dive re-lay (joint
design, gated in t_al8_gate.py -- ALL GATES PASS, worst +0.014).
DAC: rip F stub/diag/via(90.125,-17.875) + B tail to (89.625,-15.625);
new stub (90.25,-17.55), diag to (89.3,-18.15), west run to dive
(87.3,-18.15), B rejoin seg to the kept joint (89.625,-15.625).
SWCLK: stub (90.75,-17.6), diag to via (90.55,-18.05), B run south
and east to a south approach into J4.4 (92.52,-23.52).
Usage: t_al9_build226.py in out"""
import sys
sys.path.insert(0, 'hw'); sys.path.insert(0, 'scratch/work/ai')
import wx
_app = wx.App(False)
import pcbnew

SRC, OUT = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(SRC)
codes = {}
for t in board.GetTracks():
    codes[t.GetNetname()] = t.GetNetCode()
for fp in board.GetFootprints():
    for p in fp.Pads():
        if p.GetNetname():
            codes[p.GetNetname()] = p.GetNetCode()

RIPSEG = [((90.25, -16.663), (90.25, -17.163)), ((90.25, -17.163), (90.125, -17.875)),
          ((90.125, -17.875), (90.125, -16.125)), ((90.125, -16.125), (89.875, -15.875)),
          ((89.875, -15.875), (89.625, -15.625))]
nrip = 0
for t in list(board.GetTracks()):
    if t.GetNetname() != 'DAC_SYNC':
        continue
    if isinstance(t, pcbnew.PCB_VIA):
        x, y = pcbnew.ToMM(t.GetPosition())
        if abs(x - 90.125) < 0.01 and abs(y + 17.875) < 0.01:
            board.Remove(t); nrip += 1
        continue
    a = (round(pcbnew.ToMM(t.GetStart())[0], 3), round(pcbnew.ToMM(t.GetStart())[1], 3))
    b = (round(pcbnew.ToMM(t.GetEnd())[0], 3), round(pcbnew.ToMM(t.GetEnd())[1], 3))
    if any((a == r[0] and b == r[1]) or (a == r[1] and b == r[0]) for r in RIPSEG):
        board.Remove(t); nrip += 1
print(f'ripped {nrip} (expect 6: 5 segs + 1 via)')
assert nrip == 6

def add_seg(net, a, b, w, layer):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(a[0]), pcbnew.FromMM(a[1])))
    t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(b[0]), pcbnew.FromMM(b[1])))
    t.SetWidth(pcbnew.FromMM(w)); t.SetLayer(layer); t.SetNetCode(codes[net])
    board.Add(t)

def add_via(net, x, y):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
    v.SetWidth(pcbnew.FromMM(0.5)); v.SetDrill(pcbnew.FromMM(0.3))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNetCode(codes[net])
    board.Add(v)

F, IN2, B = pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu
add_seg('DAC_SYNC', (90.25, -16.663), (90.25, -17.55), 0.2, F)
add_seg('DAC_SYNC', (90.25, -17.55), (89.3, -18.15), 0.2, F)
add_seg('DAC_SYNC', (89.3, -18.15), (87.3, -18.15), 0.2, F)
add_via('DAC_SYNC', 87.3, -18.15)
add_seg('DAC_SYNC', (87.3, -18.15), (89.625, -15.625), 0.25, B)
add_seg('SWCLK', (90.75, -16.663), (90.75, -17.6), 0.2, F)
add_seg('SWCLK', (90.75, -17.6), (90.55, -18.05), 0.2, F)
add_via('SWCLK', 90.55, -18.05)
add_seg('SWCLK', (90.55, -18.05), (89.9, -23.0), 0.2, B)
add_seg('SWCLK', (89.9, -23.0), (90.3, -24.55), 0.2, B)
add_seg('SWCLK', (90.3, -24.55), (92.52, -24.55), 0.2, B)
add_seg('SWCLK', (92.52, -24.55), (92.52, -23.52), 0.2, B)
filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
board.Save(OUT)
print('saved', OUT)

"""t_as11: build exp240 from exp239 - add the +3V3D staircase tap (heal_tap3,
gate-clean 0 fails) reconnecting the east bus to via B's column via a B-layer
detour under HV_SHDN's F feed. Adds only, no rips."""
import sys, wx, json
_app = wx.App(False)
import pcbnew

SRC = 'hw/pdlvds_rx.exp239.kicad_pcb'
OUT = 'hw/pdlvds_rx.exp240.kicad_pcb'
LAY = {0: pcbnew.F_Cu, 1: pcbnew.In2_Cu, 2: pcbnew.B_Cu}
MM = pcbnew.FromMM

board = pcbnew.LoadBoard(SRC)
codes = {'+3V3D': board.GetNetcodeFromNetname('+3V3D')}
assert codes['+3V3D'] > 0

plan = json.load(open('scratch/work/ar/heal_tap7.json'))
for e in plan:
    if e[0] == 'via':
        _, net, x, y = e
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
        v.SetWidth(MM(0.5)); v.SetDrill(MM(0.3))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNetCode(codes[net])
        board.Add(v)
    else:
        _, net, li, ax, ay, bx, by, wd = e
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(MM(ax), MM(ay)))
        t.SetEnd(pcbnew.VECTOR2I(MM(bx), MM(by)))
        t.SetWidth(MM(wd)); t.SetLayer(LAY[li]); t.SetNetCode(codes[net])
        board.Add(t)
print(f'added {len(plan)} tap items')
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
board.Save(OUT)
print('saved', OUT)

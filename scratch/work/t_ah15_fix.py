import wx; _a=wx.App(False)
import pcbnew
b = pcbnew.LoadBoard('scratch/work/ah/h8.kicad_pcb')
n=0
for t in list(b.GetTracks()):
    if t.Type()==pcbnew.PCB_VIA_T and t.GetNetname()=='+3V3A':
        p=(round(t.GetPosition().x/1e6,3), round(t.GetPosition().y/1e6,3))
        if p==(68.375,17.5): b.Remove(t); n+=1
assert n==1
b.Save('scratch/work/ah/h9.kicad_pcb')
print('saved h9, removed', n)

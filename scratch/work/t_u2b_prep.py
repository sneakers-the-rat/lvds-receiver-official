import pcbnew
b=pcbnew.LoadBoard('scratch/work/t_u1.kicad_pcb')
MM=pcbnew.ToMM
def segkey(t):
    s,e=t.GetStart(),t.GetEnd()
    return tuple(sorted([(round(MM(s.x),3),round(MM(s.y),3)),
                         (round(MM(e.x),3),round(MM(e.y),3))]))
keep={tuple(sorted(((78.438,12.75),(78.688,12.75))))}
ts=b.Tracks(); ALL=[ts[i] for i in range(ts.size())]
n=0
for t in ALL:
    if t.GetNetname()!='ULPI_D1': continue
    if t.Type()==pcbnew.PCB_VIA_T or segkey(t) not in keep:
        b.Remove(t); n+=1
print('D1 ripped:', n)
b.Save('scratch/work/t_u2b_in.kicad_pcb'); print('saved')

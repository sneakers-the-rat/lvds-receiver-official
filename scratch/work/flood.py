import math, sys
sys.path.insert(0,'hw'); sys.path.insert(0,'scratch/heal8')
import pcbnew, repair, router
from router import netclass
b=pcbnew.LoadBoard('scratch/work/t_n2.kicad_pcb')
net='I2C_SDA'; LI=1; LAYER=pcbnew.In2_Cu
items,_=repair.build_items(b)
width,clr_net=netclass(net); HW=width/2
def cell_clear(x,y):
    for it in items[LI].near(LI,x,y):
        if it[1]==net: continue
        clr=max(clr_net,netclass(it[1])[1])+0.02
        if router.dist_to_item(it,x,y)<HW+clr: return False
    return True
X0,X1,Y0,Y1=64.5,73.5,8,23; C=0.25
NX=int((X1-X0)/C)+1; NY=int((Y1-Y0)/C)+1
start=(69.95,21.9)
si,sj=round((start[0]-X0)/C),round((start[1]-Y0)/C)
seen=set([(si,sj)]); stack=[(si,sj)]
while stack:
    i,j=stack.pop()
    for di in (-1,0,1):
        for dj in (-1,0,1):
            nb=(i+di,j+dj)
            if nb in seen: continue
            if not (0<=nb[0]<NX and 0<=nb[1]<NY): continue
            if cell_clear(X0+nb[0]*C, Y0+nb[1]*C):
                seen.add(nb); stack.append(nb)
print("reachable cells:", len(seen))
for j in range(NY-1,-1,-1):
    row=""
    for i in range(NX):
        x,y=X0+i*C,Y0+j*C
        if (i,j)==(si,sj): row+='S'
        elif (i,j) in seen: row+='.'
        else: row+='#'
    print(f"y={Y0+j*C:5.2f} {row}")
print("x axis: start",X0,"step",C)

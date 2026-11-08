import sys, wx
_app = wx.App(False)
import pcbnew
sys.path.insert(0, 'scratch/work/ai'); sys.path.insert(0, 'hw')
import importlib.util
spec = importlib.util.spec_from_file_location('opt', 'scratch/work/an/t_an1b_hvopt2.py')
# don't exec the whole optimizer; instead replicate its pieces minimally:
from t_ai_lib import load_items, pt_margin, seg_margin, in_box_pool, apply_rip, fmt_it
from router import netclass
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp231.kicad_pcb')
items = load_items(b)
def seg(net, li, a, c, w):
    return (li, ('seg', net, (a[0], a[1], c[0], c[1], w/2), netclass(net)[1]))
def via(net, x, y, d):
    return ('via', net, (x, y, d/2), netclass(net)[1])
RIP_SHDN = [('via','HV_SHDN',30.875,-2.875),('seg','HV_SHDN',30.625,-3.375),
            ('seg','HV_SHDN',30.875,-3.125),('seg','HV_SHDN',30.875,-2.875)]
RIP_NE = [('seg','+5V',30.400,-4.000),('seg','+5V',31.125,-3.875),
          ('seg','+5V',31.375,-3.625),('seg','+5V',31.625,-3.375)]
RIP_SE = [('seg','+5V',31.625,-4.375),('seg','+5V',31.375,-4.750)]
RIP_RUN2 = [('seg','+5V',29.650,-4.000)]
st, n1 = apply_rip(items, RIP_SHDN+RIP_NE+RIP_SE)
st3, n2 = apply_rip(st, RIP_RUN2)
def ne_refan():
    return [seg('+5V',0,(31.150,-4.000),(31.550,-4.350),0.6),
            seg('+5V',0,(31.550,-4.350),(32.000,-3.900),0.6),
            seg('+5V',0,(32.000,-3.900),(31.950,-3.350),0.6),
            seg('+5V',0,(31.950,-3.350),(31.875,-3.125),0.6)]
def se_refan(e1,e2):
    return [seg('+5V',0,(31.150,-4.000),e1,0.6), seg('+5V',0,e1,e2,0.6),
            seg('+5V',0,e2,(31.375,-5.500),0.6)]
def p5v_v3(dx,in2y,rx):
    return [seg('+5V',0,(29.650,-4.000),(dx,in2y),0.2), via('+5V',dx,in2y,0.6),
            seg('+5V',1,(dx,in2y),(rx,in2y),0.6), via('+5V',rx,in2y,0.6),
            seg('+5V',0,(rx,in2y),(31.150,-4.000),0.2),
            seg('+5V',0,(rx,in2y),(31.125,-3.875),0.2)]
vadds = p5v_v3(31.05,-4.30,31.55) + ne_refan() + se_refan((32.10,-4.35),(31.80,-5.05))
it2 = {li: list(st3[li]) for li in range(3)}
for a in vadds:
    if isinstance(a[0], int): it2[a[0]].append(a[1])
    else:
        for li in range(3): it2[li].append(a)
pool = in_box_pool(it2, (29.0,34.6,-6.4,1.5), pad=1.2)
print('--- variant adds exact gates (worst 6):')
ws = []
for a in vadds:
    if isinstance(a[0], int):
        li,o = a
        m,w = seg_margin(li,(o[2][0],o[2][1]),(o[2][2],o[2][3]),o[1],o[2][4],pool[li])
        ws.append((m,f'L{li} {o[1]} seg {o[2]}',w))
    else:
        for li in range(3):
            m,w = pt_margin(li,a[2][0],a[2][1],a[1],a[2][2],pool[li])
            ws.append((m,f'L{li} {a[1]} via',w))
ws.sort(key=lambda t:t[0])
for m,n_,w in ws[:6]: print(f'   {m:+.3f} {n_} vs {fmt_it(w)}')
print('--- SHDN via (31.05,-3.15) d0.5 per layer:')
for li in range(3):
    m,w = pt_margin(li,31.05,-3.15,'HV_SHDN',0.25,pool[li])
    print(f'   L{li}: {m:+.3f} vs {fmt_it(w)}')
m,w = seg_margin(0,(30.375,-3.5),(31.05,-3.15),'HV_SHDN',0.10,pool[0])
print(f'   F web: {m:+.3f} vs {fmt_it(w)}')
print('--- INTVCC dive scan on this pool (0.05 grid, am-style):')
feas=[]
for gx in range(17):
    for gy in range(17):
        x=30.50+gx*0.05; y=-3.20+gy*0.05
        ms=[pt_margin(li,x,y,'HV_INTVCC',0.25,pool[li])[0] for li in range(3)]
        if min(ms)<0: continue
        ma,_=seg_margin(0,(30.375,-3.0),(x,y),'HV_INTVCC',0.10,pool[0])
        if ma<0: continue
        feas.append((min(ms),x,y,ms,ma))
feas.sort(reverse=True)
print(f'   dives: {len(feas)}')
for f in feas[:8]: print(f'   ({f[1]:.2f},{f[2]:.2f}) min {f[0]:+.3f} layers {[round(v,3) for v in f[3]]} acc {f[4]:+.3f}')

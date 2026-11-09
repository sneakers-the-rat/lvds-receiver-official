import sys
sys.path.insert(0, 'scratch/work/ax')
from t_ax0_pre import *  # noqa
b = pcbnew.LoadBoard('hw/pdlvds_rx.exp250.kicad_pcb')
MM = 1000000
def mm(v): return (round(v.x/MM,3), round(v.y/MM,3))
print('--- PHY_1V8 items within 1.5mm of (78.1,17.5) ---')
for t in b.GetTracks():
    p = mm(t.GetPosition()) if isinstance(t, pcbnew.PCB_VIA) else None
    if t.GetNetname() == 'PHY_1V8':
        if isinstance(t, pcbnew.PCB_VIA):
            if abs(p[0]-78.1)<1.5 and abs(p[1]-17.5)<1.5: print(' via', p)
        else:
            s,e = mm(t.GetStart()), mm(t.GetEnd())
            if min(abs(s[0]-78.1),abs(e[0]-78.1))<1.5 and min(abs(s[1]-17.5),abs(e[1]-17.5))<1.5:
                print(' seg L', t.GetLayer(), s, e, 'w', t.GetWidth()/MM)
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetNetname()=='PHY_1V8':
            q = mm(p.GetPosition())
            if abs(q[0]-78.1)<1.5 and abs(q[1]-17.5)<1.5: print(' pad', fp.GetReference(), p.GetNumber(), q)
print('--- U5 ---')
for fp in b.GetFootprints():
    if fp.GetReference()=='U5':
        print('U5 at', mm(fp.GetPosition()), 'value', fp.GetValue())
        xs=[]; ys=[]
        for p in fp.Pads():
            q=mm(p.GetPosition()); xs.append(q[0]); ys.append(q[1])
        print(' pads x', min(xs), max(xs), 'y', min(ys), max(ys), 'count', len(xs))
print('--- C22 ---')
for fp in b.GetFootprints():
    if fp.GetReference()=='C22':
        print('C22 at', mm(fp.GetPosition()), 'fp', fp.GetFPID().GetLibItemName())
        for p in fp.Pads(): print('  pad', p.GetNumber(), p.GetNetname(), mm(p.GetPosition()))
print('--- footprints with pads in box x[76,86] y[13,23] ---')
seen={}
for fp in b.GetFootprints():
    for p in fp.Pads():
        q=mm(p.GetPosition())
        if 76<=q[0]<=86 and 13<=q[1]<=23: seen[fp.GetReference()]=fp.GetValue()
print(seen)
